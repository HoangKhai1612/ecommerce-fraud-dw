#!/bin/sh
# Idempotent initialization for the docker-local PostgreSQL instance.
# Runs ONLY when the data directory is empty (first initialization).
# The authoritative Data Warehouse runs on the Windows PostgreSQL 18 server.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE SCHEMA IF NOT EXISTS raw;
    CREATE SCHEMA IF NOT EXISTS staging;
    CREATE SCHEMA IF NOT EXISTS marts;
EOSQL

if [ -n "${POSTGRES_RO_USER}" ]; then
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        DO \$\$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${POSTGRES_RO_USER}') THEN
                CREATE ROLE ${POSTGRES_RO_USER} LOGIN PASSWORD '${POSTGRES_RO_PASSWORD}';
            END IF;
        END
        \$\$;
        GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_RO_USER};
        GRANT USAGE ON SCHEMA raw, staging, marts TO ${POSTGRES_RO_USER};
        GRANT SELECT ON ALL TABLES IN SCHEMA raw, staging, marts TO ${POSTGRES_RO_USER};
EOSQL
fi
