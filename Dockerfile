FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY apps ./apps
COPY packages ./packages
COPY migrations ./migrations
COPY scripts ./scripts
COPY alembic.ini ./

RUN pip install --no-cache-dir -e ".[dev]"

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
