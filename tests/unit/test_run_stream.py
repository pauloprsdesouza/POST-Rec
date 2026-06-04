"""Tests for SSE formatting helpers."""

from apps.api.services.run_stream import format_sse


def test_format_sse():
    assert format_sse("run_update", '{"ok":true}') == 'event: run_update\ndata: {"ok":true}\n\n'
