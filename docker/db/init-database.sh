#!/bin/sh

set -e

export PGUSER="$POSTGRES_USER"

psql -c "ALTER SYSTEM SET max_connections = '100';"
psql -c "ALTER SYSTEM SET shared_buffers = '1GB';"
psql -c "ALTER SYSTEM SET effective_cache_size = '3GB';"
psql -c "ALTER SYSTEM SET maintenance_work_mem = '256MB';"
psql -c "ALTER SYSTEM SET checkpoint_completion_target = '0.7';"
psql -c "ALTER SYSTEM SET wal_buffers = '16MB';"
psql -c "ALTER SYSTEM SET default_statistics_target = '100';"
psql -c "ALTER SYSTEM SET random_page_cost = '1.1';"
psql -c "ALTER SYSTEM SET effective_io_concurrency = '200';"
psql -c "ALTER SYSTEM SET work_mem = '6990kB';"
psql -c "ALTER SYSTEM SET min_wal_size = '1GB';"
psql -c "ALTER SYSTEM SET max_wal_size = '2GB';"
psql -c "ALTER SYSTEM SET max_worker_processes = '2';"
psql -c "ALTER SYSTEM SET max_parallel_workers_per_gather = '1';"
psql -c "ALTER SYSTEM SET max_parallel_workers = '2';"

psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_USER_PASSWORD';"
psql -c "CREATE DATABASE $DB_NAME;"
psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
psql -c "ALTER DATABASE $DB_NAME OWNER TO $DB_USER;"

if [ -f /opt/backups/restore.dump ]; then
  echo "Restoring backup..."
  pg_restore -d $DB_NAME --clean --if-exists /opt/backups/restore.dump
fi
