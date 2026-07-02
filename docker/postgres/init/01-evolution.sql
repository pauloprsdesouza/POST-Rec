-- Evolution API database (separate DB on shared PostgreSQL).
-- Applied on first postgres boot and idempotently by shared-db-init.

DO $$
BEGIN
  CREATE USER evolution WITH PASSWORD 'evolution';
EXCEPTION
  WHEN duplicate_object THEN NULL;
END
$$;

SELECT 'CREATE DATABASE evolution OWNER evolution'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'evolution')\gexec

GRANT ALL PRIVILEGES ON DATABASE evolution TO evolution;
