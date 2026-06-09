"""Merge session expectation fields into run constraints and prompt text."""

from __future__ import annotations

from typing import Any


def merge_expectation_into_constraints(
    expectation: Any | None,
    constraints: dict[str, Any],
) -> dict[str, Any]:
    """Enrich run constraints with session expectation fields when present."""
    if expectation is None:
        return constraints

    merged = dict(constraints)

    if expectation.preferred_validation:
        merged["preferred_validation"] = list(expectation.preferred_validation)

    if expectation.publication_goal:
        merged["publication_goal"] = expectation.publication_goal

    for field in (
        "expects_original_ideas",
        "expects_datasets",
        "expects_experimental_plan",
        "expects_references",
    ):
        value = getattr(expectation, field, None)
        if value is not None:
            merged[field] = value

    if expectation.avoid_real_user_experiments:
        merged.setdefault("avoid_real_user_experiments", True)

    return merged


def format_user_expectations(constraints: dict[str, Any]) -> str:
    """Human-readable summary for LLM prompts."""
    lines: list[str] = []

    if constraints.get("publication_goal"):
        lines.append(f"- Publication goal: {constraints['publication_goal']}")

    preferred_validation = constraints.get("preferred_validation")
    if preferred_validation:
        lines.append(f"- Preferred validation: {', '.join(str(v) for v in preferred_validation)}")

    expectation_flags = {
        "expects_original_ideas": "Include original, non-derivative research ideas",
        "expects_datasets": "Include concrete dataset suggestions",
        "expects_experimental_plan": "Include a detailed experimental plan",
        "expects_references": "Include supporting references from retrieved papers",
    }
    for key, label in expectation_flags.items():
        if constraints.get(key) is True:
            lines.append(f"- {label}")

    if constraints.get("avoid_real_user_experiments"):
        lines.append("- Avoid proposals requiring live user studies or A/B tests with real users")

    return "\n".join(lines) if lines else "No additional user expectations specified."
