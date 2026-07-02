# Retrieval API resilience

POST-Rec applies patterns used by large-scale API clients (AWS, Google, Stripe):

| Pattern | Implementation |
|---------|----------------|
| **Exponential backoff + full jitter** | `http_retry.full_jitter_backoff` — `sleep = random(0, min(cap, base × 2^n))` |
| **Respect `Retry-After`** | Parsed from 429/503 responses when present |
| **Token pacing** | OpenAlex minimum interval via Redis (or in-process fallback) |
| **Circuit breaker** | Opens after repeated 429/503; fail-fast instead of hammering |
| **Response cache** | Redis cache of fetch results (6h default) across runs |
| **Graceful degradation** | Early stop when enough unique papers + circuit open |
| **Source** | OpenAlex only (field/subfield/topic filters + optional recall fallback) |

## Configuration (`.env`)

```env
RETRIEVAL_HTTP_RETRIES=4
RETRIEVAL_FETCH_MAX_ATTEMPTS=5
RETRIEVAL_CACHE_ENABLED=true
RETRIEVAL_CACHE_TTL_SECONDS=21600
RETRIEVAL_CIRCUIT_FAILURE_THRESHOLD=4
RETRIEVAL_CIRCUIT_COOLDOWN_SECONDS=120
RETRIEVAL_MIN_PAPERS_BEFORE_SKIP=12
RETRIEVAL_OPENALEX_MIN_INTERVAL=0.35
OPENALEX_API_KEY=            # required for search (free at openalex.org/settings/api)
OPENALEX_EMAIL=              # optional contact string in User-Agent
```

## Tips

1. Set **OpenAlex API key** for rate-limit and cost telemetry.
2. Ensure **Redis** is reachable — shared rate limiter, circuit state, fetch cache, and taxonomy cache.
3. Re-run similar topics within cache TTL to avoid duplicate 429 storms.
4. Tune filter tier (`balanced` / `strict` / `recall`) with `scripts/validate_openalex_config.py`.

## Consolidated retrieval strategy

POST-Rec uses fewer, higher-yield OpenAlex calls:

| Technique | Benefit |
|-----------|---------|
| **Consolidated query plan** | ~4–8 jobs/run instead of keyword fan-out |
| **Larger page sizes** | OpenAlex `per_page=100` |
| **Server-side filters** | `has_abstract`, field/subfield/topic, `is_paratext:false` |
| **Corpus prefetch** | Reuse matching `source_document` rows (free, no API) |
| **Citation expansion** | `cites:` / `related_to:` when corpus is sparse |
| **DOI batch enrichment** | Fill missing abstracts from OpenAlex by DOI |
