# Scripts

| Script | Purpose |
|--------|---------|
| `evolution_init.py` | Create Evolution API WhatsApp instance `postrec` if missing |
| `verify_stack.py` | Check Postgres/pgvector, Redis, RabbitMQ, MinIO, Evolution API |
| `verify_schema.py` | Verify Alembic head matches DB + key schema expectations |
| `docker_bootstrap.ps1` / `docker_bootstrap.sh` | Start infra or full stack |
| `docker_migrate.py` | Alembic + missing ORM tables (used by `migrate` service) |
| `bootstrap_homelab.py` | Verify DB/Redis/RabbitMQ and apply migrations |
| `check_migrations.py` | Print Alembic version and key indexes |
| `deploy_config.py` | Shared helpers: `load_env_file`, `deploy_domain`, `require_deploy_domain` |
| `run_offline_evaluation.py` | Baseline vs FGGV offline metrics |
| `export_anonymized_validation_data.py` | Export validation data for analysis |
| `export_analysis_dataset.py` | Export analysis-ready CSV/JSON datasets |
| `generate_research_report.py` | Generate full research report JSON offline |
| `run_worker.ps1` | Start Celery worker on Windows |
| `remote_setup.py` / `remote_finish_setup.py` | Homelab infra bootstrap (`SSH_HOST`, `SSH_PASSWORD`, local `.env`) |
| `hostinger_deploy.py`, `publish_hostinger.py`, `configure_domain.py` | Production deploy (`HOSTINGER_HOST`, `HOSTINGER_SSH_PASSWORD`) |
| `deploy_portainer.py`, `deploy_grafana.py` | Production service deploy |
| `grafana_dashboard.py`, `import_grafana_dashboard.py` | Canonical Grafana dashboard build/import |
| `deploy_observability_homelab.py` | Homelab observability deploy (`HOMELAB_HOST`, `SSH_PASSWORD`) |
| `validate_grafana_api.py`, `validate_grafana_ops.py`, `validate_grafana_business_sql.py` | Post-deploy Grafana validation |
| `openalex_probe.py` | Local OpenAlex diagnostic |
| `ssh_run.py`, `check_celery_metrics.py` | Remote ops helpers (`SSH_PASSWORD`, `SSH_HOST`) |
| `seed_qualis.py`, `seed_qualis_hostinger.py` | Data / infra |
| `enable_rabbitmq_celery_compat.py` | One-off RabbitMQ 4 + Celery compatibility |
| `generate_traefik_apps.py` | Traefik config from `deploy/apps/registry.json` |
| `benchmark_openalex_filters.py`, `openalex_scenarios.py`, `validate_openalex_config.py` | OpenAlex tuning |

**Domain config:** `deploy/apps/registry.json` (`domain` field) or `DEPLOY_DOMAIN` env var.

**Secrets:** Never commit passwords. Use `.env` locally; production uses server `.env` with `GRAFANA_ADMIN_PASSWORD`, `JWT_SECRET`, etc.

Ad-hoc debug scripts (`scripts/_*.py`) are gitignored — use `ssh_run.py` with env-based credentials.
