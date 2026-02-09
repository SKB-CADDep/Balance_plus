#!/bin/bash
set -e
echo "Restoring dump into $POSTGRES_DB ..."
pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v --clean --if-exists --no-owner --no-privileges /docker-entrypoint-initdb.d/init.dump
echo "Restore finished."