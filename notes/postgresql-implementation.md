# PostgreSQL Implementation Summary

## Overview
The application now supports both SQLite and PostgreSQL databases, with environment-based configuration to switch between them.

## What Was Implemented

### 1. Environment Variables (env/.env)
Added the following configuration variables:

```bash
# Database Configuration
ACTIVE_ENV=local                    # Environment: local, production, staging, test
USE_SQLITE=True                     # Set to False to use PostgreSQL

# PostgreSQL Configuration
PG_CONNECTION_URL_INTERNAL=postgresql://...  # For production/staging/test
PG_CONNECTION_URL_EXTERNAL=postgresql://...  # For local/other environments
PG_INIT_MIGRATE_SQLITE=False       # Set to True to migrate SQLite data to PostgreSQL
```

**Connection Logic:**
- If `USE_SQLITE=True` (case-insensitive), use SQLite
- If `USE_SQLITE=False` or unset, use PostgreSQL
- If `ACTIVE_ENV` is not set, defaults to `production`
- `production`, `staging`, `test` → use `PG_CONNECTION_URL_INTERNAL`
- All other environments → use `PG_CONNECTION_URL_EXTERNAL`

### 2. New Module: lib/db_connection.py
Created a database connection abstraction layer that:
- Detects which database to use based on environment variables
- Provides unified connection functions for both SQLite and PostgreSQL
- Handles environment-based PostgreSQL URL selection
- Checks migration flags

Key functions:
- `get_database_type()` - Returns "sqlite" or "postgresql"
- `get_connection(db_path)` - Returns appropriate database connection
- `should_use_sqlite()` - Checks USE_SQLITE environment variable
- `get_active_env()` - Returns active environment (defaults to "production")
- `should_migrate_from_sqlite()` - Checks PG_INIT_MIGRATE_SQLITE flag

### 3. Updated lib/database.py
Modified all database operations to work with both SQLite and PostgreSQL:

**New Functions:**
- `is_database_initialized(db_path)` - Checks if database is initialized (looks for db_metadata.last_updated)
- `drop_all_tables(db_path)` - Drops all tables (used for PostgreSQL sync and cleanup)
- `migrate_sqlite_to_postgresql(sqlite_db_path)` - Migrates data from SQLite to PostgreSQL

**Modified Functions:**
- `create_database()` - Works with both databases (compatible schema)
- `populate_database()` - Uses connection abstraction, works with both databases
- `update_database()` - Different strategies for SQLite (backup/restore) vs PostgreSQL (drop/recreate)
- `get_last_updated()` - Works with both databases
- `backup_database()` - Only applies to SQLite
- `restore_database()` - Only applies to SQLite

**PostgreSQL-specific behaviors:**
- No backup/restore (uses drop/recreate strategy)
- If initialization fails, tables are dropped before retry
- Uses `DROP TABLE CASCADE` for PostgreSQL
- Uses `INSERT ... ON CONFLICT` instead of `INSERT OR IGNORE`
- Uses `lastval()` instead of `lastrowid` for getting last inserted ID

### 4. Updated app/database.py
Modified app query functions to work with both databases:
- `database_exists()` - Now checks initialization status for both databases
- `get_last_updated()` - Works with both databases
- `get_weekly_alcohol_data()` - Uses correct SQL placeholders (? for SQLite, %s for PostgreSQL)

### 5. Added PostgreSQL Dependency
Added `psycopg2-binary>=2.9.10` to pyproject.toml dependencies.

### 6. Updated .env.example
Added comprehensive documentation and placeholder values for all new environment variables.

## How to Use

### Use SQLite (Default)
```bash
# In env/.env
USE_SQLITE=True
```

Then run commands as usual:
```bash
make init     # Initialize database
make update   # Sync database
make run      # Start app
```

### Use PostgreSQL
```bash
# In env/.env
USE_SQLITE=False
ACTIVE_ENV=local  # or production, staging, test
```

Then run commands as usual:
```bash
make init     # Initialize PostgreSQL database
make update   # Sync PostgreSQL database
make run      # Start app with PostgreSQL
```

### Migrate SQLite Data to PostgreSQL
```bash
# In env/.env
USE_SQLITE=False
PG_INIT_MIGRATE_SQLITE=True
```

Then run:
```bash
make init     # Will migrate existing SQLite data to PostgreSQL
```

After migration, set `PG_INIT_MIGRATE_SQLITE=False` to prevent re-migration on subsequent syncs.

### Deploy to Render.com
1. In Render.com dashboard, add environment variables:
   ```
   USE_SQLITE=False
   ACTIVE_ENV=production
   PG_CONNECTION_URL_INTERNAL=<your_internal_url>
   PG_CONNECTION_URL_EXTERNAL=<your_external_url>
   ```

2. Deploy the app - it will automatically use PostgreSQL

3. Initialize the database:
   - Option A: Use the app's "Initialize Database" button
   - Option B: Run `health-data init` via Render shell
   - Option C: Set `PG_INIT_MIGRATE_SQLITE=True` to migrate from existing SQLite data

## Testing

PostgreSQL connection and schema creation have been tested successfully:
- ✓ Connection to Render.com PostgreSQL database
- ✓ Schema creation (all 4 tables + indexes)
- ✓ Database initialization check logic
- ✓ Environment variable detection

## Key Differences: SQLite vs PostgreSQL

### SQLite
- Uses file-based database (db.db)
- Backup/restore strategy during sync
- Uses `INTEGER PRIMARY KEY AUTOINCREMENT`
- Uses `INSERT OR IGNORE`
- Uses `cursor.lastrowid`

### PostgreSQL
- Uses remote database server
- Drop/recreate strategy during sync (no backups)
- Uses `SERIAL PRIMARY KEY`
- Uses `INSERT ... ON CONFLICT DO NOTHING`
- Uses `SELECT lastval()`

## Files Modified
- `pyproject.toml` - Added psycopg2-binary dependency
- `env/.env` - Added PostgreSQL credentials and configuration
- `env/.env.example` - Added PostgreSQL placeholders
- `lib/db_connection.py` - NEW: Database connection abstraction
- `lib/database.py` - Updated all functions for dual database support
- `app/database.py` - Updated query functions for dual database support

## Next Steps
The implementation is complete and tested. You can now:
1. Deploy to Render.com with PostgreSQL
2. Use SQLite for local development
3. Migrate between databases as needed
