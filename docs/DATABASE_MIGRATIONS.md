# Database Migrations Guide

This guide explains how database migrations work in the Report Analyst application, covering both development and production scenarios.

## Overview

The application uses a **hybrid migration approach**:
- **Development (SQLite)**: Automatic table creation on first connection (simple, fast)
- **Production (PostgreSQL)**: Alembic migrations for version control and rollback capability

## Migration System

### Alembic

We use [Alembic](https://alembic.sqlalchemy.org/) for database migrations in production. Alembic provides:
- Version control for database schema changes
- Rollback capability (`alembic downgrade`)
- Team collaboration (shared migration history)
- Safe production deployments

### Environment Variables

- `DATABASE_URL`: Database connection string (required)
  - SQLite: `sqlite:///path/to/db`
  - PostgreSQL: `postgresql://user:pass@host:port/db`
- `USE_ALEMBIC_MIGRATIONS`: Enable Alembic migrations (default: `false`)
  - Set to `true` for production PostgreSQL deployments
  - Set to `false` for development (uses auto-creation)
- `ALEMBIC_CONFIG`: Path to `alembic.ini` (optional, default: `./alembic.ini`)

## Development Workflow

### SQLite (Default)

When using SQLite (default for development), tables are created automatically:

```python
from report_analyst.core.cache_manager import CacheManager

# Tables are created automatically on first connection
cache_manager = CacheManager()
# No migration needed!
```

**No action required** - just start using the application.

### Local PostgreSQL (Optional)

If you want to test with PostgreSQL locally:

1. **Set up PostgreSQL database:**
   ```bash
   createdb report_analyst
   ```

2. **Set environment variable:**
   ```bash
   export DATABASE_URL="postgresql://user:pass@localhost/report_analyst"
   ```

3. **Choose migration approach:**
   
   **Option A: Auto-creation (development)**
   ```bash
   # Don't set USE_ALEMBIC_MIGRATIONS (or set to false)
   # Tables created automatically
   ```
   
   **Option B: Alembic migrations (production-like)**
   ```bash
   export USE_ALEMBIC_MIGRATIONS=true
   alembic upgrade head
   ```

## Production Workflow

### Heroku Deployment

#### Automatic Migrations (Recommended)

Migrations run automatically on deploy via the `release` phase in `Procfile`:

```procfile
release: python -m alembic upgrade head || echo "Migrations skipped..."
web: streamlit run report_analyst/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
```

**Setup:**
1. Set environment variables on Heroku:
   ```bash
   heroku config:set DATABASE_URL="postgresql://..."
   heroku config:set USE_ALEMBIC_MIGRATIONS=true
   ```

2. Deploy:
   ```bash
   git push heroku main
   # Migrations run automatically before web dyno starts
   ```

#### Manual Migrations

If you prefer to run migrations manually:

```bash
# Run migrations manually
heroku run alembic upgrade head

# Or use the migration script
heroku run bash migrations/run_migrations.sh
```

### Other Deployments

For other platforms (Render, Railway, etc.):

1. **Set environment variables:**
   ```bash
   DATABASE_URL=postgresql://...
   USE_ALEMBIC_MIGRATIONS=true
   ```

2. **Run migrations before starting the app:**
   ```bash
   # In your deployment script or startup command
   python -m alembic upgrade head
   python -m streamlit run report_analyst/streamlit_app.py
   ```

## Migration Commands

### Check Migration Status

```bash
# Check current revision
alembic current

# Check if migrations are needed
python -c "from report_analyst.core.migration_utils import check_migration_status; print(check_migration_status())"
```

### Create New Migration

```bash
# Auto-generate migration from schema changes
alembic revision --autogenerate -m "description_of_changes"

# Review the generated migration file in alembic/versions/
# Edit if needed, then apply:
alembic upgrade head
```

### Apply Migrations

```bash
# Upgrade to latest (head)
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision>

# Upgrade one step
alembic upgrade +1
```

### Rollback Migrations

```bash
# Downgrade one step
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision>

# Downgrade to base (removes all tables - use with caution!)
alembic downgrade base
```

### View Migration History

```bash
# List all migrations
alembic history

# Show current revision
alembic current

# Show detailed history
alembic history --verbose
```

## Migration Files

Migrations are stored in `alembic/versions/`:
- Format: `<revision>_<description>.py`
- Example: `001_initial_schema.py`

### Initial Migration

The initial migration (`001_initial_schema.py`) creates:
- `document_chunks` - Document text chunks with embeddings
- `questions` - Question definitions
- `analysis_cache` - Cached analysis results
- `question_analysis` - Analysis results per question
- `chunk_relevance` - Chunk relevance scores
- `stored_files` - File storage (PostgreSQL only)

## Troubleshooting

### Migration Fails on Heroku

**Problem:** `alembic: command not found`

**Solution:** Ensure `alembic` is in `requirements.txt`:
```bash
pip freeze | grep alembic >> requirements.txt
```

### Tables Already Exist

**Problem:** Migration fails because tables already exist

**Solution:** 
- If using auto-creation, don't set `USE_ALEMBIC_MIGRATIONS=true`
- If using migrations, mark current state as migrated:
  ```bash
  alembic stamp head
  ```

### Migration Out of Sync

**Problem:** Database schema doesn't match migrations

**Solution:**
1. Check current state: `alembic current`
2. Check head: `alembic history`
3. If needed, create a new migration to sync:
   ```bash
   alembic revision --autogenerate -m "sync_schema"
   ```

### Development vs Production Mismatch

**Problem:** Different behavior in dev vs production

**Solution:**
- Development: `USE_ALEMBIC_MIGRATIONS=false` (or unset)
- Production: `USE_ALEMBIC_MIGRATIONS=true`

## Best Practices

1. **Always review auto-generated migrations** before applying
2. **Test migrations locally** before deploying to production
3. **Backup database** before running migrations in production
4. **Use descriptive migration names**: `add_user_table`, `add_index_to_chunks`
5. **Keep migrations small and focused** - one logical change per migration
6. **Never edit applied migrations** - create new ones instead

## Migration Utilities

The `report_analyst.core.migration_utils` module provides helper functions:

```python
from report_analyst.core.migration_utils import (
    check_migration_status,
    get_current_revision,
    get_head_revision,
    needs_migration,
    run_migrations,
)

# Check if migration is needed
if needs_migration():
    print("Database needs migration")
    run_migrations()

# Get detailed status
status = check_migration_status()
print(f"Current: {status['current_revision']}")
print(f"Head: {status['head_revision']}")
print(f"Up to date: {status['is_up_to_date']}")
```

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Migrations Guide](https://docs.sqlalchemy.org/en/20/core/metadata.html)
- [Heroku Release Phase](https://devcenter.heroku.com/articles/release-phase)


