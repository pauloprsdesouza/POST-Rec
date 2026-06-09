"""Persistent user research profile management."""

import uuid

from sqlalchemy.orm import Session

from apps.api.shared.models import RecommendationCandidate, RecommendationFeedback, SessionProfile, UserResearchProfile


class ProfileService:
    def get_or_create(self, db: Session, user_id: uuid.UUID) -> UserResearchProfile:
        profile = db.query(UserResearchProfile).filter_by(user_id=user_id).first()
        if profile:
            return profile
        profile = UserResearchProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    def upsert_from_session_profile(
        self, db: Session, user_id: uuid.UUID, session_profile: SessionProfile
    ) -> UserResearchProfile:
        profile = self.get_or_create(db, user_id)
        profile.research_area = session_profile.research_area or profile.research_area
        profile.academic_level = session_profile.academic_level or profile.academic_level
        profile.professional_role = session_profile.professional_role or profile.professional_role
        profile.experience_with_ai = session_profile.experience_with_ai or profile.experience_with_ai
        profile.experience_with_recommender_systems = (
            session_profile.experience_with_recommender_systems or profile.experience_with_recommender_systems
        )
        profile.experience_with_scientific_writing = (
            session_profile.experience_with_scientific_writing or profile.experience_with_scientific_writing
        )
        profile.goal_with_postrec = session_profile.goal_with_postrec or profile.goal_with_postrec
        db.commit()
        db.refresh(profile)
        return profile

    def update_profile(self, db: Session, user_id: uuid.UUID, data: dict) -> UserResearchProfile:
        profile = self.get_or_create(db, user_id)
        for field in (
            "research_area",
            "academic_level",
            "professional_role",
            "experience_with_ai",
            "experience_with_recommender_systems",
            "experience_with_scientific_writing",
            "goal_with_postrec",
        ):
            if field in data and data[field] is not None:
                setattr(profile, field, data[field])
        if "recommendation_defaults" in data and data["recommendation_defaults"] is not None:
            profile.recommendation_defaults = data["recommendation_defaults"]
        db.commit()
        db.refresh(profile)
        return profile

    def apply_feedback(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        feedback: RecommendationFeedback,
        recommendation: RecommendationCandidate,
    ) -> UserResearchProfile:
        profile = self.get_or_create(db, user_id)
        learned = list(profile.learned_topics or [])
        avoided = list(profile.avoided_topics or [])
        techniques = list(profile.preferred_techniques or [])

        positive = feedback.decision in {"approved", "save"} or (feedback.relevance_score or 0) >= 4
        negative = feedback.decision in {"rejected", "needs_revision"} and (feedback.relevance_score or 5) <= 2

        if recommendation.technique_name and positive:
            if recommendation.technique_name not in techniques:
                techniques.append(recommendation.technique_name)
            if recommendation.technique_name not in learned:
                learned.append(recommendation.technique_name)

        if recommendation.title and positive:
            snippet = recommendation.title[:120]
            if snippet not in learned:
                learned.append(snippet)

        if recommendation.technique_name and negative:
            if recommendation.technique_name not in avoided:
                avoided.append(recommendation.technique_name)

        if feedback.comment and len(feedback.comment.strip()) > 10:
            notes = list(profile.feedback_notes or [])
            notes.append(
                {
                    "decision": feedback.decision,
                    "relevance": feedback.relevance_score,
                    "comment": feedback.comment.strip()[:500],
                }
            )
            profile.feedback_notes = notes[-20:]

        defaults = dict(profile.recommendation_defaults or {})
        originality = feedback.originality_score or 3
        if positive and originality >= 4:
            defaults["preferred_run_mode"] = "exploratory"
        elif positive and originality <= 2:
            defaults["preferred_run_mode"] = "sota"
        elif negative:
            defaults["preferred_run_mode"] = "sota"
        profile.recommendation_defaults = defaults

        profile.learned_topics = learned[-30:]
        profile.avoided_topics = avoided[-30:]
        profile.preferred_techniques = techniques[-20:]
        db.commit()
        db.refresh(profile)
        return profile

    def expanded_seed_topics(self, profile: UserResearchProfile, base_topics: list[str]) -> list[str]:
        merged: list[str] = []
        seen: set[str] = set()
        for topic in base_topics + list(profile.learned_topics or []) + list(profile.preferred_techniques or []):
            key = topic.strip().lower()
            if key and key not in seen:
                seen.add(key)
                merged.append(topic.strip())
        return merged

    def remove_learned_topics(self, db: Session, user_id: uuid.UUID, topics: list[str]) -> UserResearchProfile:
        profile = self.get_or_create(db, user_id)
        if not topics:
            return profile

        remove_keys = {topic.strip().lower() for topic in topics if topic and topic.strip()}
        if not remove_keys:
            return profile

        learned = [topic for topic in (profile.learned_topics or []) if topic.strip().lower() not in remove_keys]
        techniques = [
            topic for topic in (profile.preferred_techniques or []) if topic.strip().lower() not in remove_keys
        ]
        profile.learned_topics = learned
        profile.preferred_techniques = techniques
        db.commit()
        db.refresh(profile)
        return profile


profile_service = ProfileService()
