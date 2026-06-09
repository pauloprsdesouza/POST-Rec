"""Celery worker tasks for recommendation pipeline."""

import asyncio
import uuid

from sqlalchemy.orm import Session

from apps.api.features.notifications.service import notification_service
from apps.api.features.profile.service import profile_service
from apps.api.features.recommendations.llm import gemini_service
from apps.api.features.recommendations.pipeline import sota_pipeline_service
from apps.api.features.recommendations.ranking import hybrid_ranking_service
from apps.api.features.retrieval.service import retrieval_service
from apps.api.features.runs.events import failure_user_message, retry_user_message
from apps.api.features.runs.service import run_service
from apps.api.features.runs.stream_service import run_stream_service
from apps.api.shared.database import SessionLocal
from apps.api.shared.infra.cache import cache_service
from apps.api.shared.infra.embedding_config import resolve_embedding_model
from apps.api.shared.infra.http_retry import RetryableFetchError
from apps.api.shared.models import DocumentEmbedding, RecommendationRun, SessionExpectation, UserResearchProfile
from apps.api.shared.observability.logging import configure_logging, get_logger
from apps.api.shared.settings import get_settings
from apps.api.workers.celery_app import celery_app
from packages.postrec_core.domain.enums import RunStatus
from packages.postrec_core.domain.expectation_context import merge_expectation_into_constraints
from packages.postrec_core.domain.run_mode import RunMode

configure_logging()
logger = get_logger("postrec-worker")


def _invalidate_run_caches(run: RecommendationRun) -> None:
    cache_service.invalidate_run(str(run.id))
    if run.user_id:
        cache_service.invalidate_user_runs(str(run.user_id))


def _resolve_run_context(
    db: Session,
    run: RecommendationRun,
    topics: list[str],
    constraints: dict,
) -> tuple[list[str], dict, SessionExpectation | None, str | None, list[str] | None, list[str] | None, int]:
    expectation = None
    if run.expectation_id:
        expectation = db.query(SessionExpectation).filter_by(id=run.expectation_id).first()

    if expectation and expectation.seed_topics and not topics:
        topics = list(expectation.seed_topics)

    constraints = merge_expectation_into_constraints(expectation, constraints)

    research_area = expectation.research_area if expectation else None
    learned_topics: list[str] | None = None
    avoided_topics: list[str] | None = None
    expanded_topics = topics
    max_article_age_years = get_settings().retrieval_max_article_age_years
    if constraints.get("max_article_age_years") is not None:
        max_article_age_years = int(constraints["max_article_age_years"])

    if run.user_id:
        profile = db.query(UserResearchProfile).filter_by(user_id=run.user_id).first()
        if profile:
            research_area = research_area or profile.research_area
            learned_topics = list(profile.learned_topics or [])
            avoided_topics = list(profile.avoided_topics or [])
            expanded_topics = profile_service.expanded_seed_topics(profile, topics)
            if constraints.get("max_article_age_years") is None:
                defaults = profile.recommendation_defaults or {}
                if defaults.get("max_article_age_years") is not None:
                    max_article_age_years = int(defaults["max_article_age_years"])

    return (
        expanded_topics,
        constraints,
        expectation,
        research_area,
        learned_topics,
        avoided_topics,
        max_article_age_years,
    )


def _persist_embeddings(
    db: Session,
    papers: list,
    embeddings: list[list[float]],
    embedding_model: str,
) -> dict[str, list[float]]:
    paper_ids = [paper.id for paper in papers]
    existing_rows = (
        db.query(DocumentEmbedding).filter(DocumentEmbedding.document_id.in_(paper_ids)).all() if paper_ids else []
    )
    existing_keys = {(row.document_id, row.content_hash or "") for row in existing_rows}

    for paper, embedding in zip(papers, embeddings, strict=False):
        content_hash = paper.content_hash or ""
        if not content_hash or (paper.id, content_hash) in existing_keys:
            continue
        db.add(
            DocumentEmbedding(
                document_id=paper.id,
                embedding=embedding,
                embedding_model=embedding_model,
                content_hash=content_hash,
            )
        )
        existing_keys.add((paper.id, content_hash))

    db.commit()
    return {str(paper.id): emb for paper, emb in zip(papers, embeddings, strict=False)}


