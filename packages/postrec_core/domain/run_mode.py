"""Run mode definitions for recommendation generation."""

from enum import StrEnum


class RunMode(StrEnum):
    QUICK = "quick"
    SOTA = "sota"
    EXPLORATORY = "exploratory"
    FGGV = "fggv"

    @classmethod
    def parse(cls, value: str | None) -> "RunMode":
        if not value:
            return cls.QUICK
        normalized = value.strip().lower()
        for mode in cls:
            if mode.value == normalized:
                return mode
        return cls.QUICK

    @property
    def uses_full_sota_pipeline(self) -> bool:
        return self in (RunMode.SOTA, RunMode.EXPLORATORY, RunMode.FGGV)

    @property
    def uses_fggv_verification(self) -> bool:
        return self == RunMode.FGGV

    @property
    def strict_critic(self) -> bool:
        return self in (RunMode.SOTA, RunMode.FGGV)
