"""OpenAlex retrieval and corpus pipeline settings."""

from pydantic_settings import BaseSettings

from apps.api.shared.settings._common import SHARED_SETTINGS_CONFIG


class RetrievalSettings(BaseSettings):
    model_config = SHARED_SETTINGS_CONFIG

    openalex_email: str = ""
    openalex_api_key: str = ""

    retrieval_fetch_max_attempts: int = 5
    retrieval_http_retries: int = 4
    retrieval_use_celery_deferred: bool = True
    retrieval_deferred_timeout_seconds: int = 180
    retrieval_min_relevance_score: float = 0.22
    retrieval_domain_filter_enabled: bool = True
    retrieval_min_domain_alignment: float = 0.40
    article_llm_validation_enabled: bool = True
    article_llm_min_relevance_score: float = 0.42
    article_min_valid_papers: int = 2
    article_grounding_best_effort_enabled: bool = True
    article_sparse_corpus_threshold: int = 12
    retrieval_cache_enabled: bool = True
    retrieval_cache_ttl_seconds: int = 21_600
    retrieval_circuit_failure_threshold: int = 4
    retrieval_circuit_cooldown_seconds: float = 120.0
    retrieval_min_papers_before_skip: int = 12
    retrieval_openalex_min_interval: float = 0.35
    retrieval_openalex_field_filter_enabled: bool = True
    retrieval_openalex_subfield_filter_enabled: bool = True
    retrieval_openalex_topic_filter_enabled: bool = True
    retrieval_openalex_require_core_source: bool = False
    retrieval_openalex_filter_tier: str = "balanced"
    retrieval_openalex_use_search: bool = True
    retrieval_openalex_fallback_recall_enabled: bool = True
    retrieval_openalex_fallback_min_results: int = 8
    retrieval_openalex_topic_min_relevance: float = 75.0
    retrieval_openalex_foundation_min_citations: int = 2
    retrieval_openalex_sota_min_citations: int = 0
    retrieval_openalex_citation_expansion_enabled: bool = True
    retrieval_openalex_citation_expansion_seeds: int = 3
    retrieval_openalex_citation_expansion_limit: int = 25
    retrieval_openalex_log_rate_limit: bool = True
    retrieval_openalex_taxonomy_cache_ttl_seconds: int = 86_400
    retrieval_openalex_open_access_only: bool = False
    retrieval_openalex_doi_enrichment_enabled: bool = True
    retrieval_openalex_doi_batch_size: int = 25
    retrieval_openalex_fwci_boost_enabled: bool = True
    retrieval_corpus_prefetch_enabled: bool = True
    retrieval_corpus_prefetch_min_score: float = 0.28
    retrieval_learned_topic_cap: int = 2
    retrieval_openalex_per_page_max: int = 100
    hybrid_retrieval_enabled: bool = True
    hybrid_sparse_weight: float = 0.4
    retrieval_max_article_age_years: int = 5
    sota_recent_years: int = 3
    sota_seminal_citation_threshold: int = 50
    sota_tier_quota: float = 0.6
    dual_retrieval_enabled: bool = True
    bm25_sparse_enabled: bool = True
    vector_retrieval_enabled: bool = True
    vector_retrieval_top_k: int = 100
