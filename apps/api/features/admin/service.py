"""Admin dashboard aggregation (operators only)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from apps.api.features.auth.roles import is_admin
from apps.api.features.health.service import check_readiness, readiness_status
from apps.api.features.validation.service import validation_metrics_service
from apps.api.shared.infra.cache import CacheKeys, CacheTTL, cache_service
from apps.api.shared.models import LLMUsage, RecommendationFeedback, RecommendationRun, User
from apps.api.shared.settings import Settings, get_settings
from packages.postrec_core.domain.enums import RunStatus, UserRole


class AdminService:
    def get_overview(self, db: Session) -> dict:
        key = CacheKeys.admin_overview()

        def load() -> dict:
            return self._compute_overview(db)

        return cache_service.get_or_load(key, CacheTTL.ADMIN_OVERVIEW, load)

    def _compute_overview(self, db: Session) -> dict:
        user_stats = db.query(
            func.count(User.id).label("total"),
            func.sum(case((User.is_active.is_(True), 1), else_=0)).label("active"),
            func.sum(case((User.role == UserRole.ADMIN, 1), else_=0)).label("admins"),
        ).one()

        run_stats = db.query(
            func.count(RecommendationRun.id).label("total"),
            func.sum(case((RecommendationRun.status == RunStatus.COMPLETED, 1), else_=0)).label("completed"),
            func.sum(
                case(
                    (
                        RecommendationRun.status.in_((RunStatus.FAILED, RunStatus.FAILED_SCHEMA_VALIDATION)),
                        1,
                    ),
                    else_=0,
                )
            ).label("failed"),
        ).one()

        feedback_total = int(db.query(func.count(RecommendationFeedback.id)).scalar() or 0)
        cost_total = float(db.query(func.coalesce(func.sum(LLMUsage.estimated_cost_usd), 0)).scalar() or 0)

        total_users = int(user_stats.total or 0)
        total_runs = int(run_stats.total or 0)
        completed = int(run_stats.completed or 0)
        failed = int(run_stats.failed or 0)

        checks = check_readiness(db)
        readiness = {"status": readiness_status(checks), "checks": checks}
        settings = get_settings()

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "users": {
                "total": total_users,
                "active": int(user_stats.active or 0),
                "admins": int(user_stats.admins or 0),
                "researchers": max(total_users - int(user_stats.admins or 0), 0),
            },
            "runs": {
                "total": total_runs,
                "completed": completed,
                "failed": failed,
                "completion_rate": completed / total_runs if total_runs else 0.0,
                "failure_rate": failed / total_runs if total_runs else 0.0,
            },
            "feedback_total": feedback_total,
            "llm_cost_usd_total": cost_total,
            "system_status": readiness["status"],
            "health_checks": readiness["checks"],
            "app_env": settings.app_env,
        }

    def get_system_config(self) -> dict:
        settings = get_settings()
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "environment": _public_settings_snapshot(settings),
        }

    def get_model_evaluation(self, db: Session) -> dict:
        rows = (
            db.query(
                LLMUsage.provider,
                LLMUsage.model,
                LLMUsage.operation,
                func.count(LLMUsage.id).label("call_count"),
                func.coalesce(func.sum(LLMUsage.input_tokens), 0).label("input_tokens"),
                func.coalesce(func.sum(LLMUsage.output_tokens), 0).label("output_tokens"),
                func.coalesce(func.sum(LLMUsage.total_tokens), 0).label("total_tokens"),
                func.coalesce(func.sum(LLMUsage.estimated_cost_usd), 0).label("estimated_cost_usd"),
            )
            .group_by(LLMUsage.provider, LLMUsage.model, LLMUsage.operation)
            .order_by(func.sum(LLMUsage.estimated_cost_usd).desc())
            .all()
        )

        by_model: dict[str, dict] = {}
        operations: list[dict] = []

        for row in rows:
            model_key = f"{row.provider}/{row.model}"
            bucket = by_model.setdefault(
                model_key,
                {
                    "provider": row.provider,
                    "model": row.model,
                    "call_count": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "estimated_cost_usd": 0.0,
                },
            )
            call_count = int(row.call_count or 0)
            input_tokens = int(row.input_tokens or 0)
            output_tokens = int(row.output_tokens or 0)
            total_tokens = int(row.total_tokens or 0)
            cost = float(row.estimated_cost_usd or 0)

            bucket["call_count"] += call_count
            bucket["input_tokens"] += input_tokens
            bucket["output_tokens"] += output_tokens
            bucket["total_tokens"] += total_tokens
            bucket["estimated_cost_usd"] += cost

            operations.append(
                {
                    "provider": row.provider,
                    "model": row.model,
                    "operation": row.operation,
                    "call_count": call_count,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "estimated_cost_usd": cost,
                }
            )

        models = sorted(by_model.values(), key=lambda item: item["estimated_cost_usd"], reverse=True)
        aggregate_cost = sum(item["estimated_cost_usd"] for item in models)
        aggregate_tokens = sum(item["total_tokens"] for item in models)

        settings = get_settings()
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "configured_models": {
                "generation": settings.gemini_generation_model,
                "embedding": settings.gemini_embedding_model,
                "embedding_dimensions": settings.gemini_embedding_dimensions,
            },
            "aggregate": {
                "call_count": sum(item["call_count"] for item in models),
                "total_tokens": aggregate_tokens,
                "estimated_cost_usd": aggregate_cost,
            },
            "models": models,
            "operations": operations,
        }

    def list_users(self, db: Session, *, limit: int = 50, offset: int = 0) -> dict:
        query = db.query(User).order_by(User.created_at.desc())
        total = query.count()
        users = query.offset(offset).limit(limit).all()
        return {
            "total": total,
            "items": [_user_item(user) for user in users],
        }

    def update_user_role(
        self,
        db: Session,
        *,
        actor: User,
        user_id: uuid.UUID,
        role: str,
    ) -> dict:
        if role not in (UserRole.RESEARCHER, UserRole.ADMIN):
            raise ValueError("Invalid role")

        target = db.query(User).filter_by(id=user_id).first()
        if not target:
            raise LookupError("User not found")

        if target.id == actor.id and role != UserRole.ADMIN:
            raise PermissionError("Cannot remove your own admin access")

        target.role = role
        db.commit()
        db.refresh(target)
        return _user_item(target)

    def get_evaluation_dashboard(self, db: Session) -> dict:
        return validation_metrics_service.get_dashboard(db)

    def get_research_report(self, db: Session) -> dict:
        return validation_metrics_service.get_research_report(db)


def _user_item(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone_number": user.phone_number,
        "role": user.role,
        "is_active": user.is_active,
        "is_admin": is_admin(user),
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _public_settings_snapshot(settings: Settings) -> dict:
    """Non-secret operational configuration for admin review."""

    return {
        "app_env": settings.app_env,
        "auth_enabled": settings.auth_enabled,
        "gemini_generation_model": settings.gemini_generation_model,
        "gemini_embedding_model": settings.gemini_embedding_model,
        "gemini_embedding_dimensions": settings.gemini_embedding_dimensions,
        "hybrid_retrieval_enabled": settings.hybrid_retrieval_enabled,
        "bm25_sparse_enabled": settings.bm25_sparse_enabled,
        "vector_retrieval_enabled": settings.vector_retrieval_enabled,
        "article_llm_validation_enabled": settings.article_llm_validation_enabled,
        "critic_enabled": settings.critic_enabled,
        "fggv_facet_critic_enabled": settings.fggv_facet_critic_enabled,
        "qualis_enabled": settings.qualis_enabled,
        "ranking_calibration_enabled": settings.ranking_calibration_enabled,
        "experiment_fggv_vs_sota_id": settings.experiment_fggv_vs_sota_id,
        "experiment_treatment_fraction": settings.experiment_treatment_fraction,
        "max_papers_default": settings.max_papers_default,
        "max_recommendations_default": settings.max_recommendations_default,
        "max_cost_per_run_usd": settings.max_cost_per_run_usd,
        "run_timeout_seconds": settings.run_timeout_seconds,
        "retrieval_max_article_age_years": settings.retrieval_max_article_age_years,
        "cache_enabled": settings.cache_enabled,
        "otel_enabled": settings.otel_enabled,
        "whatsapp_notifications_enabled": settings.whatsapp_notifications_enabled,
    }


admin_service = AdminService()
