#!/bin/bash
set -e

echo "Initializing social_medium database..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "social_medium" <<'EOSQL'
-- Load schema
\i /docker-entrypoint-initdb.d/medium/01_schema.sql

-- Load data
\i /docker-entrypoint-initdb.d/medium/02_data.sql
EOSQL

echo "✓ social_medium initialized"
