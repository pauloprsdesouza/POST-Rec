"""Build OpenAlex /works query filters from research context."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from packages.postrec_core.retrieval.context_alignment import infer_expected_fields
from packages.postrec_core.retrieval.openalex_taxonomy_cache import cached_taxonomy_lookup

TaxonomyCacheLoader = Callable[..., tuple[str, ...]]
_taxonomy_cache_loader: TaxonomyCacheLoader | None = None

OPENALEX_API_BASE = "https://api.openalex.org"
OPENALEX_TOPICS_URL = f"{OPENALEX_API_BASE}/topics"
OPENALEX_FIELDS_URL = f"{OPENALEX_API_BASE}/fields"
OPENALEX_SUBFIELDS_URL = f"{OPENALEX_API_BASE}/subfields"

OPENALEX_WORK_TYPES = "article|review|preprint|book-chapter|proceedings-article"
OPENALEX_TOPIC_ID_PATTERN = re.compile(r"/T(\d+)$")
OPENALEX_WORK_ID_PATTERN = re.compile(r"/(W\d+)$", re.IGNORECASE)

# Static fallbacks when API lookup is unavailable.
OPENALEX_FIELD_IDS: dict[str, tuple[str, ...]] = {
    "computer_science": ("17",),
    "engineering": ("22",),
    "medicine_health": ("27", "29", "36"),
    "psychology": ("32",),
    "social_science": ("33",),
    "natural_science": ("11", "13", "23", "31"),
    "business_economics": ("14", "20"),
    "education": ("12", "33"),
}

OPENALEX_SUBFIELD_IDS: dict[str, tuple[str, ...]] = {
    "computer_science": ("1710", "1702"),
    "engineering": ("2208", "2207"),
    "medicine_health": ("2739", "2713"),
    "psychology": ("3207", "3203"),
    "social_science": ("3312", "3308"),
    "natural_science": ("1105", "1312"),
    "business_economics": ("1408", "2002"),
    "education": ("3304",),
}

OPENALEX_DOMAIN_IDS: dict[str, str] = {
    "computer_science": "3",
    "engineering": "3",
    "natural_science": "1",
    "medicine_health": "4",
    "psychology": "2",
    "social_science": "2",
    "business_economics": "2",
    "education": "2",
}

RESEARCH_AREA_SUBFIELD_HINTS: dict[str, tuple[str, ...]] = {
    "recommender systems": ("1710",),
    "recommender system": ("1710",),
    "information retrieval": ("1710",),
    "machine learning": ("1702",),
    "deep learning": ("1702",),
    "natural language processing": ("1702",),
    "computer vision": ("1707",),
    "clinical psychology": ("3203",),
    "clinical medicine": ("2739",),
}


def set_taxonomy_cache_loader(loader: TaxonomyCacheLoader | None) -> None:
    global _taxonomy_cache_loader
    _taxonomy_cache_loader = loader


def _cached_lookup(
    *,
    namespace: str,
    phrase: str,
    loader: Callable[[], tuple[str, ...]],
    extra: str = "",
    ttl_seconds: int = 86_400,
) -> tuple[str, ...]:
    if _taxonomy_cache_loader is not None:
        return _taxonomy_cache_loader(
            namespace=namespace,
            phrase=phrase,
            loader=loader,
            extra=extra,
        )
    memory_key = f"{namespace}:{phrase}:{extra}"
    return cached_taxonomy_lookup(memory_key, loader, ttl_seconds=ttl_seconds)


@dataclass(frozen=True)
class OpenAlexFilterConfig:
    tier: str = "balanced"
    use_field_filter: bool = True
    use_subfield_filter: bool = True
    use_topic_filter: bool = True
    require_core_source: bool = False
    open_access_only: bool = False
    topic_min_relevance: float = 75.0
    foundation_min_citations: int = 2
    sota_min_citations: int = 0


def extract_openalex_topic_id(topic_url: str | None) -> str | None:
    if not topic_url:
        return None
    match = OPENALEX_TOPIC_ID_PATTERN.search(str(topic_url))
    return f"T{match.group(1)}" if match else None


def extract_openalex_work_id(work_url: str | None) -> str | None:
    if not work_url:
        return None
    value = str(work_url).strip()
    match = OPENALEX_WORK_ID_PATTERN.search(value)
    if match:
        return match.group(1).upper()
    if value.upper().startswith("W") and value[1:].isdigit():
        return value.upper()
    return None


def extract_openalex_numeric_id(entity_url: str | None) -> str | None:
    if not entity_url:
        return None
    match = re.search(r"/(\d+)$", str(entity_url))
    return match.group(1) if match else None


def _openalex_get(path: str, *, params: dict[str, str | int]) -> dict:
    import httpx

    response = httpx.get(
        f"{OPENALEX_API_BASE}{path}",
        params=params,
        timeout=12.0,
        headers={"Accept": "application/json"},
    )
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) else {}


def _lookup_openalex_topic_ids_api(search_phrase: str, min_relevance: float = 75.0) -> tuple[str, ...]:
    cleaned = " ".join(search_phrase.lower().split())
    if len(cleaned) < 3:
        return ()
    try:
        payload = _openalex_get("/topics", params={"search": cleaned, "per_page": 3})
    except Exception:
        return ()

    topic_ids: list[str] = []
    for item in payload.get("results") or []:
        if not isinstance(item, dict):
            continue
        relevance = float(item.get("relevance_score") or 0.0)
        if relevance < min_relevance:
            continue
        topic_id = extract_openalex_topic_id(str(item.get("id") or ""))
        if topic_id:
            topic_ids.append(topic_id)
    return tuple(dict.fromkeys(topic_ids))


def lookup_openalex_topic_ids(search_phrase: str, min_relevance: float = 75.0) -> tuple[str, ...]:
    return _cached_lookup(
        namespace="topics",
        phrase=search_phrase,
        loader=lambda: _lookup_openalex_topic_ids_api(search_phrase, min_relevance),
        extra=str(min_relevance),
    )


def _lookup_openalex_field_ids_api(search_phrase: str) -> tuple[str, ...]:
    cleaned = " ".join(search_phrase.lower().split())
    if len(cleaned) < 3:
        return ()
    try:
        payload = _openalex_get("/fields", params={"search": cleaned, "per_page": 2})
    except Exception:
        return ()

    field_ids: list[str] = []
    for item in payload.get("results") or []:
        if not isinstance(item, dict):
            continue
        field_id = extract_openalex_numeric_id(str(item.get("id") or ""))
        if field_id:
            field_ids.append(field_id)
    return tuple(dict.fromkeys(field_ids))


def lookup_openalex_field_ids_from_api(search_phrase: str) -> tuple[str, ...]:
    return _cached_lookup(
        namespace="fields",
        phrase=search_phrase,
        loader=lambda: _lookup_openalex_field_ids_api(search_phrase),
    )


def _lookup_openalex_subfield_ids_api(search_phrase: str) -> tuple[str, ...]:
    cleaned = " ".join(search_phrase.lower().split())
    if len(cleaned) < 3:
        return ()
    try:
        payload = _openalex_get("/subfields", params={"search": cleaned, "per_page": 3})
    except Exception:
        return ()

    subfield_ids: list[str] = []
    for item in payload.get("results") or []:
        if not isinstance(item, dict):
            continue
        subfield_id = extract_openalex_numeric_id(str(item.get("id") or ""))
        if subfield_id:
            subfield_ids.append(subfield_id)
    return tuple(dict.fromkeys(subfield_ids))


def lookup_openalex_subfield_ids_from_api(search_phrase: str) -> tuple[str, ...]:
    return _cached_lookup(
        namespace="subfields",
        phrase=search_phrase,
        loader=lambda: _lookup_openalex_subfield_ids_api(search_phrase),
    )


def resolve_openalex_field_ids(research_area: str | None, topics: list[str] | None) -> tuple[str, ...]:
    expected = infer_expected_fields(research_area or "", tuple(topics or []))
    field_ids: list[str] = []
    for profile_id in expected:
        field_ids.extend(OPENALEX_FIELD_IDS.get(profile_id, ()))

    if research_area and research_area.strip():
        field_ids.extend(lookup_openalex_field_ids_from_api(research_area.strip()))

    return tuple(dict.fromkeys(field_ids))


def resolve_openalex_subfield_ids(research_area: str | None, topics: list[str] | None) -> tuple[str, ...]:
    subfield_ids: list[str] = []
    normalized_area = " ".join((research_area or "").lower().split())
    if normalized_area in RESEARCH_AREA_SUBFIELD_HINTS:
        subfield_ids.extend(RESEARCH_AREA_SUBFIELD_HINTS[normalized_area])

    expected = infer_expected_fields(research_area or "", tuple(topics or []))
    for profile_id in expected:
        subfield_ids.extend(OPENALEX_SUBFIELD_IDS.get(profile_id, ()))

    if research_area and research_area.strip():
        subfield_ids.extend(lookup_openalex_subfield_ids_from_api(research_area.strip()))

    return tuple(dict.fromkeys(subfield_ids))


def resolve_openalex_domain_ids(research_area: str | None, topics: list[str] | None) -> tuple[str, ...]:
    expected = infer_expected_fields(research_area or "", tuple(topics or []))
    domain_ids: list[str] = []
    for profile_id in expected:
        domain_id = OPENALEX_DOMAIN_IDS.get(profile_id)
        if domain_id:
            domain_ids.append(domain_id)
    return tuple(dict.fromkeys(domain_ids))


def resolve_openalex_topic_ids(
    *,
    research_area: str | None,
    topics: list[str] | None,
    max_topics: int = 2,
    topic_min_relevance: float = 75.0,
) -> tuple[str, ...]:
    phrases: list[str] = []
    if research_area and research_area.strip():
        phrases.append(research_area.strip())
    for topic in topics or []:
        if topic and topic.strip():
            phrases.append(topic.strip())
        if len(phrases) >= max_topics + 1:
            break

    resolved: list[str] = []
    for phrase in phrases[: max_topics + 1]:
        for topic_id in lookup_openalex_topic_ids(phrase, topic_min_relevance):
            resolved.append(topic_id)
        if len(resolved) >= max_topics:
            break
    return tuple(dict.fromkeys(resolved))[:max_topics]


def _tier_flags(config: OpenAlexFilterConfig) -> tuple[bool, bool, bool]:
    if config.tier == "strict":
        return config.use_field_filter, config.use_subfield_filter, config.use_topic_filter
    if config.tier == "recall":
        return config.use_field_filter, False, False
    return config.use_field_filter, config.use_subfield_filter, config.use_topic_filter


def build_openalex_work_filters(
    *,
    article_age_cutoff: int,
    pass_kind: str,
    research_area: str | None = None,
    topics: list[str] | None = None,
    config: OpenAlexFilterConfig | None = None,
    # Backward-compatible kwargs
    use_field_filter: bool | None = None,
    use_topic_filter: bool | None = None,
    require_core_source: bool | None = None,
) -> str:
    cfg = config or OpenAlexFilterConfig()
    if use_field_filter is not None:
        cfg = OpenAlexFilterConfig(
            tier=cfg.tier,
            use_field_filter=use_field_filter,
            use_subfield_filter=cfg.use_subfield_filter,
            use_topic_filter=cfg.use_topic_filter if use_topic_filter is None else use_topic_filter,
            require_core_source=cfg.require_core_source if require_core_source is None else require_core_source,
            topic_min_relevance=cfg.topic_min_relevance,
            foundation_min_citations=cfg.foundation_min_citations,
            sota_min_citations=cfg.sota_min_citations,
        )
    elif use_topic_filter is not None or require_core_source is not None:
        cfg = OpenAlexFilterConfig(
            tier=cfg.tier,
            use_field_filter=cfg.use_field_filter,
            use_subfield_filter=cfg.use_subfield_filter,
            use_topic_filter=cfg.use_topic_filter if use_topic_filter is None else use_topic_filter,
            require_core_source=cfg.require_core_source if require_core_source is None else require_core_source,
            topic_min_relevance=cfg.topic_min_relevance,
            foundation_min_citations=cfg.foundation_min_citations,
            sota_min_citations=cfg.sota_min_citations,
        )

    use_field, use_subfield, use_topic = _tier_flags(cfg)
    parts = [
        "has_abstract:true",
        "is_retracted:false",
        "is_paratext:false",
        f"publication_year:>{article_age_cutoff}",
        f"type:{OPENALEX_WORK_TYPES}",
    ]

    min_citations = cfg.foundation_min_citations if pass_kind == "foundation" else cfg.sota_min_citations
    if min_citations > 0:
        parts.append(f"cited_by_count:>{min_citations}")

    subfield_ids = resolve_openalex_subfield_ids(research_area, topics) if use_subfield else ()
    field_ids = resolve_openalex_field_ids(research_area, topics) if use_field else ()

    if use_subfield and subfield_ids:
        parts.append(f"primary_topic.subfield.id:{'|'.join(subfield_ids)}")
    elif use_field and field_ids:
        parts.append(f"primary_topic.field.id:{'|'.join(field_ids)}")
    elif use_field:
        domain_ids = resolve_openalex_domain_ids(research_area, topics)
        if len(domain_ids) == 1:
            parts.append(f"primary_topic.domain.id:{domain_ids[0]}")

    if use_topic:
        topic_ids = resolve_openalex_topic_ids(
            research_area=research_area,
            topics=topics,
            topic_min_relevance=cfg.topic_min_relevance,
        )
        if topic_ids:
            if cfg.tier == "strict":
                parts.append(f"primary_topic.id:{'|'.join(topic_ids)}")
            else:
                parts.append(f"topics.id:{'|'.join(topic_ids)}")

    if cfg.require_core_source:
        parts.append("primary_location.source.is_core:true")

    if cfg.open_access_only:
        parts.append("open_access.is_oa:true")

    return ",".join(parts)


def build_openalex_expansion_filters(
    *,
    article_age_cutoff: int,
    work_id: str,
    mode: str,
) -> str:
    base = [
        "has_abstract:true",
        "is_retracted:false",
        "is_paratext:false",
        f"publication_year:>{article_age_cutoff}",
        f"type:{OPENALEX_WORK_TYPES}",
    ]
    if mode == "cites":
        base.append(f"cites:{work_id}")
    elif mode == "related_to":
        base.append(f"related_to:{work_id}")
    else:
        raise ValueError(f"Unknown expansion mode: {mode}")
    return ",".join(base)


def openalex_auth_params(*, api_key: str | None) -> dict[str, str]:
    if api_key and api_key.strip():
        return {"api_key": api_key.strip()}
    return {}
