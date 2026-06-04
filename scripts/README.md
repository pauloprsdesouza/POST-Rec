# Scripts

| Script | Purpose |
|--------|---------|
| `bootstrap_homelab.py` | Verify DB/Redis/RabbitMQ and apply migrations |
| `check_migrations.py` | Print Alembic version and key indexes |
| `run_offline_evaluation.py` | Baseline vs FGGV offline metrics (`--ablations` optional) |
| `export_anonymized_validation_data.py` | Export validation data for analysis |
| `run_worker.ps1` | Start Celery worker on Windows |
| `remote_setup.py` / `remote_finish_setup.py` | Deploy to homelab host |
| `enable_rabbitmq_celery_compat.py` | One-off RabbitMQ 4 + Celery compatibility on homelab |
