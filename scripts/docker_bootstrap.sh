#!/usr/bin/env bash
# Bootstrap local Docker infrastructure for POST-Rec.
# Usage:
#   ./scripts/docker_bootstrap.sh              # infra only
#   ./scripts/docker_bootstrap.sh --full       # infra + api + worker + web

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FULL_STACK=false
if [[ "${1:-}" == "--full" ]]; then
  FULL_STACK=true
fi

if [[ ! -f .env ]]; then
  if $FULL_STACK && [[ -f .env.docker.example ]]; then
    cp .env.docker.example .env
    echo "Created .env from .env.docker.example — add GEMINI_API_KEY before production runs."
  elif [[ -f .env.local.infra.example ]]; then
    cp .env.local.infra.example .env
    echo "Created .env from .env.local.infra.example — add GEMINI_API_KEY as needed."
  fi
fi

echo "Starting POST-Rec Docker infrastructure..."
docker compose up -d postgres redis rabbitmq minio minio-init evolution-postgres evolution-redis evolution-api evolution-manager

echo "Waiting for PostgreSQL..."
for _ in $(seq 1 30); do
  if docker compose exec -T postgres pg_isready -U postrec -d postrec >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "Running database migrations..."
docker compose run --rm migrate

echo "Ensuring Evolution WhatsApp instance..."
docker compose run --rm evolution-init

cat <<EOF

Infrastructure ready:
  PostgreSQL (pgvector)  localhost:5432  postrec / postrec
  Redis                  localhost:6379
  RabbitMQ               localhost:5672  postrec / postrec
  RabbitMQ management    http://localhost:15672
  MinIO API              localhost:9000  minioadmin / minioadmin
  MinIO console          http://localhost:9001
  Evolution API          http://localhost:8080  (apikey: dev-evolution-api-key)
  Evolution Manager      http://localhost:3000  (scan QR for instance postrec)
EOF

if $FULL_STACK; then
  echo ""
  echo "Starting application services..."
  docker compose up --build -d api worker web
  cat <<EOF
  API       http://localhost:8000
  Web UI    http://localhost:5173
  API docs  http://localhost:8000/docs
EOF
else
  cat <<EOF

Run the app on the host:
  uvicorn apps.api.main:app --reload --port 8000
  celery -A apps.api.workers.celery_app worker --loglevel=INFO
  cd apps/web && npm run dev
EOF
fi
