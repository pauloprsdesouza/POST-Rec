"""Recommendation read routes."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.shared.database import get_db
from apps.api.shared.dependencies import get_current_user_optional
from apps.api.shared.models import User
from apps.api.shared.schemas.common import RecommendationResponse
from apps.api.shared.infra.cache import CacheKeys, CacheTTL, is_terminal_run
from apps.api.shared.infra.cache_helpers import load_cached_json
from apps.api.features.runs.access import ensure_run_access, get_run_or_404
from apps.api.features.runs.query import run_recommendations_payload

router = APIRouter(prefix="/api/v1")


@router.get("/recommendation-runs/{run_id}/recommendations", response_model=list[RecommendationResponse])
def get_recommendations(
    run_id: uuid.UUID,
    include_refinement: bool = False,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    run = get_run_or_404(db, run_id)
    ensure_run_access(run, current_user)

    run_key = str(run_id)
    cache_suffix = ":all" if include_refinement else ":published"
    if not is_terminal_run(run.status):
        return [
            RecommendationResponse.model_validate(item)
            for item in run_recommendations_payload(db, run_id, include_refinement=include_refinement)
        ]

    data = load_cached_json(
        CacheKeys.run_recommendations(run_key) + cache_suffix,
        CacheTTL.RECOMMENDATIONS,
        lambda: run_recommendations_payload(db, run_id, include_refinement=include_refinement),
        terminal=True,
    )
    return [RecommendationResponse.model_validate(item) for item in data]
