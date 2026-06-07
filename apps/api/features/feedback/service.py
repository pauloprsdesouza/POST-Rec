"""Feedback service."""

import uuid

from sqlalchemy.orm import Session

from apps.api.shared.models import RecommendationCandidate, RecommendationFeedback
from apps.api.shared.infra.cache import cache_service
from apps.api.features.profile.service import profile_service
from apps.api.shared.settings import get_settings
from packages.postrec_core.scoring.expectation_alignment import compute_eas


class FeedbackService:
    def create_feedback(
        self,
        db: Session,
        recommendation_id: uuid.UUID,
        session_id: uuid.UUID,
        run_id: uuid.UUID,
        data: dict,
        *,
        user_id: str | None = None,
    ) -> RecommendationFeedback:
        eas = compute_eas(data)
        feedback = RecommendationFeedback(
            user_id=user_id,
            session_id=session_id,
            run_id=run_id,
            recommendation_id=recommendation_id,
            relevance_score=data["relevance_score"],
            originality_score=data["originality_score"],
            clarity_score=data["clarity_score"],
            feasibility_score=data["feasibility_score"],
            trust_score=data["trust_score"],
            usefulness_score=data["usefulness_score"],
            would_use_in_real_paper=data["would_use_in_real_paper"],
            decision=data["decision"],
            comment=data.get("comment"),
            expectation_alignment_score=eas,
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        if user_id:
            recommendation = db.query(RecommendationCandidate).filter_by(id=recommendation_id).first()
            if recommendation:
                try:
                    profile_service.apply_feedback(
                        db,
                        user_id=uuid.UUID(user_id),
                        feedback=feedback,
                        recommendation=recommendation,
                    )
                    cache_service.invalidate_user_profile(user_id)
                except (ValueError, TypeError):
                    pass

        cache_service.invalidate_validation_dashboard()

        if user_id and get_settings().ranking_calibration_enabled:
            feedback_count = db.query(RecommendationFeedback).count()
            if feedback_count >= 5 and feedback_count % 5 == 0:
                try:
                    from apps.api.features.feedback.calibration import ranking_calibration_service

                    ranking_calibration_service.calibrate(db)
                except Exception:
                    pass

        return feedback


feedback_service = FeedbackService()
