#!/bin/sh
set -e

echo "=== Latium AI Backend Prestart ==="
echo "Executing pending database migrations via Alembic..."
alembic upgrade head
echo "Database migrations up to date."
