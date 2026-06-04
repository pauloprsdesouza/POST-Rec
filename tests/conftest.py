"""Pytest configuration."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postrec:postrec@localhost:5432/postrec")
os.environ.setdefault("OTEL_ENABLED", "false")
os.environ.setdefault("AUTH_ENABLED", "false")
