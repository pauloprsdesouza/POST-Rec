"""One-shot refactor: move apps/api to vertical slice layout and rewrite imports."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "apps" / "api"

MOVES: list[tuple[str, str]] = [
    ("database.py", "shared/database.py"),
    ("dependencies.py", "shared/dependencies.py"),
    ("settings.py", "shared/settings.py"),
    ("models.py", "shared/models.py"),
    ("observability", "shared/observability"),
    ("schemas/common.py", "shared/schemas/common.py"),
    ("services/cache_service.py", "shared/infra/cache.py"),
    ("services/embedding_config.py", "shared/infra/embedding_config.py"),
    ("services/http_retry.py", "shared/infra/http_retry.py"),
    ("services/source_rate_limiter.py", "shared/infra/source_rate_limiter.py"),
    ("services/resilience", "shared/infra/resilience"),
    ("routers/auth.py", "features/auth/router.py"),
    ("routers/users.py", "features/users/router.py"),
    ("services/auth_service.py", "features/auth/service.py"),
    ("services/evolution_service.py", "features/auth/evolution.py"),
    ("services/profile_service.py", "features/profile/service.py"),
    ("services/run_service.py", "features/runs/service.py"),
    ("services/run_query.py", "features/runs/query.py"),
    ("services/run_events.py", "features/runs/events.py"),
    ("services/run_cost.py", "features/runs/cost.py"),
    ("services/run_stream.py", "features/runs/stream.py"),
    ("services/run_stream_service.py", "features/runs/stream_service.py"),
    ("services/retrieval_service.py", "features/retrieval/service.py"),
    ("services/corpus_retrieval_service.py", "features/retrieval/corpus.py"),
    ("services/vector_retrieval_service.py", "features/retrieval/vector.py"),
    ("services/retrieval_cache.py", "features/retrieval/cache.py"),
    ("services/fetch_queue.py", "features/retrieval/fetch_queue.py"),
    ("services/relevance_service.py", "features/retrieval/relevance.py"),
    ("services/sota_pipeline_service.py", "features/recommendations/pipeline.py"),
    ("services/hybrid_ranking_service.py", "features/recommendations/ranking.py"),
    ("services/novelty_verification_service.py", "features/recommendations/novelty.py"),
    ("services/facet_verification_service.py", "features/recommendations/facets.py"),
    ("services/source_service.py", "features/recommendations/sources.py"),
    ("services/llm_service.py", "features/recommendations/llm.py"),
    ("services/feedback_service.py", "features/feedback/service.py"),
    ("services/ranking_calibration_service.py", "features/feedback/calibration.py"),
    ("services/validation_metrics_service.py", "features/validation/service.py"),
    ("services/sota_metrics_service.py", "features/validation/metrics.py"),
    ("services/notification_service.py", "features/notifications/service.py"),
]

IMPORT_REPLACEMENTS: list[tuple[str, str]] = [
    ("from apps.api.services.resilience", "from apps.api.shared.infra.resilience"),
    ("from apps.api.services.cache_service", "from apps.api.shared.infra.cache"),
    ("from apps.api.services.embedding_config", "from apps.api.shared.infra.embedding_config"),
    ("from apps.api.services.http_retry", "from apps.api.shared.infra.http_retry"),
    ("from apps.api.services.source_rate_limiter", "from apps.api.shared.infra.source_rate_limiter"),
    ("import apps.api.services.cache_service", "import apps.api.shared.infra.cache as cache_service_module"),
    ("from apps.api.services.retrieval_service", "from apps.api.features.retrieval.service"),
    ("from apps.api.services.corpus_retrieval_service", "from apps.api.features.retrieval.corpus"),
    ("from apps.api.services.vector_retrieval_service", "from apps.api.features.retrieval.vector"),
    ("from apps.api.services.retrieval_cache", "from apps.api.features.retrieval.cache"),
    ("from apps.api.services.fetch_queue", "from apps.api.features.retrieval.fetch_queue"),
    ("from apps.api.services.relevance_service", "from apps.api.features.retrieval.relevance"),
    ("from apps.api.services.run_stream_service", "from apps.api.features.runs.stream_service"),
    ("from apps.api.services.run_service", "from apps.api.features.runs.service"),
    ("from apps.api.services.run_query", "from apps.api.features.runs.query"),
    ("from apps.api.services.run_events", "from apps.api.features.runs.events"),
    ("from apps.api.services.run_cost", "from apps.api.features.runs.cost"),
    ("from apps.api.services.run_stream", "from apps.api.features.runs.stream"),
    ("from apps.api.services.sota_pipeline_service", "from apps.api.features.recommendations.pipeline"),
    ("from apps.api.services.hybrid_ranking_service", "from apps.api.features.recommendations.ranking"),
    ("from apps.api.services.novelty_verification_service", "from apps.api.features.recommendations.novelty"),
    ("from apps.api.services.facet_verification_service", "from apps.api.features.recommendations.facets"),
    ("from apps.api.services.source_service", "from apps.api.features.recommendations.sources"),
    ("from apps.api.services.llm_service", "from apps.api.features.recommendations.llm"),
    ("from apps.api.services.feedback_service", "from apps.api.features.feedback.service"),
    ("from apps.api.services.ranking_calibration_service", "from apps.api.features.feedback.calibration"),
    ("from apps.api.services.validation_metrics_service", "from apps.api.features.validation.service"),
    ("from apps.api.services.sota_metrics_service", "from apps.api.features.validation.metrics"),
    ("from apps.api.services.notification_service", "from apps.api.features.notifications.service"),
    ("from apps.api.services.profile_service", "from apps.api.features.profile.service"),
    ("from apps.api.services.auth_service", "from apps.api.features.auth.service"),
    ("from apps.api.services.evolution_service", "from apps.api.features.auth.evolution"),
    ("from apps.api.routers.auth", "from apps.api.features.auth.router"),
    ("from apps.api.routers.users", "from apps.api.features.users.router"),
    ("from apps.api.routers.api", "from apps.api.features"),
    ("from apps.api.database", "from apps.api.shared.database"),
    ("from apps.api.dependencies", "from apps.api.shared.dependencies"),
    ("from apps.api.settings", "from apps.api.shared.settings"),
    ("from apps.api.models", "from apps.api.shared.models"),
    ("from apps.api.schemas.common", "from apps.api.shared.schemas.common"),
    ("from apps.api.observability", "from apps.api.shared.observability"),
    ("import apps.api.database", "import apps.api.shared.database"),
    ("import apps.api.settings", "import apps.api.shared.settings"),
]


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def move_paths() -> None:
    for src_rel, dst_rel in MOVES:
        src = API / src_rel
        dst = API / dst_rel
        if not src.exists():
            print(f"SKIP missing: {src_rel}")
            continue
        ensure_parent(dst)
        if dst.exists():
            print(f"SKIP exists: {dst_rel}")
            continue
        src.rename(dst)
        print(f"MOVED {src_rel} -> {dst_rel}")


def rewrite_imports_in_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in IMPORT_REPLACEMENTS:
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def rewrite_all_python() -> int:
    changed = 0
    for path in ROOT.rglob("*.py"):
        if "refactor_vertical_slices.py" in str(path):
            continue
        if rewrite_imports_in_file(path):
            changed += 1
    return changed


def create_init_files() -> None:
    dirs = [
        API / "shared",
        API / "shared/schemas",
        API / "shared/infra",
        API / "features",
        API / "features/auth",
        API / "features/users",
        API / "features/profile",
        API / "features/runs",
        API / "features/retrieval",
        API / "features/recommendations",
        API / "features/feedback",
        API / "features/validation",
        API / "features/notifications",
        API / "features/sessions",
        API / "features/consent",
        API / "features/survey",
        API / "features/health",
    ]
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
        init_file = directory / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Feature slice."""\n', encoding="utf-8")


def cleanup_empty_dirs() -> None:
    for rel in ("services", "routers", "schemas", "observability"):
        path = API / rel
        if path.exists() and not any(path.rglob("*")):
            path.rmdir()
            print(f"REMOVED empty dir: {rel}")


def main() -> None:
    create_init_files()
    move_paths()
    changed = rewrite_all_python()
    cleanup_empty_dirs()
    print(f"Updated imports in {changed} files")


if __name__ == "__main__":
    main()
