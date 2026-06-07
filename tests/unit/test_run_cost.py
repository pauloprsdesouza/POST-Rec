"""Tests for run cost aggregation."""

from decimal import Decimal
from uuid import uuid4

from apps.api.shared.models import LLMUsage, RecommendationRun
from apps.api.features.runs.cost import add_usage_cost, get_run_estimated_cost, get_run_usage_summary


class _FakeRun:
    id = uuid4()
    estimated_cost_usd = 0.0


def test_add_usage_cost_updates_run_total():
    run = _FakeRun()
    db = _FakeSession(run)
    add_usage_cost(db, run.id, 0.00125)
    assert run.estimated_cost_usd == 0.00125


def test_get_run_estimated_cost_uses_llm_usage_sum():
    run = _FakeRun()
    run.estimated_cost_usd = 0.0
    db = _FakeSession(run, usage_total=Decimal("0.0042"))
    assert get_run_estimated_cost(db, run) == 0.0042


def test_get_run_usage_summary_aggregates_lines():
    run = _FakeRun()
    db = _FakeUsageSession(
        run,
        rows=[
            _UsageRow("embedding", "gemini-embedding", 8000, 0, Decimal("0.0008")),
            _UsageRow("generation", "gemini-2.0-flash", 4500, 1800, Decimal("0.0017")),
        ],
    )
    summary = get_run_usage_summary(db, run, recommendation_count=5)
    assert summary["estimated_cost_usd"] == 0.0025
    assert summary["input_tokens"] == 12500
    assert summary["output_tokens"] == 1800
    assert summary["total_tokens"] == 14300
    assert summary["estimated_cost_per_recommendation_usd"] == 0.0005
    assert len(summary["lines"]) == 2


class _UsageRow:
    def __init__(self, operation, model, input_tokens, output_tokens, cost):
        self.operation = operation
        self.model = model
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = input_tokens + output_tokens
        self.estimated_cost_usd = cost
        self.created_at = None


class _FakeUsageSession:
    def __init__(self, run, rows):
        self._run = run
        self._rows = rows
        self._usage_total = sum(float(row.estimated_cost_usd) for row in rows)

    def query(self, model):
        if model is RecommendationRun:
            return _FakeRunQuery(self._run)
        if model is LLMUsage:
            return _FakeUsageQuery(self._rows, self._usage_total)
        return _FakeQuery(self._usage_total)


class _FakeUsageQuery:
    def __init__(self, rows, total):
        self._rows = rows
        self._total = total

    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def all(self):
        return self._rows

    def scalar(self):
        return self._total


class _FakeQuery:
    def __init__(self, scalar_value):
        self._scalar_value = scalar_value

    def filter(self, *_args, **_kwargs):
        return self

    def scalar(self):
        return self._scalar_value


class _FakeSession:
    def __init__(self, run, usage_total=Decimal("0")):
        self._run = run
        self._usage_total = usage_total

    def query(self, model):
        if model is RecommendationRun:
            return _FakeRunQuery(self._run)
        return _FakeQuery(self._usage_total)


class _FakeRunQuery:
    def __init__(self, run):
        self._run = run

    def filter_by(self, **_kwargs):
        return self

    def first(self):
        return self._run
