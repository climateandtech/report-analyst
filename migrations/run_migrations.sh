#!/bin/bash
# Script to run database migrations on Heroku or other deployments

set -e

echo "Running database migrations..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable is not set"
    exit 1
fi

# Check if USE_ALEMBIC_MIGRATIONS is enabled
if [ "$USE_ALEMBIC_MIGRATIONS" != "true" ]; then
    echo "Warning: USE_ALEMBIC_MIGRATIONS is not set to 'true'. Skipping migrations."
    echo "Set USE_ALEMBIC_MIGRATIONS=true to enable Alembic migrations."
    exit 0
fi

# Run migrations
python -m alembic upgrade head

if [ $? -eq 0 ]; then
    echo "Migrations completed successfully"
else
    echo "Error: Migrations failed"
    exit 1
fi


