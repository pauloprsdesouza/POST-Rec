"""Ranking, FGGV, Qualis, experiments, and run pipeline settings."""

from pydantic_settings import BaseSettings

from apps.api.shared.settings._common import SHARED_SETTINGS_CONFIG


class PipelineSettings(BaseSettings):
    model_config = SHARED_SETTINGS_CONFIG

    critic_enabled: bool = True
    critic_reject_on_failure: bool = True
    novelty_min_embedding_distance: float = 0.15
    novelty_llm_blend: float = 0.35

    qualis_enabled: bool = True
    qualis_csv_path: str = ""
    qualis_boost_weight: float = 0.10
    qualis_use_redis_cache: bool = True
    qualis_cache_ttl: int = 2_592_000

    ranking_calibration_enabled: bool = True
    require_sota_fields_quick: bool = True
    fggv_facet_critic_enabled: bool = True
    fggv_saturation_aware: bool = True
    fggv_min_facet_novelty_index: float = 0.35
    fggv_min_per_facet_novelty: float = 0.28
    fggv_false_novel_facet_threshold: int = 2
    fggv_llm_facet_blend: float = 0.25
    max_papers_default: int = 50
    max_recommendations_default: int = 5
    run_timeout_seconds: int = 900
    max_cost_per_run_usd: float = 2.00

    experiment_fggv_vs_sota_id: str = "fggv_vs_sota_v1"
    experiment_treatment_fraction: float = 0.5

    run_stream_enabled: bool = True
