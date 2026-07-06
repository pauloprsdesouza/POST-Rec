"""Prometheus /metrics HTTP server for Celery (multiprocess-safe)."""

from __future__ import annotations

import os
import shutil
import tempfile
import threading
from pathlib import Path

from apps.api.shared.observability.logging import get_logger

logger = get_logger("postrec-worker-metrics")

_DEFAULT_MULTIPROC_DIR = os.path.join(tempfile.gettempdir(), "postrec-prom")
MULTIPROC_DIR = os.environ.get("PROMETHEUS_MULTIPROC_DIR", _DEFAULT_MULTIPROC_DIR)
_started = False


def prepare_multiprocess_dir() -> None:
    """Reset prometheus_client multiprocess directory before worker pool starts."""
    path = Path(MULTIPROC_DIR)
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = str(path)


def start_worker_metrics_server(port: int = 9101) -> None:
    """Expose aggregated prometheus metrics from all Celery worker processes."""
    global _started
    if _started:
        return

    from wsgiref.simple_server import make_server

    from prometheus_client import CollectorRegistry, make_wsgi_app, multiprocess

    bind_host = os.environ.get("WORKER_METRICS_BIND_HOST", "127.0.0.1")
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    app = make_wsgi_app(registry)

    def serve() -> None:
        httpd = make_server(bind_host, port, app)
        logger.info(
            "worker_metrics_server_started",
            host=bind_host,
            port=port,
            multiproc_dir=MULTIPROC_DIR,
        )
        httpd.serve_forever()

    threading.Thread(target=serve, name="postrec-worker-metrics", daemon=True).start()
    _started = True
