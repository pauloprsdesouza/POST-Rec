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
| `run_worker.ps1` | Start Celery worker on Windows |
| `remote_setup.py` / `remote_finish_setup.py` | Deploy to homelab host |
| `enable_rabbitmq_celery_compat.py` | One-off RabbitMQ 4 + Celery compatibility on homelab |
