"""Tests for Traefik/landing generation security defaults."""

import json
from pathlib import Path

from scripts.generate_traefik_apps import (
    generate_landing,
    generate_traefik,
    generate_unknown_page,
    load_registry,
    show_apps_on_landing,
)


def test_landing_hides_apps_by_default():
    reg = load_registry(Path("deploy/apps/registry.json"))
    assert show_apps_on_landing(reg, reg["apps"]) is False

    landing = generate_landing(reg["domain"], reg, reg["apps"])
    assert "Published applications" not in landing
    assert "/portainer" not in landing
    assert "/grafana" not in landing
    assert "/researchly" not in landing

    unknown = generate_unknown_page(reg, reg["apps"])
    assert "Available apps" not in unknown
    assert "/portainer" not in unknown


def test_traefik_includes_security_middlewares():
    reg = load_registry(Path("deploy/apps/registry.json"))
    traefik = generate_traefik(reg["domain"], reg["apps"])
    assert "security-headers:" in traefik
    assert "redirect-to-https:" in traefik
    assert "stsSeconds: 31536000" in traefik
    assert "middlewares: [redirect-to-https" in traefik
    assert "middlewares: [security-headers" in traefik


def test_show_apps_when_explicitly_enabled(tmp_path: Path):
    reg = {
        "domain": "example.com",
        "landing": {"show_apps": True},
        "apps": {
            "demo": {
                "title": "Demo",
                "description": "Demo app",
                "service_host": "demo",
                "base_path": "/demo",
                "list_publicly": True,
            }
        },
    }
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(reg), encoding="utf-8")
    loaded = load_registry(path)
    assert show_apps_on_landing(loaded, loaded["apps"]) is True
    landing = generate_landing(loaded["domain"], loaded, loaded["apps"])
    assert "Published applications" in landing
    assert "/demo" in landing
