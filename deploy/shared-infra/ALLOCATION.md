# Shared PostgreSQL & Redis allocation

Single instances serve POST-Rec, Evolution API, and the Coolify control plane.

## PostgreSQL (`pgvector/pgvector:pg16`)

| Database   | User       | Purpose              | Host (Coolify net) | Host (POST-Rec net) |
|------------|------------|----------------------|--------------------|---------------------|
| `postrec`  | `postrec`  | POST-Rec app + Alembic | `shared-postgres` | `postgres`          |
| `evolution`| `evolution`| Evolution API (Prisma) | `shared-postgres` | `postgres`          |
| `coolify`  | `coolify`  | Coolify platform DB  | `shared-postgres` | N/A (Coolify only)  |

- `postrec` is created by the container `POSTGRES_DB` on first boot.
- `evolution` and `coolify` are created by `shared-db-init` / migration scripts.
- Enable `vector` in `postrec` via Alembic migrations (existing flow).

## Redis (`redis:7-alpine`, no password on internal Docker network)

| DB index | Consumer        | Env variable / notes                          |
|----------|-----------------|-----------------------------------------------|
| 0        | POST-Rec        | `REDIS_URL`                                   |
| 1        | POST-Rec Celery | `CELERY_RESULT_BACKEND`                       |
| 2        | POST-Rec cache  | `CACHE_REDIS_DB`                              |
| 3        | Evolution API   | `CACHE_REDIS_URI` + prefix `evolution`        |
| 4        | Coolify         | `REDIS_DB` in `/data/coolify/source/.env`     |
| 5        | Coolify cache   | `REDIS_CACHE_DB` in Coolify `.env`            |

Reserved for future stacks: DB 6–15.

## Networks

- POST-Rec services use `post-rec_default`.
- Production `postgres` and `redis` also join external network `coolify` with aliases `shared-postgres` and `shared-redis`.
- Coolify reads `DB_HOST=shared-postgres` and `REDIS_HOST=shared-redis`.

## Risks

- **Single point of failure**: one Postgres/Redis outage affects all stacks.
- **Backup coupling**: snapshot/restore must include all databases; test restore regularly.
- **Coolify coupling**: Coolify upgrades may overwrite `/data/coolify/source/docker-compose*.yml`. Keep `deploy/coolify/docker-compose.shared-db.yml` in POST-Rec and re-copy after upgrades; start Coolify with `docker compose -f docker-compose.shared-db.yml up -d`.
- **Redis isolation**: logical DB indexes only — not as strong as separate instances; prefixes and DB indexes prevent key collisions.

## Verification

```bash
# POST-Rec stack
docker compose exec postgres psql -U postrec -d postgres -c '\l'
docker compose exec redis redis-cli INFO keyspace

# From Coolify container
docker exec coolify php artisan migrate:status
curl -sf http://127.0.0.1:8000/api/health

# Evolution
docker compose exec evolution-api wget -qO- http://127.0.0.1:8080/
```