@celery_app.task(name="apps.api.workers.tasks.process_recommendation_run", bind=True, max_retries=3)
def process_recommendation_run(self, run_id: str) -> dict:
    db = SessionLocal()
    try:
        run = db.query(RecommendationRun).filter_by(id=uuid.UUID(run_id)).first()
        if not run:
            raise ValueError(f"Run {run_id} not found")

        if run.status == RunStatus.CANCELLED:
            return {"status": "cancelled"}

        if run.status == RunStatus.COMPLETED:
            return {"status": "completed"}

        if run.status in (RunStatus.FAILED, RunStatus.FAILED_SCHEMA_VALIDATION):
            run.error_message = None
            run.finished_at = None
            run.status = run.current_step or RunStatus.SEARCHING_PAPERS
            db.commit()
            _invalidate_run_caches(run)

        run_input = run.input or {}
        topics = run_input.get("topics", [])
        constraints = run_input.get("constraints") or {}
        (
            expanded_topics,
            constraints,
            expectation,
            research_area,
            learned_topics,
            avoided_topics,
            max_article_age_years,
        ) = _resolve_run_context(db, run, topics, constraints)

        run_service.update_status(db, run, RunStatus.SEARCHING_PAPERS, 15, "Searching papers")

        papers = asyncio.run(
            retrieval_service.retrieve_papers(
                db,
                expanded_topics,
                run.max_papers,
                research_area=research_area,
                learned_topics=learned_topics,
                avoided_topics=avoided_topics,
                max_article_age_years=max_article_age_years,
            )
        )
        run_service._add_event(
            db,
            run,
            "papers_retrieved",
            f"Retrieved {len(papers)} source documents",
            payload={
                "document_ids": [str(p.id) for p in papers],
                "count": len(papers),
                "sources": list({p.source for p in papers}),
            },
        )
        db.commit()
        _invalidate_run_caches(run)
        run_stream_service.publish(db, run)

        run_service.update_status(db, run, RunStatus.GENERATING_EMBEDDINGS, 45, "Embedding papers")
        texts = [f"{p.title}. {p.abstract or ''}" for p in papers]
        embeddings = gemini_service.generate_embeddings(db, run_id, texts)
        embedding_model = resolve_embedding_model(get_settings().gemini_embedding_model)
        embedding_by_paper_id = _persist_embeddings(db, papers, embeddings, embedding_model)

        run_service.update_status(db, run, RunStatus.RANKING_CANDIDATES, 60, "Ranking")

        run_mode = RunMode.parse(run.mode)
        papers, ranking_payload = hybrid_ranking_service.rerank_papers(
            db,
            run_id,
            papers,
            embeddings,
            topics=expanded_topics,
            research_area=research_area,
            expected_output=expectation.expected_output if expectation else None,
            max_papers=run.max_papers,
        )
        run_service._add_event(
            db,
            run,
            "papers_ranked",
            f"Ranked {len(papers)} papers with hybrid retrieval",
            payload=ranking_payload,
        )
        db.commit()

        ranked_embeddings = [
            embedding_by_paper_id[str(paper.id)] for paper in papers if str(paper.id) in embedding_by_paper_id
        ]

        run_service.update_status(
            db,
            run,
            RunStatus.GENERATING_RECOMMENDATIONS,
            80,
            "Generating recommendations",
        )

        paper_dicts = [
            {
                "paper_id": f"P{index + 1}",
                "source_document_id": str(p.id),
                "title": p.title,
                "year": p.year,
                "doi": p.doi,
                "url": p.url,
                "abstract": p.abstract,
                "citation_count": p.citation_count or 0,
                "relevance_score": (p.metadata_ or {}).get("relevance_score"),
                "tier": (p.metadata_ or {}).get("tier"),
                "retrieval_pass": (p.metadata_ or {}).get("retrieval_pass"),
                "methods": (p.metadata_ or {}).get("methods"),
                "limitations": (p.metadata_ or {}).get("limitations"),
            }
            for index, p in enumerate(papers)
        ]

        recommendations = sota_pipeline_service.generate(
            db=db,
            run_id=run_id,
            mode=run_mode,
            research_area=expectation.research_area if expectation else "",
            seed_topics=topics,
            expected_output=expectation.expected_output if expectation else "",
            desired_depth=expectation.desired_depth if expectation else "medium",
            constraints=constraints,
            papers=paper_dicts,
            paper_embeddings=ranked_embeddings,
            max_recommendations=run.max_recommendations,
            avoided_topics=avoided_topics,
        )

        run_service.update_status(db, run, RunStatus.VALIDATING_OUTPUT, 90, "Validating output")
        published = [rec for rec in recommendations if rec.get("_publication_status", "published") == "published"]
        if not recommendations:
            run.error_message = "No valid recommendations generated"
            run_service.update_status(db, run, RunStatus.FAILED, 100, "No recommendations were generated")
            notification_service.notify_run_failed(
                db,
                run,
                error_message="No valid recommendations generated",
            )
            return {"status": "failed", "error": "No recommendations"}

        run.error_message = None
        run_service.save_recommendations(db, run, recommendations)
        run_service._add_event(
            db,
            run,
            "recommendations_validated",
            f"Saved {len(published)} published, {len(recommendations) - len(published)} need refinement",
            payload={
                "published": len(published),
                "needs_refinement": len(recommendations) - len(published),
                "total": len(recommendations),
            },
        )
        db.commit()
        completion_message = "Run completed"
        if not published:
            completion_message = "Run completed — ideas saved for refinement"
        run_service.update_status(db, run, RunStatus.COMPLETED, 100, completion_message)

        notification_service.notify_run_completed(
            db,
            run,
            recommendation_count=len(published) or len(recommendations),
        )

        logger.info(
            "run_completed",
            run_id=run_id,
            recommendation_count=len(recommendations),
            published_count=len(published),
            paper_count=len(papers),
        )
        return {
            "status": "completed",
            "recommendations": len(recommendations),
            "published": len(published),
        }

    except Exception as exc:
        logger.exception("run_failed", run_id=run_id, error=str(exc))
        run = db.query(RecommendationRun).filter_by(id=uuid.UUID(run_id)).first()
        if not run:
            raise

        attempt = self.request.retries + 1
        max_attempts = self.max_retries + 1

        if attempt < max_attempts:
            run.error_message = None
            run.finished_at = None
            if run.status in (RunStatus.FAILED, RunStatus.FAILED_SCHEMA_VALIDATION):
                run.status = run.current_step or RunStatus.SEARCHING_PAPERS
            run_service._add_event(
                db,
                run,
                "retry_scheduled",
                retry_user_message(exc),
                payload={"attempt": attempt, "max_attempts": max_attempts},
            )
            db.commit()
            _invalidate_run_caches(run)
            run_stream_service.publish(db, run)
            raise self.retry(exc=exc, countdown=30) from exc

        run.error_message = failure_user_message(exc)[:500]
        run_service.update_status(
            db,
            run,
            RunStatus.FAILED,
            run.progress,
            failure_user_message(exc),
        )
        notification_service.notify_run_failed(db, run, error_message=run.error_message)
        raise
    finally:
        db.close()


