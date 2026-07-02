-- Coolify platform database (separate DB on shared PostgreSQL).
-- Production password is set by scripts/migrate_coolify_shared_db.py from /data/coolify/source/.env.
-- Local default password matches Coolify installer defaults.

DO $$
BEGIN
  CREATE USER coolify WITH PASSWORD 'coolify';
EXCEPTION
  WHEN duplicate_object THEN NULL;
END
$$;

SELECT 'CREATE DATABASE coolify OWNER coolify'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'coolify')\gexec

GRANT ALL PRIVILEGES ON DATABASE coolify TO coolify;
