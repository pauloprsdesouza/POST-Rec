"""Research-context alignment for retrieved papers (field-agnostic)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from packages.postrec_core.retrieval.text_utils import expand_tokens, overlap_score, phrase_tokens, tokenize

DEFAULT_CONTEXT_PASS_THRESHOLD = 0.40

NEGATED_SCOPE_PATTERN = re.compile(
    r"\b(without|no|not|lack(?:ing)?|absence of|exclude(?:d|s|ing)?|unrelated to)\b"
    r"[^.]{0,48}\b([a-z][a-z0-9\s-]{2,40})\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class FieldProfile:
    field_id: str
    aliases: tuple[str, ...]
    venue_patterns: tuple[re.Pattern[str], ...]
    discourse_patterns: tuple[re.Pattern[str], ...]
    foreign_discourse_patterns: tuple[re.Pattern[str], ...] = ()


def _compile(patterns: tuple[str, ...]) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(pattern, re.IGNORECASE) for pattern in patterns)


FIELD_PROFILES: dict[str, FieldProfile] = {
    "computer_science": FieldProfile(
        field_id="computer_science",
        aliases=(
            "computer science",
            "computing",
            "informatics",
            "software engineering",
            "artificial intelligence",
            "machine learning",
            "deep learning",
            "data mining",
            "information retrieval",
            "recommender systems",
            "recommender system",
            "natural language processing",
            "computer vision",
            "human computer interaction",
            "cybersecurity",
            "distributed systems",
        ),
        venue_patterns=_compile(
            (
                r"\bacm\b",
                r"\bieee\b",
                r"recsys",
                r"sigir",
                r"cikm",
                r"\bkdd\b",
                r"\bwww\b",
                r"neurips",
                r"icml",
                r"iclr",
                r"ijcai",
                r"\baaai\b",
                r"arxiv",
                r"computer",
                r"informatics",
                r"software",
            )
        ),
        discourse_patterns=_compile(
            (
                r"\b(algorithm(?:s)?|benchmark(?:s)?|dataset(?:s)?)\b",
                r"\b(machine learning|deep learning|neural networks?)\b",
                r"\b(recommender systems?|recommendation systems?|collaborative filtering)\b",
                r"\b(information retrieval|learning to rank|ndcg)\b",
                r"\b(graph neural|knowledge graph|embedding(?:s)?)\b",
                r"\b(computational model(?:ing)?|simulation(?:s)?)\b",
            )
        ),
        foreign_discourse_patterns=_compile(
            (
                r"\b(qualitative (?:interview|study)|ethnograph(?:y|ic))\b",
                r"\b(clinical trial|randomized controlled trial|patients?\b)\b",
                r"\b(nursing home|midwifery|crop rotation)\b",
            )
        ),
    ),
    "engineering": FieldProfile(
        field_id="engineering",
        aliases=(
            "engineering",
            "electrical engineering",
            "mechanical engineering",
            "civil engineering",
            "control systems",
            "robotics",
            "signal processing",
        ),
        venue_patterns=_compile((r"\bieee\b", r"asme", r"engineering", r"robotics", r"control")),
        discourse_patterns=_compile(
            (
                r"\b(prototype|sensor(?:s)?|actuator(?:s)?|control system)\b",
                r"\b(finite element|structural analysis|power grid)\b",
            )
        ),
    ),
    "medicine_health": FieldProfile(
        field_id="medicine_health",
        aliases=(
            "medicine",
            "clinical medicine",
            "biomedical",
            "healthcare",
            "public health",
            "epidemiology",
            "nursing",
            "oncology",
            "cardiology",
            "clinical nlp",
        ),
        venue_patterns=_compile(
            (
                r"medicine",
                r"clinical",
                r"lancet",
                r"jama",
                r"bmj",
                r"oncolog",
                r"cardiol",
                r"epidemiol",
                r"public health",
                r"nursing",
                r"pediatr",
                r"geriatr",
            )
        ),
        discourse_patterns=_compile(
            (
                r"\b(clinical trial|randomized controlled|patients?\b|hospital(?:s|ization)?)\b",
                r"\b(diagnos(?:is|tic)|prognos(?:is|tic)|therapy|treatment)\b",
                r"\b(cohort study|case-control|survival analysis)\b",
            )
        ),
    ),
    "psychology": FieldProfile(
        field_id="psychology",
        aliases=(
            "psychology",
            "psychological",
            "psychiatry",
            "mental health",
            "cognitive science",
            "behavioral science",
        ),
        venue_patterns=_compile((r"psycholog", r"psychiatr", r"mental health", r"personality", r"behavior")),
        discourse_patterns=_compile(
            (
                r"\b(psycholog(?:y|ical)|psychiatr(?:y|ic)|mental health)\b",
                r"\b(personality|adolescents?|survey participants|self-report)\b",
                r"\b(cognitive bias|psychometric|depression scale)\b",
            )
        ),
    ),
    "social_science": FieldProfile(
        field_id="social_science",
        aliases=(
            "sociology",
            "social science",
            "anthropology",
            "social work",
            "political science",
            "demography",
        ),
        venue_patterns=_compile((r"sociolog", r"anthropolog", r"social science", r"political science", r"demograph")),
        discourse_patterns=_compile(
            (
                r"\b(sociolog(?:y|ical)|anthropolog(?:y|ical)|social work)\b",
                r"\b(qualitative (?:interview|study)|focus group|ethnograph(?:y|ic))\b",
                r"\b(rural communit(?:y|ies)|agricultur(?:e|al))\b",
            )
        ),
    ),
    "natural_science": FieldProfile(
        field_id="natural_science",
        aliases=("physics", "chemistry", "biology", "ecology", "genomics", "materials science"),
        venue_patterns=_compile((r"physics", r"chemistry", r"biology", r"nature", r"science\b", r"cell\b", r"plos")),
        discourse_patterns=_compile(
            (
                r"\b(spectroscop(?:y|ic)|genome|protein|molecule(?:s)?)\b",
                r"\b(field experiment|laboratory assay|species)\b",
            )
        ),
    ),
    "business_economics": FieldProfile(
        field_id="business_economics",
        aliases=("economics", "finance", "management", "marketing", "business", "accounting"),
        venue_patterns=_compile((r"econom", r"finance", r"management", r"marketing", r"accounting")),
        discourse_patterns=_compile(
            (
                r"\b(regression analysis|panel data|stock market|gdp)\b",
                r"\b(randomized field experiment|consumer behavior)\b",
            )
        ),
    ),
    "education": FieldProfile(
        field_id="education",
        aliases=("education", "pedagogy", "learning sciences", "curriculum"),
        venue_patterns=_compile((r"education", r"pedagog", r"curriculum", r"teaching")),
        discourse_patterns=_compile((r"\b(classroom|students?|curriculum|pedagog(?:y|ical))\b",)),
    ),
}


@dataclass(frozen=True)
class ResearchContext:
    research_area: str
    topics: tuple[str, ...] = ()
    learned_topics: tuple[str, ...] = ()
    avoided_topics: tuple[str, ...] = ()
    area_tokens: frozenset[str] = frozenset()
    topic_tokens: frozenset[str] = frozenset()
    scope_tokens: frozenset[str] = frozenset()
    expected_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContextAlignment:
    score: float
    passes: bool
    expected_fields: tuple[str, ...]
    detected_fields: tuple[str, ...]
    area_overlap: float
    topic_overlap: float
    field_alignment: float
    keyword_trap: bool
    on_context_hits: tuple[str, ...] = ()
    off_context_hits: tuple[str, ...] = ()
    rationale: str = ""

    # Backward-compatible aliases used by retrieval metadata.
    @property
    def expected_field(self) -> str | None:
        return self.expected_fields[0] if self.expected_fields else None

    @property
    def on_domain_hits(self) -> tuple[str, ...]:
        return self.on_context_hits

    @property
    def off_domain_hits(self) -> tuple[str, ...]:
        return self.off_context_hits


def normalize_text(value: str | None) -> str:
    return " ".join((value or "").lower().split())


def build_research_context(
    *,
    research_area: str | None,
    topics: list[str] | None = None,
    learned_topics: list[str] | None = None,
    avoided_topics: list[str] | None = None,
) -> ResearchContext | None:
    area = normalize_text(research_area)
    if not area and not topics:
        return None

    topic_list = tuple(topic.strip() for topic in (topics or []) if topic and topic.strip())
    learned_list = tuple(topic.strip() for topic in (learned_topics or []) if topic and topic.strip())
    avoided_list = tuple(topic.strip() for topic in (avoided_topics or []) if topic and topic.strip())

    area_tokens = frozenset(tokenize(area))
    topic_tokens = frozenset(phrase_tokens([*topic_list, *learned_list]))
    scope_tokens = frozenset(area_tokens | topic_tokens)

    expected = infer_expected_fields(area, topic_list)
    return ResearchContext(
        research_area=area,
        topics=topic_list,
        learned_topics=learned_list,
        avoided_topics=avoided_list,
        area_tokens=area_tokens,
        topic_tokens=topic_tokens,
        scope_tokens=scope_tokens,
        expected_fields=expected,
    )


def infer_expected_fields(research_area: str, topics: tuple[str, ...] = ()) -> tuple[str, ...]:
    corpus = normalize_text(" ".join([research_area, *topics]))
    if not corpus:
        return ()

    scores: dict[str, float] = {}
    for profile in FIELD_PROFILES.values():
        score = 0.0
        for alias in profile.aliases:
            alias_norm = normalize_text(alias)
            if alias_norm == corpus or alias_norm in corpus or corpus in alias_norm:
                score = max(score, 1.0)
            else:
                alias_tokens = tokenize(alias_norm)
                if alias_tokens:
                    score = max(score, overlap_score(tokenize(corpus), alias_tokens))
        if score >= 0.34:
            scores[profile.field_id] = score

    if not scores:
        return ()

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_score = ranked[0][1]
    selected = [field_id for field_id, score in ranked if score >= max(0.34, top_score - 0.20)]
    return tuple(selected)


def _paper_text(paper: dict[str, Any]) -> str:
    parts = [
        paper.get("title"),
        paper.get("abstract"),
        paper.get("venue"),
        paper.get("journal_title"),
    ]
    metadata = paper.get("metadata") if isinstance(paper.get("metadata"), dict) else paper.get("metadata_")
    if isinstance(metadata, dict):
        parts.append(metadata.get("journal_title"))
    return " ".join(str(part) for part in parts if part)


def _paper_venue(paper: dict[str, Any], fallback_text: str) -> str:
    venue = " ".join(
        str(part)
        for part in (
            paper.get("venue"),
            paper.get("journal_title"),
        )
        if part
    )
    return venue or fallback_text


def _match_labels(text: str, patterns: tuple[re.Pattern[str], ...]) -> list[str]:
    hits: list[str] = []
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            hits.append(match.group(0).lower())
    return hits


def score_field_presence(text: str, venue: str, profile: FieldProfile) -> float:
    score = 0.0
    venue_hits = _match_labels(venue, profile.venue_patterns)
    discourse_hits = _match_labels(text, profile.discourse_patterns)
    if venue_hits:
        score += min(0.55, 0.18 + 0.12 * len(venue_hits))
    if discourse_hits:
        score += min(0.45, 0.10 + 0.08 * len(discourse_hits))
    return min(1.0, score)


def detect_paper_fields(paper: dict[str, Any]) -> dict[str, float]:
    text = _paper_text(paper)
    venue = _paper_venue(paper, text)
    scores = {profile.field_id: score_field_presence(text, venue, profile) for profile in FIELD_PROFILES.values()}
    if str(paper.get("source") or "").lower() == "arxiv" and "computer_science" in scores:
        scores["computer_science"] = min(1.0, scores["computer_science"] + 0.12)
    return scores


def _field_alignment(expected_fields: tuple[str, ...], detected_fields: dict[str, float]) -> float:
    if not expected_fields:
        return 0.55
    expected_scores = [detected_fields.get(field_id, 0.0) for field_id in expected_fields]
    if not expected_scores:
        return 0.0
    return max(expected_scores)


def _foreign_field_pressure(
    expected_fields: tuple[str, ...],
    detected_fields: dict[str, float],
    text: str,
    venue: str,
) -> tuple[float, list[str]]:
    if not expected_fields:
        return 0.0, []

    foreign_hits: list[str] = []
    pressure = 0.0
    for field_id, score in detected_fields.items():
        if field_id in expected_fields or score < 0.22:
            continue
        profile = FIELD_PROFILES[field_id]
        venue_hits = _match_labels(venue, profile.venue_patterns)
        discourse_hits = _match_labels(text, profile.discourse_patterns)
        if venue_hits:
            foreign_hits.extend(f"venue:{hit}" for hit in venue_hits)
            pressure += 0.22 + 0.08 * len(venue_hits)
        if discourse_hits:
            foreign_hits.extend(discourse_hits)
            pressure += 0.10 + 0.06 * min(2, len(discourse_hits))
    return min(0.65, pressure), foreign_hits


def _strip_negated_scope_terms(text: str) -> str:
    cleaned = text
    for match in NEGATED_SCOPE_PATTERN.finditer(text):
        cleaned = cleaned.replace(match.group(0), " ")
    return cleaned


def _scope_overlaps(paper: dict[str, Any], context: ResearchContext) -> tuple[float, float, set[str], set[str]]:
    raw_text = _paper_text(paper)
    scope_text = _strip_negated_scope_terms(normalize_text(raw_text))
    title_tokens = expand_tokens(tokenize(paper.get("title")))
    body_tokens = expand_tokens(tokenize(scope_text))
    area_tokens = expand_tokens(set(context.area_tokens))
    topic_tokens = expand_tokens(set(context.topic_tokens))

    area_overlap = overlap_score(body_tokens, area_tokens) if area_tokens else 0.0
    topic_overlap = overlap_score(body_tokens, topic_tokens) if topic_tokens else 0.0
    title_area = overlap_score(title_tokens, area_tokens) if area_tokens else 0.0
    title_topic = overlap_score(title_tokens, topic_tokens) if topic_tokens else 0.0
    area_overlap = max(area_overlap, title_area * 0.95)
    topic_overlap = max(topic_overlap, title_topic * 0.95)

    paper_text = normalize_text(scope_text)
    for field_id in context.expected_fields:
        profile = FIELD_PROFILES.get(field_id)
        if not profile:
            continue
        for alias in profile.aliases:
            alias_norm = normalize_text(alias)
            if alias_norm and alias_norm in paper_text:
                area_overlap = max(area_overlap, 0.72)
                break

    return area_overlap, topic_overlap, title_tokens, body_tokens


def _is_keyword_trap(
    *,
    area_overlap: float,
    topic_overlap: float,
    field_alignment: float,
    foreign_pressure: float,
    expected_fields: tuple[str, ...],
) -> bool:
    if not expected_fields:
        return False
    return topic_overlap >= 0.38 and area_overlap < 0.14 and field_alignment < 0.24 and foreign_pressure >= 0.22


def compute_context_alignment(
    paper: dict[str, Any],
    *,
    research_area: str | None,
    topics: list[str] | None = None,
    learned_topics: list[str] | None = None,
    avoided_topics: list[str] | None = None,
    pass_threshold: float = DEFAULT_CONTEXT_PASS_THRESHOLD,
) -> ContextAlignment:
    context = build_research_context(
        research_area=research_area,
        topics=topics,
        learned_topics=learned_topics,
        avoided_topics=avoided_topics,
    )
    if context is None:
        return ContextAlignment(
            score=1.0,
            passes=True,
            expected_fields=(),
            detected_fields=(),
            area_overlap=0.0,
            topic_overlap=0.0,
            field_alignment=1.0,
            keyword_trap=False,
            rationale="no_research_context",
        )

    text = _paper_text(paper)
    venue = _paper_venue(paper, text)
    area_overlap, topic_overlap, _, body_tokens = _scope_overlaps(paper, context)
    detected = detect_paper_fields(paper)
    detected_ranked = tuple(
        field_id
        for field_id, score in sorted(detected.items(), key=lambda item: item[1], reverse=True)
        if score >= 0.18
    )
    field_alignment = _field_alignment(context.expected_fields, detected)
    foreign_pressure, foreign_hits = _foreign_field_pressure(context.expected_fields, detected, text, venue)

    on_hits: list[str] = []
    if area_overlap >= 0.12:
        on_hits.append("area_overlap")
    if topic_overlap >= 0.18:
        on_hits.append("topic_overlap")
    for field_id in context.expected_fields:
        if detected.get(field_id, 0.0) >= 0.22:
            on_hits.append(f"field:{field_id}")

    avoided_tokens = phrase_tokens(list(context.avoided_topics))
    if avoided_tokens and body_tokens & avoided_tokens:
        distinctive_hits = body_tokens & (avoided_tokens - set(context.topic_tokens))
        if len(distinctive_hits) >= 2 or overlap_score(body_tokens, avoided_tokens) >= 0.45:
            foreign_hits.append("avoided_topic")

    keyword_trap = _is_keyword_trap(
        area_overlap=area_overlap,
        topic_overlap=topic_overlap,
        field_alignment=field_alignment,
        foreign_pressure=foreign_pressure,
        expected_fields=context.expected_fields,
    )

    scope_component = (0.45 * area_overlap) + (0.35 * topic_overlap)
    field_component = 0.35 * field_alignment
    penalty = min(0.55, foreign_pressure)
    if keyword_trap:
        penalty = max(penalty, 0.45)
    if "avoided_topic" in foreign_hits:
        penalty = max(penalty, 0.35)

    score = scope_component + field_component - penalty
    if context.expected_fields and field_alignment >= 0.30 and area_overlap >= 0.10:
        score = max(score, 0.58)
    if context.expected_fields and field_alignment >= 0.45 and topic_overlap >= 0.22:
        score = max(score, 0.62)
    score = max(0.0, min(1.0, score))

    has_scope = area_overlap >= 0.10 or topic_overlap >= 0.20
    has_field_support = (
        not context.expected_fields
        or field_alignment >= 0.20
        or area_overlap >= 0.40
        or (topic_overlap >= 0.40 and field_alignment >= 0.12)
    )
    passes = (
        score >= pass_threshold
        and has_scope
        and has_field_support
        and not keyword_trap
        and foreign_pressure < 0.42
        and "avoided_topic" not in foreign_hits
    )

    rationale = (
        f"area={area_overlap:.2f}, topic={topic_overlap:.2f}, "
        f"field={field_alignment:.2f}, foreign={foreign_pressure:.2f}"
    )
    if keyword_trap:
        rationale += ", keyword_trap"

    return ContextAlignment(
        score=round(score, 4),
        passes=passes,
        expected_fields=context.expected_fields,
        detected_fields=detected_ranked,
        area_overlap=round(area_overlap, 4),
        topic_overlap=round(topic_overlap, 4),
        field_alignment=round(field_alignment, 4),
        keyword_trap=keyword_trap,
        on_context_hits=tuple(on_hits),
        off_context_hits=tuple(foreign_hits),
        rationale=rationale,
    )


def apply_context_alignment_to_score(base_score: float, alignment: ContextAlignment) -> float:
    if alignment.passes:
        if alignment.score >= 0.70:
            return min(1.0, base_score + 0.04)
        return base_score
    if alignment.score <= 0.18:
        return min(base_score, 0.10)
    return base_score * max(0.30, alignment.score)