@celery_app.task(
    name="apps.api.workers.tasks.deferred_source_fetch",
    bind=True,
    max_retries=4,
)
def deferred_source_fetch(self, source: str, query: str, limit: int, pass_kind: str = "foundation") -> list[dict]:
    """Retry a single source fetch on the retrieval queue after rate-limit failures."""
    from apps.api.shared.infra.source_rate_limiter import source_rate_limiter

    source_rate_limiter.wait(source)
    try:
        papers = asyncio.run(retrieval_service.fetch_source(source, query, limit, pass_kind))
        logger.info(
            "deferred_source_fetch_ok",
            source=source,
            query=query,
            count=len(papers),
            attempt=self.request.retries + 1,
        )
        return papers
    except RetryableFetchError as exc:
        logger.warning(
            "deferred_source_fetch_retry",
            source=source,
            query=query,
            attempt=self.request.retries + 1,
            error=str(exc),
            status_code=exc.status_code,
        )
        countdown = int(exc.retry_after_seconds or min(30 * (self.request.retries + 1), 120))
        raise self.retry(exc=exc, countdown=countdown) from exc
    except Exception as exc:
        logger.warning(
            "deferred_source_fetch_retry",
            source=source,
            query=query,
            attempt=self.request.retries + 1,
            error=f"{type(exc).__name__}: {exc}",
        )
        raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1)) from exc
