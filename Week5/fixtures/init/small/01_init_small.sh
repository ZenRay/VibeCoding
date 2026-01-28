#!/bin/bash
set -e

echo "Initializing ecommerce_small database..."

# Use ON_ERROR_STOP=0 to continue on errors (like duplicate keys)
psql -v ON_ERROR_STOP=0 --username "$POSTGRES_USER" --dbname "ecommerce_small" <<'EOSQL'
-- Load schema
\i /docker-entrypoint-initdb.d/small/01_schema.sql

-- Load data
\i /docker-entrypoint-initdb.d/small/02_data_customers.sql
\i /docker-entrypoint-initdb.d/small/03_data_products.sql
\i /docker-entrypoint-initdb.d/small/04_data_orders.sql
\i /docker-entrypoint-initdb.d/small/05_data_reviews.sql
EOSQL

echo "✓ ecommerce_small initialized"
