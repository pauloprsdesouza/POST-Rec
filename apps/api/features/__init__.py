"""Aggregate feature routers for the API."""

from fastapi import APIRouter

from apps.api.features.admin.router import router as admin_router
from apps.api.features.auth.router import router as auth_router
from apps.api.features.consent.router import router as consent_router
from apps.api.features.experiments.router import router as experiments_router
from apps.api.features.feedback.router import router as feedback_router
from apps.api.features.health.router import router as health_router
from apps.api.features.profile.router import router as profile_router
from apps.api.features.recommendations.router import router as recommendations_router
from apps.api.features.runs.router import router as runs_router
from apps.api.features.sessions.router import router as sessions_router
from apps.api.features.survey.router import router as survey_router
from apps.api.features.users.router import router as users_router

api_router = APIRouter()
for feature_router in (
    auth_router,
    users_router,
    sessions_router,
    consent_router,
    profile_router,
    runs_router,
    recommendations_router,
    feedback_router,
    survey_router,
    experiments_router,
    health_router,
    admin_router,
):
    api_router.include_router(feature_router)

__all__ = ["api_router"]
