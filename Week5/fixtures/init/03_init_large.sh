#!/bin/bash
set -e

echo "Initializing erp_large database..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "erp_large" <<'EOSQL'
-- Load schema
\i /docker-entrypoint-initdb.d/large/01_schema.sql

-- Load data
\i /docker-entrypoint-initdb.d/large/02_data.sql
EOSQL

echo "✓ erp_large initialized"
