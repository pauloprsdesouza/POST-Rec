#!/usr/bin/env python3
"""Benchmark OpenAlex filter tiers for POST-Rec retrieval scenarios."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

import httpx

from packages.postrec_core.retrieval.context_alignment import compute_context_alignment
from packages.postrec_core.retrieval.openalex_query import (
    OpenAlexFilterConfig,
    build_openalex_work_filters,
)
from scripts.openalex_scenarios import OPENALEX_VALIDATION_SCENARIOS


async def run_variant(
    client: httpx.AsyncClient,
    *,
    query: str,
    research_area: str,
    topics: list[str],
    tier: str,
    use_search: bool,
    api_key: str | None,
) -> dict:
    config = OpenAlexFilterConfig(tier=tier)
    filter_clause = build_openalex_work_filters(
        article_age_cutoff=2020,
        pass_kind="foundation",
        research_area=research_area,
        topics=topics,
        config=config,
    )
    params: dict = {"filter": filter_clause, "per_page": 5, "select": "id,title,primary_topic"}
    if use_search:
        params["search"] = query
    if api_key:
        params["api_key"] = api_key

    response = await client.get("https://api.openalex.org/works", params=params, timeout=30.0)
    response.raise_for_status()
    payload = response.json()
    meta = payload.get("meta") or {}
    samples = []
    alignment_passes = 0
    keyword_traps = 0
    for work in (payload.get("results") or [])[:5]:
        topic = work.get("primary_topic") or {}
        field = (topic.get("field") or {}).get("display_name")
        subfield = (topic.get("subfield") or {}).get("display_name")
        alignment = compute_context_alignment(
            {
                "title": work.get("title"),
                "openalex_field": field,
                "openalex_subfield": subfield,
                "openalex_primary_topic": topic.get("display_name"),
            },
            research_area=research_area,
            topics=topics,
        )
        if alignment.passes:
            alignment_passes += 1
        if alignment.keyword_trap:
            keyword_traps += 1
        samples.append(
            {
                "title": (work.get("title") or "")[:80],
                "field": field,
                "subfield": subfield,
                "alignment_passes": alignment.passes,
                "keyword_trap": alignment.keyword_trap,
            }
        )
    sample_size = len(samples)
    return {
        "tier": tier,
        "use_search": use_search,
        "count": meta.get("count"),
        "cost_usd": meta.get("cost_usd"),
        "filter": filter_clause,
        "alignment_pass_rate": round(alignment_passes / sample_size, 4) if sample_size else 0.0,
        "keyword_trap_rate": round(keyword_traps / sample_size, 4) if sample_size else 0.0,
        "samples": samples,
    }


async def main_async(api_key: str | None) -> list[dict]:
    rows: list[dict] = []
    async with httpx.AsyncClient() as client:
        for scenario in OPENALEX_VALIDATION_SCENARIOS:
            scenario_rows: dict = {"scenario": scenario["name"], "variants": []}
            for tier in ("strict", "balanced", "recall"):
                for use_search in (True, False):
                    result = await run_variant(
                        client,
                        query=scenario["query"],
                        research_area=scenario["research_area"],
                        topics=scenario["topics"],
                        tier=tier,
                        use_search=use_search,
                        api_key=api_key,
                    )
                    scenario_rows["variants"].append(result)
            rows.append(scenario_rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark OpenAlex filter configurations")
    parser.add_argument("--api-key", default=None, help="OpenAlex API key (optional)")
    parser.add_argument("--output", type=Path, default=None, help="Write JSON report to path")
    args = parser.parse_args()

    report = asyncio.run(main_async(args.api_key))
    text = json.dumps(report, indent=2)
    print(text)
    if args.output:
        args.output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
