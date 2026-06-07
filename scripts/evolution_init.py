#!/usr/bin/env python3
"""Create the POST-Rec Evolution API WhatsApp instance if it does not exist."""

from __future__ import annotations

import os
import sys
import time

import httpx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def wait_for_api(base_url: str, api_key: str, *, timeout_seconds: int = 120) -> None:
    deadline = time.time() + timeout_seconds
    headers = {"apikey": api_key}
    while time.time() < deadline:
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{base_url.rstrip('/')}/", headers=headers)
                if response.status_code < 500:
                    return
        except httpx.RequestError:
            pass
        time.sleep(3)
    raise RuntimeError(f"Evolution API did not become ready at {base_url}")


def fetch_instances(base_url: str, api_key: str) -> list[dict]:
    headers = {"apikey": api_key}
    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            f"{base_url.rstrip('/')}/instance/fetchInstances",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("instances") or data.get("data") or []
    return []


def instance_name(entry: dict) -> str:
    return str(entry.get("name") or entry.get("instanceName") or "")


def create_instance(base_url: str, api_key: str, name: str) -> None:
    headers = {"apikey": api_key, "Content-Type": "application/json"}
    payload = {
        "instanceName": name,
        "integration": "WHATSAPP-BAILEYS",
        "qrcode": True,
    }
    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            f"{base_url.rstrip('/')}/instance/create",
            json=payload,
            headers=headers,
        )
        if response.status_code == 403 and "already in use" in response.text.lower():
            return
        response.raise_for_status()


def main() -> int:
    base_url = _env("EVOLUTION_API_URL", "http://evolution-api:8080")
    api_key = _env("EVOLUTION_API_KEY", "dev-evolution-api-key")
    name = _env("EVOLUTION_INSTANCE_NAME", "postrec")

    if not api_key or not name:
        print("Evolution init skipped (EVOLUTION_API_KEY or EVOLUTION_INSTANCE_NAME missing).")
        return 0

    print(f"Waiting for Evolution API at {base_url}...")
    wait_for_api(base_url, api_key)

    instances = fetch_instances(base_url, api_key)
    if any(instance_name(item) == name for item in instances):
        print(f"Evolution instance '{name}' already exists.")
    else:
        print(f"Creating Evolution instance '{name}'...")
        create_instance(base_url, api_key, name)
        print(f"Evolution instance '{name}' created.")

    print(
        "Pair WhatsApp: open http://localhost:3000 (Evolution Manager), "
        f"select instance '{name}', and scan the QR code."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
