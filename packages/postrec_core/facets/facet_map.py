"""Literature Facet Map (LFM) construction from retrieved papers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from packages.postrec_core.facets.extraction import extract_paper_facets
from packages.postrec_core.facets.taxonomy import FacetType


@dataclass
class LiteratureFacetMap:
    """Corpus-level facet index used for contrastive verification."""

    paper_facets: list[dict[str, str]] = field(default_factory=list)
    facet_corpus: dict[str, list[str]] = field(default_factory=dict)
    facet_corpus_meta: dict[str, list[dict[str, str]]] = field(default_factory=dict)
    saturation: dict[str, float] = field(default_factory=dict)

    def corpus_texts_for(self, facet: FacetType | str) -> list[str]:
        key = facet.value if isinstance(facet, FacetType) else str(facet)
        return list(self.facet_corpus.get(key, []))

    def corpus_meta_for(self, facet: FacetType | str) -> list[dict[str, str]]:
        key = facet.value if isinstance(facet, FacetType) else str(facet)
        return list(self.facet_corpus_meta.get(key, []))


def build_literature_facet_map(papers: list[dict[str, Any]]) -> LiteratureFacetMap:
    """Extract per-paper facets and aggregate corpus statements per facet type."""
    paper_facets: list[dict[str, str]] = []
    facet_corpus: dict[str, list[str]] = {facet.value: [] for facet in FacetType.all_ordered()}
    facet_corpus_meta: dict[str, list[dict[str, str]]] = {facet.value: [] for facet in FacetType.all_ordered()}

    for paper in papers:
        if not isinstance(paper, dict):
            continue
        facets = extract_paper_facets(paper)
        paper_facets.append(facets)
        title = str(paper.get("title") or "Unknown")
        for facet in FacetType.all_ordered():
            text = facets.get(facet.value, "").strip()
            if text:
                facet_corpus[facet.value].append(text)
                facet_corpus_meta[facet.value].append({"paper_title": title, "text": text})

    saturation: dict[str, float] = {}
    total = max(len(paper_facets), 1)
    for facet in FacetType.all_ordered():
        non_empty = sum(1 for pf in paper_facets if pf.get(facet.value, "").strip())
        saturation[facet.value] = round(non_empty / total, 4)

    return LiteratureFacetMap(
        paper_facets=paper_facets,
        facet_corpus=facet_corpus,
        facet_corpus_meta=facet_corpus_meta,
        saturation=saturation,
    )
