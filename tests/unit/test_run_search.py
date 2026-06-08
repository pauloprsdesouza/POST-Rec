from apps.api.features.runs.search import normalize_search_query


def test_normalize_search_query_splits_words():
    assert normalize_search_query("Graph Neural Networks") == ["graph", "neural", "networks"]


def test_normalize_search_query_ignores_short_tokens():
    assert normalize_search_query("a b x") == []


def test_normalize_search_query_limits_token_count():
    tokens = normalize_search_query("one two three four five six seven eight nine ten")
    assert len(tokens) == 8


def test_normalize_search_query_handles_accents():
    assert "pesquisa" in normalize_search_query("novidade na pesquisa clínica")
