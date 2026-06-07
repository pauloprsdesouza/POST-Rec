# POST-Rec

**Paper-Oriented Scientific Topic Recommender** — research ideas grounded in retrieved literature, with verified novelty scoring and volunteer validation.

## Features

- **Hybrid retrieval** — OpenAlex, Crossref, Semantic Scholar; BM25 + dense + pgvector ranking
- **Run modes** — `quick`, `sota`, `exploratory`, and **FGGV** (Facet-Grounded Gap Verification)
- **SOTA pipeline** — landscape → gap matrix → proposals → critic → verified ranking
- **FGGV** — per-facet novelty, gap alignment, saturation-aware scoring, diversity selection ([docs](docs/fggv-evaluation.md))
- **Expectation Alignment Score (EAS)** — feedback-driven calibration
- **Auth** — WhatsApp OTP (optional Evolution API)

## Stack

| Layer | Technology |
|-------|------------|
| UI | React, Bootstrap, Vite, TypeScript |
| API | FastAPI |
| Workers | Celery, RabbitMQ, Redis |
| Data | PostgreSQL + pgvector |
| LLM | Google Gemini (generation + embeddings) |

## Prerequisites

- Python 3.11+
- Node.js 20+ (for the web UI)
- PostgreSQL with [pgvector](https://github.com/pgvector/pgvector)
- RabbitMQ and Redis (for async runs)
- [GitHub CLI](https://cli.github.com/) (optional, for deployment scripts)
- Google Gemini API key ([AI Studio](https://aistudio.google.com/apikey))

## Quick start

### 1. Clone and configure

```powershell
git clone https://github.com/pauloprsdesouza/POST-Rec.git
cd POST-Rec
copy .env.example .env
# Edit .env: DATABASE_URL, RabbitMQ, Redis, GEMINI_API_KEY
```

### 2. Install dependencies

```powershell
pip install -e ".[dev]"
cd apps/web
npm install
cd ../..
```

### 3. Database

```powershell
py -m alembic upgrade head
# Or: py scripts/bootstrap_homelab.py  (verifies connections + migrates)
```

### 4. Run locally (three terminals)

```powershell
# API
uvicorn apps.api.main:app --reload --port 8000

# Worker
celery -A apps.api.workers.celery_app worker --loglevel=INFO

# Web UI
cd apps/web
npm run dev
```

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| Web UI | http://localhost:5173 |
| API docs | http://localhost:8000/docs |

### Docker (recommended when homelab is offline)

POST-Rec needs **PostgreSQL + pgvector**, **Redis**, **RabbitMQ**, and **MinIO**. All are included in `docker-compose.yml`.

**Option A — infrastructure only** (run API/worker/web on the host):

```powershell
copy .env.local.infra.example .env
# Edit .env: GEMINI_API_KEY, optional API keys
.\scripts\docker_bootstrap.ps1
py -m alembic upgrade head   # if bootstrap did not migrate
uvicorn apps.api.main:app --reload --port 8000
celery -A apps.api.workers.celery_app worker --loglevel=INFO
cd apps/web; npm run dev
```

**Option B — full stack in Docker**:

```powershell
copy .env.docker.example .env
# Edit .env: GEMINI_API_KEY
.\scripts\docker_bootstrap.ps1 -FullStack
# Or: docker compose up --build
```

| Service | URL | Credentials |
|---------|-----|-------------|
| API | http://localhost:8000 | — |
| Web UI | http://localhost:5173 | — |
| PostgreSQL | localhost:5432 | `postrec` / `postrec` |
| Redis | localhost:6379 | no auth |
| RabbitMQ | localhost:5672 | `postrec` / `postrec` |
| RabbitMQ UI | http://localhost:15672 | `postrec` / `postrec` |
| MinIO | localhost:9000 | `minioadmin` / `minioadmin` |
| MinIO console | http://localhost:9001 | `minioadmin` / `minioadmin` |
| Evolution API | http://localhost:8080 | apikey `dev-evolution-api-key` |
| Evolution Manager (QR) | http://localhost:3000 | pair instance `postrec` |

**WhatsApp OTP:** Evolution API starts with the infra stack. After first boot, open **Evolution Manager** at http://localhost:3000, select instance `postrec`, and scan the QR code with WhatsApp. Until paired, OTP sends will fail (dev mode still logs codes in the API).

Stop everything: `docker compose down`. Remove data volumes: `docker compose down -v`.

**Verify the stack** (after `docker compose up`):

```powershell
docker compose exec api python scripts/verify_stack.py
docker compose exec worker celery -A apps.api.workers.celery_app inspect ping
Invoke-RestMethod http://localhost:8000/api/v1/health
```

For **infra in Docker + app on the host**, copy `.env.local.infra.example` to `.env` (your old homelab credentials will not match local Postgres/RabbitMQ/Redis), then:

```powershell
py scripts/verify_stack.py
```

When the **homelab** (`192.168.10.13`) is back online, copy `.env.remote.example` to `.env` and run `py scripts/bootstrap_homelab.py` or `py scripts/verify_stack.py`.

### Docker (legacy note)

If you still use a remote homelab host, point `.env` at that host and run only `docker compose up api worker web` — or skip Docker entirely and use the three-terminal flow above.


For a shared infrastructure host (PostgreSQL, Redis, RabbitMQ, MinIO), configure hosts in `.env` and use:

- `py scripts/bootstrap_homelab.py` — connectivity check and schema
- `py scripts/remote_setup.py` — remote deploy helper (optional)

## Run modes

| Mode | Description |
|------|-------------|
| `quick` | Single-pass generation with SOTA fields and novelty verification |
| `sota` | Full landscape → gaps → proposals with strict critic |
| `exploratory` | Same pipeline, higher novelty weight |
| `fggv` | Facet-grounded gap verification (proposed method for evaluation) |

## Evaluation

```powershell
py -m pytest tests/unit -q
py scripts/run_offline_evaluation.py --ablations
```

See [docs/fggv-evaluation.md](docs/fggv-evaluation.md) for baselines and human-study protocol.

Retrieval uses circuit breakers, full-jitter backoff, and Redis caching for 429 resilience — see [docs/retrieval-resilience.md](docs/retrieval-resilience.md).

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | Required for production LLM calls |
| `GEMINI_GENERATION_MODEL` | `gemini-2.5-flash-lite` | Recommendation generation |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` | Paper embeddings (768 dims) |
| `DATABASE_URL` | — | PostgreSQL connection string |

Without `GEMINI_API_KEY`, the API uses deterministic fallbacks for development.

## Project layout

```
apps/api/          FastAPI, services, Celery workers
apps/web/          React frontend
packages/postrec_core/   Domain logic, retrieval, scoring, FGGV
migrations/        Alembic schema revisions
scripts/           Bootstrap, evaluation, homelab helpers
tests/             Unit and evaluation tests
docs/              FGGV protocol and archived specs
```

## Documentation

- [docs/README.md](docs/README.md) — index
- [docs/fggv-evaluation.md](docs/fggv-evaluation.md) — method, baselines, empirical protocol
- [scripts/README.md](scripts/README.md) — utility scripts

## License

[MIT](LICENSE)
