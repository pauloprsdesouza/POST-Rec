# Scripts

| Script | Purpose |
|--------|---------|
| `evolution_init.py` | Create Evolution API WhatsApp instance `postrec` if missing |
| `verify_stack.py` | Check Postgres/pgvector, Redis, RabbitMQ, MinIO, Evolution API (run on host or `docker compose exec api …`) |
| `docker_bootstrap.ps1` / `docker_bootstrap.sh` | Start infra or full stack; optional `-FullStack` runs migrate + verify |
| `docker_migrate.py` | Alembic + missing ORM tables (used by `migrate` service) |
| `bootstrap_homelab.py` | Verify DB/Redis/RabbitMQ and apply migrations |
| `check_migrations.py` | Print Alembic version and key indexes |
| `run_offline_evaluation.py` | Baseline vs FGGV offline metrics (`--ablations` optional) |
| `export_anonymized_validation_data.py` | Export validation data for analysis |
| `export_analysis_dataset.py` | Export analysis-ready CSV/JSON datasets |
| `generate_research_report.py` | Generate full research report JSON offline |
| `run_worker.ps1` | Start Celery worker on Windows |
| `remote_setup.py` / `remote_finish_setup.py` | Deploy to homelab host |
| `hostinger_deploy.py`, `configure_domain.py`, `deploy_portainer.py`, `deploy_shared_infra.py` | Production deploy (`HOSTINGER_HOST`, `HOSTINGER_SSH_PASSWORD`) |
| `deploy_observability_homelab.py`, `import_grafana_dashboard.py` | Observability stack deploy |
| `validate_grafana_api.py`, `validate_grafana_ops.py`, `validate_grafana_business_sql.py` | Post-deploy Grafana validation |
| `openalex_probe.py` | Local OpenAlex diagnostic |
| `ssh_run.py`, `check_celery_metrics.py` | Remote ops helpers (`SSH_PASSWORD`, `SSH_HOST`, optional `SSH_USER`) |
| `seed_qualis.py`, `migrate_coolify_shared_db.py` | Data / infra |
| `enable_rabbitmq_celery_compat.py` | One-off RabbitMQ 4 + Celery compatibility on homelab |
| `generate_traefik_apps.py` | Traefik config generation |
| `benchmark_openalex_filters.py`, `openalex_scenarios.py`, `validate_openalex_config.py` | OpenAlex tuning |

Ad-hoc debug scripts (`scripts/_*.py`) are gitignored — use `ssh_run.py` with env-based credentials instead.
