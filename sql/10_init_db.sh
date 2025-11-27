#!/bin/bash

# This is a shell option in bash (and many POSIX shells) that makes the script exit immediately if any command returns a non-zero exit status.
set -e

# Create 'open-cp' database and open-cp user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE ROLE "$OPENCP_USER" NOSUPERUSER CREATEDB CREATEROLE LOGIN PASSWORD '$OPENCP_PASSWORD';
    CREATE DATABASE "$OPENCP_DB" OWNER "$OPENCP_USER" ENCODING 'utf-8';
    CREATE SCHEMA "$OPENCP_SCHEMA";
EOSQL

# Create Keycloak user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE ROLE "$KEYCLOAK_USER" NOSUPERUSER CREATEDB CREATEROLE LOGIN PASSWORD '$KEYCLOAK_PASSWORD';
EOSQL

# Connect to the newly created database and create the schema
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" "$KEYCLOAK_DB" <<-EOSQL
    CREATE SCHEMA "$KEYCLOAK_SCHEMA";
EOSQL

# Assign privileges on the keycloak schema to the Keycloak user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" "$KEYCLOAK_DB" <<-EOSQL
    GRANT ALL PRIVILEGES ON SCHEMA "$KEYCLOAK_SCHEMA" TO "$KEYCLOAK_USER";
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA "$KEYCLOAK_SCHEMA" TO "$KEYCLOAK_USER";
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA "$KEYCLOAK_SCHEMA" TO "$KEYCLOAK_USER";
EOSQL

# Grant read-only privileges to open-cp user for keycloak schema
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" "$KEYCLOAK_DB" <<-EOSQL
    GRANT USAGE ON SCHEMA "$KEYCLOAK_SCHEMA" TO "$OPENCP_USER";
    GRANT SELECT ON ALL TABLES IN SCHEMA "$KEYCLOAK_SCHEMA" TO "$OPENCP_USER";
    ALTER DEFAULT PRIVILEGES IN SCHEMA "$KEYCLOAK_SCHEMA" GRANT SELECT ON TABLES TO "$OPENCP_USER";
EOSQL

# Apply schema
echo "Applying schema from 20_schema.sql..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$OPENCP_DB" -f "/sql/20_schema.sql"
echo "Schema applied successfully."

# Apply seed data (admin user)
echo "Applying seed data from 30_seed.sql..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$OPENCP_DB" -f "/sql/30_seed.sql"
echo "Seed data applied successfully."