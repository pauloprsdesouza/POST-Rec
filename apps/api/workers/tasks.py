"""Celery worker tasks for recommendation pipeline."""

import asyncio
import uuid

from apps.api.database import SessionLocal
from apps.api.models import DocumentEmbedding, RecommendationRun, UserExpectation
from apps.api.observability.logging import configure_logging, get_logger
from apps.api.services.cache_service import cache_service
from apps.api.services.embedding_config import resolve_embedding_model
from apps.api.services.http_retry import RetryableFetchError
from apps.api.services.hybrid_ranking_service import hybrid_ranking_service
from apps.api.services.llm_service import gemini_service
from apps.api.services.retrieval_service import retrieval_service
from apps.api.services.run_events import failure_user_message, retry_user_message
from apps.api.services.run_stream_service import run_stream_service
from apps.api.services.run_service import run_service
from apps.api.services.sota_pipeline_service import sota_pipeline_service
from apps.api.settings import get_settings
from apps.api.workers.celery_app import celery_app
from packages.postrec_core.domain.enums import RunStatus
from packages.postrec_core.domain.run_mode import RunMode

configure_logging()
logger = get_logger("postrec-worker")


def _invalidate_run_caches(run: RecommendationRun) -> None:
    cache_service.invalidate_run(str(run.id))
    if run.user_id:
        cache_service.invalidate_user_runs(run.user_id)


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
        constraints = run_input.get("constraints", {})
        expectation = None
        if run.expectation_id:
            expectation = db.query(UserExpectation).filter_by(id=run.expectation_id).first()

        run_service.update_status(db, run, RunStatus.STARTED, 5, "Run started")

        run_service.update_status(db, run, RunStatus.SEARCHING_PAPERS, 15, "Searching papers")

        research_area = expectation.research_area if expectation else None
        learned_topics: list[str] | None = None
        avoided_topics: list[str] | None = None
        expanded_topics = topics

        if run.user_id:
            from apps.api.models import UserResearchProfile
            from apps.api.services.profile_service import profile_service

            try:
                profile = (
                    db.query(UserResearchProfile)
                    .filter_by(user_id=uuid.UUID(run.user_id))
                    .first()
                )
                if profile:
                    research_area = research_area or profile.research_area
                    learned_topics = list(profile.learned_topics or [])
                    avoided_topics = list(profile.avoided_topics or [])
                    expanded_topics = profile_service.expanded_seed_topics(profile, topics)
            except (ValueError, TypeError):
                pass

        papers = asyncio.run(
            retrieval_service.retrieve_papers(
                db,
                expanded_topics,
                run.max_papers,
                research_area=research_area,
                learned_topics=learned_topics,
                avoided_topics=avoided_topics,
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

        run_service.update_status(db, run, RunStatus.NORMALIZING_DOCUMENTS, 25, "Normalizing")
        run_service.update_status(db, run, RunStatus.DEDUPLICATING_DOCUMENTS, 30, "Deduplicating")

        run_service.update_status(db, run, RunStatus.GENERATING_EMBEDDINGS, 45, "Embedding papers")
        texts = [f"{p.title}. {p.abstract or ''}" for p in papers]
        embeddings = gemini_service.generate_embeddings(db, run_id, texts)
        embedding_model = resolve_embedding_model(get_settings().gemini_embedding_model)

        for paper, emb in zip(papers, embeddings, strict=False):
            existing = (
                db.query(DocumentEmbedding)
                .filter_by(document_id=paper.id, content_hash=paper.content_hash or "")
                .first()
            )
            if not existing and paper.content_hash:
                db.add(
                    DocumentEmbedding(
                        document_id=paper.id,
                        embedding=emb,
                        embedding_model=embedding_model,
                        content_hash=paper.content_hash,
                    )
                )
        db.commit()

        embedding_by_paper_id = {
            str(paper.id): emb for paper, emb in zip(papers, embeddings, strict=False)
        }

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
            embedding_by_paper_id[str(paper.id)]
            for paper in papers
            if str(paper.id) in embedding_by_paper_id
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
                "title": p.title,
                "year": p.year,
                "doi": p.doi,
                "url": p.url,
                "abstract": p.abstract,
                "citation_count": p.citation_count or 0,
                "tier": (p.metadata_ or {}).get("tier"),
                "retrieval_pass": (p.metadata_ or {}).get("retrieval_pass"),
                "methods": (p.metadata_ or {}).get("methods"),
                "limitations": (p.metadata_ or {}).get("limitations"),
            }
            for p in papers
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
        )

        run_service.update_status(db, run, RunStatus.VALIDATING_OUTPUT, 90, "Validating output")
        published = [rec for rec in recommendations if rec.get("_publication_status", "published") == "published"]
        if not recommendations:
            run.error_message = "No valid recommendations generated"
            run_service.update_status(db, run, RunStatus.FAILED, 100, "No recommendations were generated")
            from apps.api.services.notification_service import notification_service

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

        from apps.api.services.notification_service import notification_service

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
        from apps.api.services.notification_service import notification_service

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
    from apps.api.services.source_rate_limiter import source_rate_limiter

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
