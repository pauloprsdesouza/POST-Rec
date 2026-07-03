#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.deploy_observability_homelab import import_grafana_dashboard, ssh_client

if __name__ == "__main__":
    if not os.environ.get("SSH_PASSWORD"):
        print("Set SSH_PASSWORD", file=sys.stderr)
        raise SystemExit(1)
    client = ssh_client()
    try:
        import_grafana_dashboard(client)
    finally:
        client.close()
