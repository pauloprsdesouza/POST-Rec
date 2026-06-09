"""Lightweight inferential statistics (no scipy dependency)."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class HypothesisTestResult:
    test_name: str
    statistic: float
    p_value: float | None
    effect_size: float | None
    effect_size_name: str | None
    group_a_mean: float
    group_b_mean: float
    group_a_n: int
    group_b_n: int
    significant_at_005: bool
    interpretation: str


def _normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _two_sided_p_from_z(z: float) -> float:
    return round(2.0 * (1.0 - _normal_cdf(abs(z))), 6)


def cohens_d(group_a: Sequence[float], group_b: Sequence[float]) -> float | None:
    if len(group_a) < 2 or len(group_b) < 2:
        return None
    mean_a = sum(group_a) / len(group_a)
    mean_b = sum(group_b) / len(group_b)
    var_a = sum((x - mean_a) ** 2 for x in group_a) / (len(group_a) - 1)
    var_b = sum((x - mean_b) ** 2 for x in group_b) / (len(group_b) - 1)
    pooled = ((len(group_a) - 1) * var_a + (len(group_b) - 1) * var_b) / (len(group_a) + len(group_b) - 2)
    if pooled <= 0:
        return None
    return round((mean_a - mean_b) / math.sqrt(pooled), 4)


def cliffs_delta(group_a: Sequence[float], group_b: Sequence[float]) -> float | None:
    if not group_a or not group_b:
        return None
    greater = sum(1 for a in group_a for b in group_b if a > b)
    less = sum(1 for a in group_a for b in group_b if a < b)
    return round((greater - less) / (len(group_a) * len(group_b)), 4)


def mann_whitney_u(group_a: Sequence[float], group_b: Sequence[float]) -> HypothesisTestResult:
    """Mann-Whitney U with normal approximation for two-sided p-value."""
    a = list(group_a)
    b = list(group_b)
    n1, n2 = len(a), len(b)
    mean_a = sum(a) / n1 if n1 else 0.0
    mean_b = sum(b) / n2 if n2 else 0.0

    if n1 == 0 or n2 == 0:
        return HypothesisTestResult(
            test_name="mann_whitney_u",
            statistic=0.0,
            p_value=None,
            effect_size=cliffs_delta(a, b),
            effect_size_name="cliffs_delta",
            group_a_mean=round(mean_a, 4),
            group_b_mean=round(mean_b, 4),
            group_a_n=n1,
            group_b_n=n2,
            significant_at_005=False,
            interpretation="Insufficient data for test.",
        )

    combined = [(value, 0) for value in a] + [(value, 1) for value in b]
    combined.sort(key=lambda item: item[0])

    ranks: list[float] = [0.0] * len(combined)
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1][0] == combined[i][0]:
            j += 1
        avg_rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[k] = avg_rank
        i = j + 1

    r1 = sum(ranks[idx] for idx, (_, group) in enumerate(combined) if group == 0)
    u1 = r1 - n1 * (n1 + 1) / 2
    u2 = n1 * n2 - u1
    u = min(u1, u2)

    mu = n1 * n2 / 2
    sigma = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    p_value = None
    if sigma > 0:
        z = (u - mu) / sigma
        p_value = _two_sided_p_from_z(z)

    delta = cliffs_delta(a, b)
    return HypothesisTestResult(
        test_name="mann_whitney_u",
        statistic=round(u, 4),
        p_value=p_value,
        effect_size=delta,
        effect_size_name="cliffs_delta",
        group_a_mean=round(mean_a, 4),
        group_b_mean=round(mean_b, 4),
        group_a_n=n1,
        group_b_n=n2,
        significant_at_005=p_value is not None and p_value < 0.05,
        interpretation=_interpret_p(p_value, mean_a, mean_b, "Mann-Whitney U"),
    )


def welch_t_test(group_a: Sequence[float], group_b: Sequence[float]) -> HypothesisTestResult:
    a = list(group_a)
    b = list(group_b)
    n1, n2 = len(a), len(b)
    mean_a = sum(a) / n1 if n1 else 0.0
    mean_b = sum(b) / n2 if n2 else 0.0

    if n1 < 2 or n2 < 2:
        return HypothesisTestResult(
            test_name="welch_t_test",
            statistic=0.0,
            p_value=None,
            effect_size=cohens_d(a, b),
            effect_size_name="cohens_d",
            group_a_mean=round(mean_a, 4),
            group_b_mean=round(mean_b, 4),
            group_a_n=n1,
            group_b_n=n2,
            significant_at_005=False,
            interpretation="Insufficient data for test.",
        )

    var_a = sum((x - mean_a) ** 2 for x in a) / (n1 - 1)
    var_b = sum((x - mean_b) ** 2 for x in b) / (n2 - 1)
    se = math.sqrt(var_a / n1 + var_b / n2)
    if se <= 0:
        t_stat = 0.0
        p_value = 1.0
    else:
        t_stat = (mean_a - mean_b) / se
        df_num = (var_a / n1 + var_b / n2) ** 2
        df_den = (var_a / n1) ** 2 / (n1 - 1) + (var_b / n2) ** 2 / (n2 - 1)
        df = df_num / df_den if df_den > 0 else min(n1, n2)
        p_value = _two_sided_p_from_z(t_stat) if df > 30 else _two_sided_p_from_z(t_stat)

    d = cohens_d(a, b)
    return HypothesisTestResult(
        test_name="welch_t_test",
        statistic=round(t_stat, 4),
        p_value=round(p_value, 6) if p_value is not None else None,
        effect_size=d,
        effect_size_name="cohens_d",
        group_a_mean=round(mean_a, 4),
        group_b_mean=round(mean_b, 4),
        group_a_n=n1,
        group_b_n=n2,
        significant_at_005=p_value is not None and p_value < 0.05,
        interpretation=_interpret_p(p_value, mean_a, mean_b, "Welch t-test"),
    )


def chi_square_2x2(a_success: int, a_total: int, b_success: int, b_total: int) -> HypothesisTestResult:
    """Chi-square test for two proportions (with Yates correction)."""
    if a_total == 0 or b_total == 0:
        return HypothesisTestResult(
            test_name="chi_square_2x2",
            statistic=0.0,
            p_value=None,
            effect_size=None,
            effect_size_name=None,
            group_a_mean=round(a_success / a_total if a_total else 0, 4),
            group_b_mean=round(b_success / b_total if b_total else 0, 4),
            group_a_n=a_total,
            group_b_n=b_total,
            significant_at_005=False,
            interpretation="Insufficient data for test.",
        )

    rate_a = a_success / a_total
    rate_b = b_success / b_total
    total = a_total + b_total
    success = a_success + b_success
    expected_a = success * a_total / total
    expected_b = success * b_total / total
    fail_a = a_total - a_success
    fail_b = b_total - b_success
    fail = fail_a + fail_b
    expected_fail_a = fail * a_total / total
    expected_fail_b = fail * b_total / total

    chi2 = 0.0
    for obs, exp in (
        (a_success, expected_a),
        (b_success, expected_b),
        (fail_a, expected_fail_a),
        (fail_b, expected_fail_b),
    ):
        if exp > 0:
            diff = abs(obs - exp) - 0.5
            chi2 += (diff**2) / exp

    p_value = _two_sided_p_from_z(math.sqrt(chi2))
    return HypothesisTestResult(
        test_name="chi_square_2x2",
        statistic=round(chi2, 4),
        p_value=p_value,
        effect_size=round(rate_a - rate_b, 4),
        effect_size_name="rate_difference",
        group_a_mean=round(rate_a, 4),
        group_b_mean=round(rate_b, 4),
        group_a_n=a_total,
        group_b_n=b_total,
        significant_at_005=p_value is not None and p_value < 0.05,
        interpretation=_interpret_p(p_value, rate_a, rate_b, "Chi-square"),
    )


def compare_groups(
    group_a: Sequence[float],
    group_b: Sequence[float],
    *,
    label_a: str = "Group A",
    label_b: str = "Group B",
) -> dict:
    mw = mann_whitney_u(group_a, group_b)
    tt = welch_t_test(group_a, group_b)
    return {
        "label_a": label_a,
        "label_b": label_b,
        "mann_whitney": _test_to_dict(mw),
        "welch_t_test": _test_to_dict(tt),
        "recommended_test": "mann_whitney" if min(len(group_a), len(group_b)) < 30 else "welch_t_test",
    }


def _test_to_dict(result: HypothesisTestResult) -> dict:
    return {
        "test_name": result.test_name,
        "statistic": result.statistic,
        "p_value": result.p_value,
        "effect_size": result.effect_size,
        "effect_size_name": result.effect_size_name,
        "group_a_mean": result.group_a_mean,
        "group_b_mean": result.group_b_mean,
        "group_a_n": result.group_a_n,
        "group_b_n": result.group_b_n,
        "significant_at_005": result.significant_at_005,
        "interpretation": result.interpretation,
    }


def _interpret_p(p_value: float | None, mean_a: float, mean_b: float, test_name: str) -> str:
    if p_value is None:
        return f"{test_name}: insufficient data."
    direction = "higher" if mean_a > mean_b else "lower" if mean_a < mean_b else "equal"
    if p_value < 0.05:
        return f"{test_name}: Group A is significantly {direction} than Group B (p={p_value:.4f})."
    return f"{test_name}: No significant difference detected (p={p_value:.4f})."
