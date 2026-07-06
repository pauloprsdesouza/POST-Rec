"""Shared deploy configuration helpers (env files, domain registry)."""

from __future__ import annotations

import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = PROJECT_ROOT / "deploy" / "apps" / "registry.json"


def load_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def deploy_domain(*, project_root: Path = PROJECT_ROOT) -> str:
    domain = os.environ.get("DEPLOY_DOMAIN", "").strip()
    if domain:
        return domain
    if REGISTRY_PATH.is_file():
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        if data.get("domain"):
            return str(data["domain"])
    return ""


def require_deploy_domain(*, project_root: Path = PROJECT_ROOT) -> str:
    domain = deploy_domain(project_root=project_root)
    if not domain:
        raise ValueError("Set DEPLOY_DOMAIN or configure deploy/apps/registry.json")
    return domain
