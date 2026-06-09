"""Tests for OpenAlex query filter construction."""

from packages.postrec_core.retrieval.openalex_query import (
    OpenAlexFilterConfig,
    build_openalex_expansion_filters,
    build_openalex_work_filters,
    extract_openalex_topic_id,
    extract_openalex_work_id,
    openalex_auth_params,
    resolve_openalex_field_ids,
    resolve_openalex_subfield_ids,
)


def test_extract_openalex_topic_id():
    assert extract_openalex_topic_id("https://openalex.org/T10203") == "T10203"


def test_extract_openalex_work_id():
    assert extract_openalex_work_id("https://openalex.org/W2741809807") == "W2741809807"


def test_resolve_openalex_field_ids_for_recsys():
    field_ids = resolve_openalex_field_ids("Recommender Systems", ["social capital"])
    assert "17" in field_ids


def test_resolve_openalex_subfield_ids_for_recsys():
    subfield_ids = resolve_openalex_subfield_ids("Recommender Systems", ["social capital"])
    assert "1710" in subfield_ids


def test_build_openalex_filters_includes_quality_and_scope_clauses():
    filters = build_openalex_work_filters(
        article_age_cutoff=2020,
        pass_kind="foundation",
        research_area="Recommender Systems",
        topics=["social capital", "social networks"],
        config=OpenAlexFilterConfig(use_topic_filter=False),
    )
    assert "has_abstract:true" in filters
    assert "is_retracted:false" in filters
    assert "is_paratext:false" in filters
    assert "publication_year:>2020" in filters
    assert "proceedings-article" in filters
    assert "primary_topic.subfield.id:" in filters or "primary_topic.field.id:17" in filters
    assert "cited_by_count:>2" in filters


def test_build_openalex_filters_for_psychology_sota_has_no_citation_floor():
    filters = build_openalex_work_filters(
        article_age_cutoff=2018,
        pass_kind="sota",
        research_area="Clinical Psychology",
        topics=["depression"],
        config=OpenAlexFilterConfig(use_topic_filter=False, sota_min_citations=0),
    )
    assert "primary_topic.subfield.id:" in filters or "primary_topic.field.id:32" in filters
    assert "cited_by_count:" not in filters


def test_build_openalex_recall_tier_drops_topic_filter():
    filters = build_openalex_work_filters(
        article_age_cutoff=2020,
        pass_kind="foundation",
        research_area="Recommender Systems",
        topics=["social capital"],
        config=OpenAlexFilterConfig(tier="recall"),
    )
    assert "topics.id:" not in filters
    assert "primary_topic.subfield.id:" not in filters
    assert "primary_topic.field.id:17" in filters


def test_build_openalex_expansion_filters_cites():
    filters = build_openalex_expansion_filters(
        article_age_cutoff=2020,
        work_id="W123",
        mode="cites",
    )
    assert "cites:W123" in filters
    assert "has_abstract:true" in filters


def test_openalex_auth_params_api_key_only():
    params = openalex_auth_params(api_key="test-key")
    assert params == {"api_key": "test-key"}


def test_build_openalex_filters_open_access_only():
    filters = build_openalex_work_filters(
        article_age_cutoff=2020,
        pass_kind="foundation",
        research_area="Recommender Systems",
        topics=["social capital"],
        config=OpenAlexFilterConfig(open_access_only=True, use_topic_filter=False),
    )
    assert "open_access.is_oa:true" in filters
