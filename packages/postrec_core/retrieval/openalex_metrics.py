"""OpenAlex retrieval metrics for a single recommendation run."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OpenAlexRunMetrics:
    requests: int = 0
    search_requests: int = 0
    filter_only_requests: int = 0
    fallback_requests: int = 0
    expansion_requests: int = 0
    doi_batch_requests: int = 0
    total_cost_usd: float = 0.0
    total_hits: int = 0
    latencies_ms: list[float] = field(default_factory=list)

    def record_fetch(
        self,
        *,
        result_count: int,
        cost_usd: float | None,
        latency_ms: float,
        use_search: bool,
        kind: str = "search",
    ) -> None:
        self.requests += 1
        if use_search:
            self.search_requests += 1
        else:
            self.filter_only_requests += 1
        if kind == "fallback":
            self.fallback_requests += 1
        elif kind.startswith("expansion"):
            self.expansion_requests += 1
        elif kind == "doi_batch":
            self.doi_batch_requests += 1
        if cost_usd is not None:
            self.total_cost_usd += float(cost_usd)
        self.total_hits += int(result_count)
        self.latencies_ms.append(latency_ms)

    def summary(self) -> dict[str, Any]:
        latency = self.latencies_ms
        return {
            "requests": self.requests,
            "search_requests": self.search_requests,
            "filter_only_requests": self.filter_only_requests,
            "fallback_requests": self.fallback_requests,
            "expansion_requests": self.expansion_requests,
            "doi_batch_requests": self.doi_batch_requests,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_hits": self.total_hits,
            "latency_ms_p50": round(_percentile(latency, 50), 2) if latency else 0.0,
            "latency_ms_p95": round(_percentile(latency, 95), 2) if latency else 0.0,
        }


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int((pct / 100) * len(ordered)))
    return ordered[index]


def summarize_alignment_stats(papers: list[dict[str, Any]]) -> dict[str, Any]:
    if not papers:
        return {
            "input": 0,
            "alignment_passes": 0,
            "alignment_failures": 0,
            "wrong_field_rate": 0.0,
            "keyword_trap_rate": 0.0,
        }
    passes = sum(1 for paper in papers if paper.get("domain_alignment_passes"))
    traps = sum(1 for paper in papers if paper.get("context_keyword_trap"))
    failures = len(papers) - passes
    return {
        "input": len(papers),
        "alignment_passes": passes,
        "alignment_failures": failures,
        "wrong_field_rate": round(failures / len(papers), 4),
        "keyword_trap_rate": round(traps / len(papers), 4),
    }
