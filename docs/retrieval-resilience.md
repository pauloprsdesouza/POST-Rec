# Retrieval API resilience

POST-Rec applies patterns used by large-scale API clients (AWS, Google, Stripe):

| Pattern | Implementation |
|---------|----------------|
| **Exponential backoff + full jitter** | `http_retry.full_jitter_backoff` — `sleep = random(0, min(cap, base × 2^n))` |
| **Respect `Retry-After`** | Parsed from 429/503 responses when present |
| **Token pacing** | Per-source minimum intervals via Redis (or in-process fallback) |
| **Circuit breaker** | Opens after repeated 429/503; fail-fast instead of hammering |
| **Response cache** | Redis cache of fetch results (6h default) across runs |
| **Graceful degradation** | Early stop when enough unique papers + circuits open |
| **Source priority** | OpenAlex → Crossref → Semantic Scholar → arXiv |

## Configuration (`.env`)

```env
RETRIEVAL_HTTP_RETRIES=4
RETRIEVAL_FETCH_MAX_ATTEMPTS=5
RETRIEVAL_CACHE_ENABLED=true
RETRIEVAL_CACHE_TTL_SECONDS=21600
RETRIEVAL_CIRCUIT_FAILURE_THRESHOLD=4
RETRIEVAL_CIRCUIT_COOLDOWN_SECONDS=120
RETRIEVAL_MIN_PAPERS_BEFORE_SKIP=12
RETRIEVAL_SEMANTIC_SCHOLAR_MIN_INTERVAL=5.0
RETRIEVAL_ARXIV_MIN_INTERVAL=4.0
SEMANTIC_SCHOLAR_API_KEY=   # strongly recommended — raises rate limits
OPENALEX_EMAIL=             # polite pool identity
CROSSREF_EMAIL=
```

## Tips

1. Set **Semantic Scholar API key** and contact emails for OpenAlex/Crossref.
2. Ensure **Redis** is reachable — shared rate limiter, circuit state, and fetch cache.
3. Re-run similar topics within cache TTL to avoid duplicate 429 storms.
4. If one source stays open, runs still complete using papers from other sources.

## Consolidated retrieval strategy (`feature/retrieval-strategy`)

POST-Rec uses fewer, higher-yield API calls (no paid OpenAlex semantic search):

| Technique | Benefit |
|-----------|---------|
| **Consolidated query plan** | ~10–20 jobs/run instead of 80+ keyword fan-out |
| **Larger page sizes** | OpenAlex `per_page=100`, Crossref `rows=80`, S2 `limit=100` |
| **Server-side filters** | `has_abstract`, OpenAlex `is_paratext:false`, S2 `year=` for SOTA |
| **Corpus prefetch** | Reuse matching `source_document` rows (free, no API) |
| **S2 recommendations** | One POST from top Semantic Scholar seeds (free API) |
| **Targeted arXiv** | Single CS/ML preprint query with `ti`/`abs` fields |

Disable legacy fan-out: `RETRIEVAL_CONSOLIDATED_PLAN_ENABLED=false`
