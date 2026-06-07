"""PostgreSQL ENUM types shared by ORM models."""

from sqlalchemy import Enum as SAEnum

from packages.postrec_core.domain.enums import CandidateStatus, RunStatus, SessionStatus
from packages.postrec_core.domain.run_mode import RunMode


def _pg_enum(enum_cls, name: str) -> SAEnum:
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=True,
        values_callable=lambda members: [member.value for member in members],
    )


run_status_enum = _pg_enum(RunStatus, "run_status")
run_mode_enum = _pg_enum(RunMode, "run_mode")
session_status_enum = _pg_enum(SessionStatus, "session_status")
candidate_status_enum = _pg_enum(CandidateStatus, "candidate_status")
