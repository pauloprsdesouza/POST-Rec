#!/usr/bin/env python3
"""Factorial OpenAlex validation harness with alignment precision metrics."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

from packages.postrec_core.retrieval.context_alignment import compute_context_alignment
from packages.postrec_core.retrieval.openalex_query import (
    OpenAlexFilterConfig,
    build_openalex_work_filters,
    openalex_auth_params,
)

SCENARIOS = [
    {
        "name": "recsys_social_capital",
        "research_area": "Recommender Systems",
        "topics": ["social capital", "social networks", "profile modeling"],
        "query": "social capital Recommender Systems social networks",
        "expected_fields": ("Computer Science",),
    },
    {
        "name": "clinical_psychology",
        "research_area": "Clinical Psychology",
        "topics": ["adolescent depression", "social networks"],
        "query": "adolescent depression social networks",
        "expected_fields": ("Psychology",),
    },
    {
        "name": "clinical_medicine_ml",
        "research_area": "Clinical Medicine",
        "topics": ["diabetes", "machine learning"],
        "query": "diabetes machine learning clinical",
        "expected_fields": ("Medicine", "Health Professions"),
    },
]

TIERS = ("strict", "balanced", "recall")
SEARCH_MODES = (True, False)
SAMPLE_SIZE = 25


def _paper_alignment_metrics(
    works: list[dict[str, Any]],
    *,
    research_area: str,
    topics: list[str],
) -> dict[str, Any]:
    if not works:
        return {
            "sample_size": 0,
            "alignment_pass_rate": 0.0,
            "wrong_field_rate": 0.0,
            "keyword_trap_rate": 0.0,
            "empty_run": True,
        }

    passes = 0
    traps = 0
    for work in works:
        paper = {
            "title": work.get("title"),
            "abstract": work.get("abstract"),
            "openalex_field": (work.get("primary_topic") or {}).get("field", {}).get("display_name"),
            "openalex_subfield": (work.get("primary_topic") or {}).get("subfield", {}).get("display_name"),
            "openalex_primary_topic": (work.get("primary_topic") or {}).get("display_name"),
        }
        alignment = compute_context_alignment(
            paper,
            research_area=research_area,
            topics=topics,
        )
        if alignment.passes:
            passes += 1
        if alignment.keyword_trap:
            traps += 1

    sample_size = len(works)
    return {
        "sample_size": sample_size,
        "alignment_pass_rate": round(passes / sample_size, 4),
        "wrong_field_rate": round((sample_size - passes) / sample_size, 4),
        "keyword_trap_rate": round(traps / sample_size, 4),
        "empty_run": sample_size == 0,
    }


def _reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
    if not inverted_index:
        return None
    positions: list[tuple[int, str]] = []
    for token, indexes in inverted_index.items():
        for index in indexes:
            positions.append((index, token))
    if not positions:
        return None
    positions.sort(key=lambda item: item[0])
    return " ".join(token for _, token in positions)


async def fetch_variant(
    client: httpx.AsyncClient,
    *,
    scenario: dict[str, Any],
    tier: str,
    use_search: bool,
    api_key: str | None,
    article_age_cutoff: int,
) -> dict[str, Any]:
    config = OpenAlexFilterConfig(tier=tier)
    filter_clause = build_openalex_work_filters(
        article_age_cutoff=article_age_cutoff,
        pass_kind="foundation",
        research_area=scenario["research_area"],
        topics=scenario["topics"],
        config=config,
    )
    params: dict[str, Any] = {
        "filter": filter_clause,
        "per_page": SAMPLE_SIZE,
        "select": "id,title,abstract_inverted_index,primary_topic,cited_by_count",
        **openalex_auth_params(api_key=api_key),
    }
    if use_search:
        params["search"] = scenario["query"]

    response = await client.get("https://api.openalex.org/works", params=params, timeout=45.0)
    response.raise_for_status()
    payload = response.json()
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}

    works: list[dict[str, Any]] = []
    for work in payload.get("results") or []:
        if not isinstance(work, dict):
            continue
        abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))
        works.append({**work, "abstract": abstract})

    alignment = _paper_alignment_metrics(
        works,
        research_area=scenario["research_area"],
        topics=scenario["topics"],
    )
    return {
        "tier": tier,
        "use_search": use_search,
        "total_count": meta.get("count"),
        "cost_usd": meta.get("cost_usd"),
        "filter": filter_clause,
        **alignment,
    }


def _rank_variants(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def score(row: dict[str, Any]) -> tuple[float, float, float, float, int]:
        total = row.get("total_count") or 0
        pass_rate = row.get("alignment_pass_rate") or 0.0
        wrong_field = row.get("wrong_field_rate") or 1.0
        trap_rate = row.get("keyword_trap_rate") or 1.0
        empty_penalty = -1_000_000.0 if row.get("empty_run") else 0.0
        return (empty_penalty, pass_rate, -wrong_field, -trap_rate, int(total))

    return sorted(rows, key=score, reverse=True)


def _decision_report(scenario_rows: dict[str, Any]) -> dict[str, Any]:
    variants = scenario_rows.get("variants") or []
    ranked = _rank_variants(variants)
    best = ranked[0] if ranked else {}
    recommendation = "balanced+search"
    if best:
        recommendation = f"{best.get('tier')}+{'search' if best.get('use_search') else 'filter_only'}"
    return {
        "scenario": scenario_rows.get("scenario"),
        "recommended": recommendation,
        "best_variant": best,
        "ranked_top3": ranked[:3],
    }


async def main_async(
    *,
    api_key: str | None,
    article_age_cutoff: int,
) -> dict[str, Any]:
    report: dict[str, Any] = {"scenarios": [], "decisions": []}
    async with httpx.AsyncClient() as client:
        for scenario in SCENARIOS:
            scenario_rows: dict[str, Any] = {"scenario": scenario["name"], "variants": []}
            for tier in TIERS:
                for use_search in SEARCH_MODES:
                    result = await fetch_variant(
                        client,
                        scenario=scenario,
                        tier=tier,
                        use_search=use_search,
                        api_key=api_key,
                        article_age_cutoff=article_age_cutoff,
                    )
                    scenario_rows["variants"].append(result)
            report["scenarios"].append(scenario_rows)
            report["decisions"].append(_decision_report(scenario_rows))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate OpenAlex filter configurations")
    parser.add_argument("--api-key", default=None, help="OpenAlex API key (optional)")
    parser.add_argument("--article-age-cutoff", type=int, default=2020)
    parser.add_argument("--output", type=Path, default=None, help="Write JSON report to path")
    args = parser.parse_args()

    report = asyncio.run(
        main_async(
            api_key=args.api_key,
            article_age_cutoff=args.article_age_cutoff,
        )
    )
    text = json.dumps(report, indent=2)
    print(text)
    if args.output:
        args.output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
