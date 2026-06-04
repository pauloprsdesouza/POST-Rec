"""Multi-stage SOTA-grounded recommendation generation."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from apps.api.observability.logging import get_logger
from apps.api.services.facet_verification_service import facet_verification_service
from apps.api.services.llm_service import gemini_service
from apps.api.services.novelty_verification_service import novelty_verification_service
from packages.postrec_core.domain.run_mode import RunMode
from packages.postrec_core.facets.saturation import underserved_facets
from packages.postrec_core.scoring.facet_diversity import select_facet_diverse

logger = get_logger("postrec-sota-pipeline")


class SotaPipelineService:
    """Orchestrate landscape → gaps → proposals → verification."""

    def generate(
        self,
        db: Session,
        run_id: str,
        *,
        mode: RunMode,
        research_area: str,
        seed_topics: list[str],
        expected_output: str,
        desired_depth: str,
        constraints: dict[str, Any],
        papers: list[dict[str, Any]],
        paper_embeddings: list[list[float]],
        max_recommendations: int,
    ) -> list[dict[str, Any]]:
        if mode.uses_full_sota_pipeline:
            if mode.uses_fggv_verification:
                return self._generate_fggv_pipeline(
                    db,
                    run_id,
                    mode=mode,
                    research_area=research_area,
                    seed_topics=seed_topics,
                    expected_output=expected_output,
                    desired_depth=desired_depth,
                    constraints=constraints,
                    papers=papers,
                    paper_embeddings=paper_embeddings,
                    max_recommendations=max_recommendations,
                )
            return self._generate_full_pipeline(
                db,
                run_id,
                mode=mode,
                research_area=research_area,
                seed_topics=seed_topics,
                expected_output=expected_output,
                desired_depth=desired_depth,
                constraints=constraints,
                papers=papers,
                paper_embeddings=paper_embeddings,
                max_recommendations=max_recommendations,
            )
        return self._generate_quick_enhanced(
            db,
            run_id,
            mode=mode,
            research_area=research_area,
            seed_topics=seed_topics,
            expected_output=expected_output,
            desired_depth=desired_depth,
            constraints=constraints,
            papers=papers,
            paper_embeddings=paper_embeddings,
            max_recommendations=max_recommendations,
        )

    def _generate_quick_enhanced(
        self,
        db: Session,
        run_id: str,
        *,
        mode: RunMode,
        research_area: str,
        seed_topics: list[str],
        expected_output: str,
        desired_depth: str,
        constraints: dict[str, Any],
        papers: list[dict[str, Any]],
        paper_embeddings: list[list[float]],
        max_recommendations: int,
    ) -> list[dict[str, Any]]:
        result = gemini_service.generate_recommendations(
            db=db,
            run_id=run_id,
            research_area=research_area,
            seed_topics=seed_topics,
            expected_output=expected_output,
            desired_depth=desired_depth,
            constraints=constraints,
            papers=papers,
            max_recommendations=max_recommendations,
            enhanced_sota_fields=True,
        )
        return self._verify_all(
            db,
            run_id,
            result.get("recommendations", []),
            papers=papers,
            paper_embeddings=paper_embeddings,
            mode=mode,
            sota_landscape=None,
        )

    def _generate_full_pipeline(
        self,
        db: Session,
        run_id: str,
        *,
        mode: RunMode,
        research_area: str,
        seed_topics: list[str],
        expected_output: str,
        desired_depth: str,
        constraints: dict[str, Any],
        papers: list[dict[str, Any]],
        paper_embeddings: list[list[float]],
        max_recommendations: int,
    ) -> list[dict[str, Any]]:
        landscape = gemini_service.generate_sota_landscape(
            db=db,
            run_id=run_id,
            research_area=research_area,
            seed_topics=seed_topics,
            expected_output=expected_output,
            papers=papers,
        )
        gap_matrix = gemini_service.generate_gap_matrix(
            db=db,
            run_id=run_id,
            research_area=research_area,
            seed_topics=seed_topics,
            papers=papers,
            sota_landscape=landscape,
        )
        result = gemini_service.generate_sota_proposals(
            db=db,
            run_id=run_id,
            research_area=research_area,
            seed_topics=seed_topics,
            expected_output=expected_output,
            desired_depth=desired_depth,
            constraints=constraints,
            papers=papers,
            sota_landscape=landscape,
            gap_matrix=gap_matrix,
            max_recommendations=max_recommendations,
        )
        recommendations = self._verify_all(
            db,
            run_id,
            result.get("recommendations", []),
            papers=papers,
            paper_embeddings=paper_embeddings,
            mode=mode,
            sota_landscape=landscape,
        )
        logger.info(
            "sota_pipeline_complete",
            run_id=run_id,
            mode=mode.value,
            landscape_methods=len(landscape.get("methods") or []),
            gaps=len(gap_matrix.get("gaps") or []),
            published=len(recommendations),
        )
        return recommendations

    def _generate_fggv_pipeline(
        self,
        db: Session,
        run_id: str,
        *,
        mode: RunMode,
        research_area: str,
        seed_topics: list[str],
        expected_output: str,
        desired_depth: str,
        constraints: dict[str, Any],
        papers: list[dict[str, Any]],
        paper_embeddings: list[list[float]],
        max_recommendations: int,
    ) -> list[dict[str, Any]]:
        landscape = gemini_service.generate_sota_landscape(
            db=db,
            run_id=run_id,
            research_area=research_area,
            seed_topics=seed_topics,
            expected_output=expected_output,
            papers=papers,
        )
        gap_matrix = gemini_service.generate_gap_matrix(
            db=db,
            run_id=run_id,
            research_area=research_area,
            seed_topics=seed_topics,
            papers=papers,
            sota_landscape=landscape,
        )
        facet_map = facet_verification_service.build_facet_map(papers)
        result = gemini_service.generate_fggv_proposals(
            db=db,
            run_id=run_id,
            research_area=research_area,
            seed_topics=seed_topics,
            expected_output=expected_output,
            desired_depth=desired_depth,
            constraints=constraints,
            papers=papers,
            sota_landscape=landscape,
            gap_matrix=gap_matrix,
            facet_saturation=facet_map.saturation,
            underserved_facets=underserved_facets(facet_map.saturation),
            max_recommendations=max(max_recommendations * 2, max_recommendations + 2),
        )
        verified = self._verify_all(
            db,
            run_id,
            result.get("recommendations", []),
            papers=papers,
            paper_embeddings=paper_embeddings,
            mode=mode,
            sota_landscape=landscape,
            gap_matrix=gap_matrix,
            facet_map=facet_map,
        )
        published = [
            rec for rec in verified if rec.get("_publication_status", "published") == "published"
        ]
        diverse = select_facet_diverse(
            published or verified,
            max_items=max_recommendations,
        )
        logger.info(
            "fggv_pipeline_complete",
            run_id=run_id,
            mode=mode.value,
            landscape_methods=len(landscape.get("methods") or []),
            gaps=len(gap_matrix.get("gaps") or []),
            verified=len(verified),
            published=len(published),
            selected=len(diverse),
        )
        if len(diverse) < len(verified):
            selected_ids = {id(r) for r in diverse}
            return diverse + [r for r in verified if id(r) not in selected_ids]
        return diverse

    def _verify_all(
        self,
        db: Session,
        run_id: str,
        recommendations: list[dict[str, Any]],
        *,
        papers: list[dict[str, Any]],
        paper_embeddings: list[list[float]],
        mode: RunMode,
        sota_landscape: dict[str, Any] | None,
        gap_matrix: dict[str, Any] | None = None,
        facet_map=None,
    ) -> list[dict[str, Any]]:
        verified = [
            novelty_verification_service.verify_recommendation(
                db,
                run_id,
                rec,
                papers,
                paper_embeddings,
                mode=mode,
                sota_landscape=sota_landscape,
                gap_matrix=gap_matrix,
                facet_map=facet_map,
            )
            for rec in recommendations
            if isinstance(rec, dict)
        ]
        return novelty_verification_service.filter_publishable(verified, mode=mode)


sota_pipeline_service = SotaPipelineService()
