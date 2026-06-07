"""Blind A/B experiment assignment for recommendation runs."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from packages.postrec_core.domain.run_mode import RunMode

EXPERIMENT_VARIANT_CONTROL = "control"
EXPERIMENT_VARIANT_TREATMENT = "treatment"
PRESENTATION_STANDARD = "standard"
PRESENTATION_BLIND = "blind"

CONTROL_MODE = RunMode.SOTA.value
TREATMENT_MODE = RunMode.FGGV.value


@dataclass(frozen=True)
class ExperimentAssignment:
    mode: str
    experiment_id: str | None = None
    experiment_variant: str | None = None
    assigned_mode: str | None = None
    presentation_profile: str = PRESENTATION_STANDARD

    @property
    def in_experiment(self) -> bool:
        return self.experiment_id is not None


def _stable_bucket(user_id: str, experiment_id: str) -> int:
    digest = hashlib.sha256(f"{experiment_id}:{user_id}".encode()).hexdigest()
    return int(digest[:8], 16) % 100


def is_user_enrolled(*, avoid_real_user_experiments: bool) -> bool:
    return not avoid_real_user_experiments


def resolve_experiment_assignment(
    *,
    user_id: str | None,
    requested_mode: str,
    avoid_real_user_experiments: bool,
    experiment_enabled: bool,
    experiment_id: str,
    treatment_fraction: float,
) -> ExperimentAssignment:
    """Assign control (sota) vs treatment (fggv) for blind study participants."""
    if not experiment_enabled or not user_id or avoid_real_user_experiments:
        mode = RunMode.parse(requested_mode).value
        return ExperimentAssignment(mode=mode, presentation_profile=PRESENTATION_STANDARD)

    bucket = _stable_bucket(user_id, experiment_id)
    threshold = max(0, min(100, int(round(treatment_fraction * 100))))
    variant = EXPERIMENT_VARIANT_TREATMENT if bucket < threshold else EXPERIMENT_VARIANT_CONTROL
    assigned_mode = TREATMENT_MODE if variant == EXPERIMENT_VARIANT_TREATMENT else CONTROL_MODE

    return ExperimentAssignment(
        mode=assigned_mode,
        experiment_id=experiment_id,
        experiment_variant=variant,
        assigned_mode=assigned_mode,
        presentation_profile=PRESENTATION_BLIND,
    )
