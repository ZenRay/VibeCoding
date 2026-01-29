#!/bin/bash
set -e

echo "Creating test databases..."

# Create three databases
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
    CREATE DATABASE ecommerce_small;
    CREATE DATABASE social_medium;
    CREATE DATABASE erp_large;
EOSQL

echo "✓ Databases created: ecommerce_small, social_medium, erp_large"
