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

### Docker (API + worker + web only)

```powershell
docker compose up --build
```

Broker, database, and Redis are **not** included in `docker-compose.yml`; point `.env` at your own instances.

## Homelab deployment

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
