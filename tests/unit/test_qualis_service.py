"""Tests for Qualis journal classification lookup."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from apps.api.features.qualis.cache import QualisCache, QualisCacheKeys
from apps.api.features.qualis.csv_import import detect_period_from_path, iter_qualis_csv_rows
from apps.api.features.qualis.normalize import normalize_issn, normalize_title
from apps.api.features.qualis.periods import period_rank_from_label
from apps.api.features.qualis.repository import QualisRepository
from apps.api.features.qualis.scoring import (
    best_estrato,
    estrato_score,
    period_rank,
    resolve_qualis_classification,
)
from apps.api.features.qualis.service import QualisService
from apps.api.features.retrieval.relevance import compute_relevance_score

FIXTURE_CSV = Path(__file__).resolve().parents[1] / "fixtures" / "qualis_sample.csv"


class InMemoryQualisRepository(QualisRepository):
    """Test double that loads fixture CSV without Postgres."""

    def __init__(self, csv_path: Path, *, period: str = "2021-2024") -> None:

        super().__init__(session_factory=lambda: None)  # type: ignore[arg-type]

        self._by_issn: dict[str, list[tuple[str, str]]] = {}

        self._by_title: dict[str, list[tuple[str, str]]] = {}

        self._load_csv(csv_path, period=period)

        self._available = True

        self._row_count = sum(len(v) for v in self._by_issn.values()) + sum(len(v) for v in self._by_title.values())

    def _load_csv(self, csv_path: Path, *, period: str) -> None:

        for row in iter_qualis_csv_rows(csv_path, period=period):
            if row.issn:
                self._by_issn.setdefault(row.issn, []).append((row.estrato, row.period))

            self._by_title.setdefault(row.title_normalized, []).append((row.estrato, row.period))

    def is_available(self) -> bool:

        return True

    def row_count(self) -> int:

        return self._row_count

    def lookup_classifications_by_issn(self, issn: str) -> list[tuple[str, str]]:

        return list(self._by_issn.get(issn, []))

    def lookup_classifications_by_title(self, title_normalized: str) -> list[tuple[str, str]]:

        return list(self._by_title.get(title_normalized, []))


class MultiPeriodQualisRepository(QualisRepository):
    """In-memory repo with explicit multi-period classifications."""

    def __init__(self, *, by_issn=None, by_title=None) -> None:

        super().__init__(session_factory=lambda: None)  # type: ignore[arg-type]

        self._by_issn = by_issn or {}

        self._by_title = by_title or {}

        self._available = True

        self._row_count = 1

    def is_available(self) -> bool:

        return True

    def row_count(self) -> int:

        return self._row_count

    def lookup_classifications_by_issn(self, issn: str) -> list[tuple[str, str]]:

        return list(self._by_issn.get(issn, []))

    def lookup_classifications_by_title(self, title_normalized: str) -> list[tuple[str, str]]:

        return list(self._by_title.get(title_normalized, []))


@pytest.fixture
def qualis_repo() -> InMemoryQualisRepository:

    return InMemoryQualisRepository(FIXTURE_CSV)


@pytest.fixture
def qualis_service(qualis_repo: InMemoryQualisRepository) -> QualisService:

    cache = QualisCache()

    cache._enabled = False

    cache._client = None

    service = QualisService(repository=qualis_repo, cache=cache)

    service._ready = True

    return service


def test_normalize_issn_accepts_hyphenated_and_plain():

    assert normalize_issn("0001-4273") == "0001-4273"

    assert normalize_issn("00014273") == "0001-4273"

    assert normalize_issn("0001 4273") == "0001-4273"


def test_normalize_title_strips_punctuation_and_case():

    assert normalize_title("Academy of Management Journal") == "ACADEMY OF MANAGEMENT JOURNAL"

    assert normalize_title("A Economia em Revista") == "A ECONOMIA EM REVISTA"


def test_detect_period_from_filename():

    assert detect_period_from_path("qualis_avaliacoes-2021-2024.csv") == "2021-2024"

    assert detect_period_from_path("qualis_avaliacoes-2017-2020.csv") == "2017-2020"

    assert detect_period_from_path("qualis_avaliacoes.csv") == "2021-2024"


def test_qualis_lookup_by_issn(qualis_service: QualisService):

    estrato, period = qualis_service.lookup(issn="00014273")

    assert estrato == "A1"

    assert period == "2021-2024"

    assert qualis_service.lookup_estrato(issn="1413-6090") == "B3"


def test_qualis_lookup_by_venue_title_fallback(qualis_service: QualisService):

    assert qualis_service.lookup_estrato(venue="Academy of Management Journal") == "A1"

    assert qualis_service.lookup_estrato(venue="A Economia em Revista") == "B3"


def test_qualis_unknown_journal_returns_none(qualis_service: QualisService):

    assert qualis_service.lookup(issn="1111-1111", venue="Nonexistent Journal") == (None, None)


def test_best_estrato_picks_highest():

    assert best_estrato({"B3", "A1", "B1"}) == "A1"


def test_period_rank_orders_by_start_year():
    assert period_rank_from_label("2021-2024") > period_rank_from_label("2017-2020")
    assert period_rank("2021-2024") > period_rank("2017-2020")


def test_resolve_qualis_prefers_recent_period_over_higher_old_estrato():

    classifications = [
        ("B1", "2017-2020"),
        ("A1", "2021-2024"),
    ]

    estrato, period = resolve_qualis_classification(classifications)

    assert estrato == "A1"

    assert period == "2021-2024"


def test_resolve_qualis_uses_old_period_when_only_old_exists():

    classifications = [("B3", "2017-2020")]

    estrato, period = resolve_qualis_classification(classifications)

    assert estrato == "B3"

    assert period == "2017-2020"


def test_resolve_qualis_best_estrato_within_same_period():

    classifications = [
        ("B3", "2021-2024"),
        ("A2", "2021-2024"),
    ]

    estrato, period = resolve_qualis_classification(classifications)

    assert estrato == "A2"

    assert period == "2021-2024"


def test_qualis_period_preference_2021_over_2017():

    repo = MultiPeriodQualisRepository(
        by_issn={
            "0001-4273": [
                ("B1", "2017-2020"),
                ("A1", "2021-2024"),
            ]
        }
    )

    service = QualisService(repository=repo, cache=QualisCache())

    service._ready = True

    service._cache._enabled = False

    estrato, period = service.lookup(issn="0001-4273")

    assert estrato == "A1"

    assert period == "2021-2024"


def test_qualis_fallback_to_2017_when_only_old_period():

    repo = MultiPeriodQualisRepository(by_issn={"1413-6090": [("B3", "2017-2020")]})

    service = QualisService(repository=repo, cache=QualisCache())

    service._ready = True

    service._cache._enabled = False

    estrato, period = service.lookup(issn="1413-6090")

    assert estrato == "B3"

    assert period == "2017-2020"


def test_estrato_score_ordering():

    assert estrato_score("A1") > estrato_score("A2") > estrato_score("B3") > estrato_score("C")


def test_qualis_service_boost_for_paper(monkeypatch: pytest.MonkeyPatch, qualis_service: QualisService):

    class _Settings:
        qualis_enabled = True

        qualis_boost_weight = 0.10

    monkeypatch.setattr("apps.api.features.qualis.service.get_settings", lambda: _Settings())

    boost, estrato, period = qualis_service.boost_for_paper({"issn": "0001-4273", "venue": "Some venue"})

    assert estrato == "A1"

    assert period == "2021-2024"

    assert boost == pytest.approx(0.10)


def test_apply_relevance_boost_includes_period(monkeypatch: pytest.MonkeyPatch, qualis_service: QualisService):

    class _Settings:
        qualis_enabled = True

        qualis_boost_weight = 0.10

    monkeypatch.setattr("apps.api.features.qualis.service.get_settings", lambda: _Settings())

    _, meta = qualis_service.apply_relevance_boost(0.5, {"issn": "0001-4273"})

    assert meta["qualis_estrato"] == "A1"

    assert meta["qualis_period"] == "2021-2024"


def test_compute_relevance_score_applies_qualis_boost(monkeypatch: pytest.MonkeyPatch, qualis_service: QualisService):

    monkeypatch.setattr("apps.api.features.retrieval.relevance.qualis_service", qualis_service)

    class _Settings:
        qualis_enabled = True

        qualis_boost_weight = 0.10

    monkeypatch.setattr("apps.api.features.qualis.service.get_settings", lambda: _Settings())

    paper = {
        "title": "Methods for recommendation systems",
        "abstract": "We discuss various filtering approaches in this domain.",
        "issn": "0001-4273",
        "venue": "Some Other Label",
        "citation_count": 2,
    }

    score_without = compute_relevance_score(
        {**paper, "issn": None},
        topics=["recommender systems"],
        research_area="Machine Learning",
    )

    score_with = compute_relevance_score(
        paper,
        topics=["recommender systems"],
        research_area="Machine Learning",
    )

    assert score_with > score_without

    assert score_with - score_without == pytest.approx(0.10, abs=0.001)


def test_qualis_cache_hit_skips_repository(monkeypatch: pytest.MonkeyPatch, qualis_repo: InMemoryQualisRepository):

    mock_redis = MagicMock()

    mock_redis.get.return_value = '{"estrato": "A1", "period": "2021-2024"}'

    cache = QualisCache()

    cache._enabled = True

    cache._client = mock_redis

    cache._prefix = "postrec:test"

    cache._ttl = 3600

    service = QualisService(repository=qualis_repo, cache=cache)

    service._ready = True

    monkeypatch.setattr(qualis_repo, "lookup_classifications_by_issn", MagicMock(return_value=[("B3", "2017-2020")]))

    estrato, period = service.lookup(issn="0001-4273")

    assert estrato == "A1"

    assert period == "2021-2024"

    qualis_repo.lookup_classifications_by_issn.assert_not_called()


def test_qualis_cache_miss_populates_repository(monkeypatch: pytest.MonkeyPatch, qualis_repo: InMemoryQualisRepository):

    mock_redis = MagicMock()

    mock_redis.get.return_value = None

    cache = QualisCache()

    cache._enabled = True

    cache._client = mock_redis

    cache._prefix = "postrec:test"

    cache._ttl = 3600

    service = QualisService(repository=qualis_repo, cache=cache)

    service._ready = True

    estrato, period = service.lookup(issn="0001-4273")

    assert estrato == "A1"

    assert period == "2021-2024"

    mock_redis.setex.assert_called_once()

    args = mock_redis.setex.call_args[0]

    assert args[0] == f"postrec:test:{QualisCacheKeys.issn('0001-4273')}"

    assert '"estrato": "A1"' in args[2] or '"estrato":"A1"' in args[2].replace(" ", "")

    assert '"period": "2021-2024"' in args[2] or '"period":"2021-2024"' in args[2].replace(" ", "")


def test_csv_rows_include_period():

    rows = list(iter_qualis_csv_rows(FIXTURE_CSV, period="2017-2020"))

    assert rows

    assert all(row.period == "2017-2020" for row in rows)
