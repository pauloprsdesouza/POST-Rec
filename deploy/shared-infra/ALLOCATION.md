# Shared PostgreSQL & Redis allocation

Single instances serve POST-Rec and Evolution API.

## PostgreSQL (`pgvector/pgvector:pg16`)

| Database   | User       | Purpose              | Host (POST-Rec net) |
|------------|------------|----------------------|---------------------|
| `postrec`  | `postrec`  | POST-Rec app + Alembic | `postgres`          |
| `evolution`| `evolution`| Evolution API (Prisma) | `postgres`          |

- `postrec` is created by the container `POSTGRES_DB` on first boot.
- `evolution` is created by `shared-db-init`.
- Enable `vector` in `postrec` via Alembic migrations (existing flow).

## Redis (`redis:7-alpine`, no password on internal Docker network)

| DB index | Consumer        | Env variable / notes                          |
|----------|-----------------|-----------------------------------------------|
| 0        | POST-Rec        | `REDIS_URL`                                   |
| 1        | POST-Rec Celery | `CELERY_RESULT_BACKEND`                       |
| 2        | POST-Rec cache  | `CACHE_REDIS_DB`                              |
| 3        | Evolution API   | `CACHE_REDIS_URI` + prefix `evolution`        |

Reserved for future stacks: DB 4–15.

## Networks

- POST-Rec services use `post-rec_default`.
- Edge routing services (web, landing, proxies, evolution-api) join internal `proxy` network for Traefik.

## Risks

- **Single point of failure**: one Postgres/Redis outage affects all stacks.
- **Backup coupling**: snapshot/restore must include all databases; test restore regularly.
- **Redis isolation**: logical DB indexes only — not as strong as separate instances; prefixes and DB indexes prevent key collisions.

## Verification

```bash
# POST-Rec stack
docker compose exec postgres psql -U postrec -d postgres -c '\l'
docker compose exec redis redis-cli INFO keyspace

# Evolution
docker compose exec evolution-api wget -qO- http://127.0.0.1:8080/
```
