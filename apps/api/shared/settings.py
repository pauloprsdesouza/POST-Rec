"""Application settings."""

from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"

DEFAULT_GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
DEFAULT_GEMINI_EMBEDDING_DIMENSIONS = 768
DEPRECATED_EMBEDDING_MODEL_PREFIX = "text-embedding-"


def normalize_embedding_model(model: str, *, default: str = DEFAULT_GEMINI_EMBEDDING_MODEL) -> str:
    """Normalize GEMINI_EMBEDDING_MODEL values, including legacy names."""
    cleaned = model.strip().removeprefix("models/")
    if not cleaned or cleaned.startswith(DEPRECATED_EMBEDDING_MODEL_PREFIX):
        return default
    return cleaned


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "post-rec"

    database_url: str = "postgresql+psycopg://app:app@192.168.10.13:5432/epilogik"

    rabbitmq_host: str = "192.168.10.13"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "admin"
    rabbitmq_password: str = ""
    celery_broker_url: str = ""
    celery_result_backend: str = ""

    redis_url: str = ""

    cache_enabled: bool = True
    cache_redis_db: int = 2
    cache_key_prefix: str = "postrec:cache:v1"

    minio_endpoint: str = "192.168.10.13:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = ""
    minio_use_ssl: bool = False
    minio_bucket: str = "postrec-artifacts"

    gemini_api_key: str = ""
    gemini_embedding_model: str = DEFAULT_GEMINI_EMBEDDING_MODEL
    gemini_generation_model: str = "gemini-2.5-flash-lite"
    gemini_embedding_dimensions: int = DEFAULT_GEMINI_EMBEDDING_DIMENSIONS

    openalex_email: str = ""
    crossref_email: str = ""
    semantic_scholar_api_key: str = ""
    core_api_key: str = ""
    core_api_base_url: str = "https://api.core.ac.uk/v3"

    retrieval_fetch_max_attempts: int = 5
    retrieval_http_retries: int = 4
    retrieval_use_celery_deferred: bool = True
    retrieval_deferred_timeout_seconds: int = 180
    retrieval_min_relevance_score: float = 0.22
    article_llm_validation_enabled: bool = True
    # LLM semantic rubric threshold (0-1). Distinct from retrieval_min_relevance_score (lexical).
    article_llm_min_relevance_score: float = 0.5
    article_min_valid_papers: int = 3
    retrieval_cache_enabled: bool = True
    retrieval_cache_ttl_seconds: int = 21_600
    retrieval_circuit_failure_threshold: int = 4
    retrieval_circuit_cooldown_seconds: float = 120.0
    retrieval_min_papers_before_skip: int = 12
    retrieval_openalex_min_interval: float = 0.35
    retrieval_crossref_min_interval: float = 0.35
    retrieval_semantic_scholar_min_interval: float = 5.0
    retrieval_arxiv_min_interval: float = 4.0
    retrieval_core_min_interval: float = 10.0
    retrieval_source_priority: str = "openalex,crossref,semantic_scholar,core,arxiv"
    retrieval_corpus_prefetch_enabled: bool = True
    retrieval_s2_recommendations_enabled: bool = True
    retrieval_s2_recommendation_seeds: int = 5
    retrieval_s2_recommendation_limit: int = 50
    retrieval_learned_topic_cap: int = 2
    retrieval_crossref_max_queries: int = 2
    retrieval_core_max_queries: int = 2
    retrieval_openalex_per_page_max: int = 100
    retrieval_crossref_rows_max: int = 80
    retrieval_semantic_scholar_limit_max: int = 100
    retrieval_core_limit_max: int = 100
    retrieval_arxiv_max_results: int = 40
    hybrid_retrieval_enabled: bool = True
    hybrid_sparse_weight: float = 0.4
    retrieval_max_article_age_years: int = 5
    sota_recent_years: int = 3
    sota_seminal_citation_threshold: int = 50
    sota_tier_quota: float = 0.6
    critic_enabled: bool = True
    critic_reject_on_failure: bool = True
    novelty_min_embedding_distance: float = 0.15
    novelty_llm_blend: float = 0.35
    dual_retrieval_enabled: bool = True
    bm25_sparse_enabled: bool = True
    vector_retrieval_enabled: bool = True
    vector_retrieval_top_k: int = 100
    qualis_enabled: bool = True
    qualis_csv_path: str = ""
    qualis_boost_weight: float = 0.10
    qualis_use_redis_cache: bool = True
    qualis_cache_ttl: int = 2_592_000  # 30d reference data; 0 = no expiry

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

    experiment_fggv_vs_sota_enabled: bool = False
    experiment_fggv_vs_sota_id: str = "fggv_vs_sota_v1"
    experiment_treatment_fraction: float = 0.5

    run_stream_enabled: bool = True

    log_level: str = "INFO"
    log_format: str = "json"

    otel_service_name: str = "postrec-api"
    otel_exporter_otlp_endpoint: str = "http://192.168.10.13:12345"
    otel_exporter_otlp_protocol: str = "grpc"
    otel_enabled: bool = False

    auth_enabled: bool = True
    api_internal_key: str = "dev-internal-key"
    jwt_secret: str = "dev-jwt-secret"

    api_base_url: str = "http://localhost:8000"
    frontend_app_url: str = "http://localhost:5173"

    evolution_api_url: str = "http://192.168.10.13:8080"
    evolution_api_key: str = ""
    evolution_instance_name: str = ""

    phone_default_country_code: str = "55"

    otp_length: int = 6
    otp_ttl_minutes: int = 5
    otp_resend_seconds: int = 60
    otp_max_attempts: int = 5
    whatsapp_notifications_enabled: bool = True

    @field_validator("gemini_embedding_model", mode="before")
    @classmethod
    def coerce_embedding_model(cls, value: object) -> str:
        if value is None:
            return DEFAULT_GEMINI_EMBEDDING_MODEL
        return normalize_embedding_model(str(value))

    @model_validator(mode="after")
    def normalize_gemini_models(self) -> "Settings":
        self.gemini_embedding_model = normalize_embedding_model(self.gemini_embedding_model)
        return self

    @model_validator(mode="after")
    def resolve_connection_urls(self) -> "Settings":
        pwd = quote_plus(self.rabbitmq_password)
        user = quote_plus(self.rabbitmq_user)

        if not self.celery_broker_url and self.rabbitmq_password:
            self.celery_broker_url = f"pyamqp://{user}:{pwd}@{self.rabbitmq_host}:{self.rabbitmq_port}//"
        if not self.redis_url and self.rabbitmq_password:
            self.redis_url = f"redis://:{pwd}@{self.rabbitmq_host}:6379/0"
        if not self.celery_result_backend and self.rabbitmq_password:
            self.celery_result_backend = f"redis://:{pwd}@{self.rabbitmq_host}:6379/1"
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
