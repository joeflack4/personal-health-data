# MVP Phase 2: Library (Data Processing)

## Overview
This phase implements the data processing library that fetches Google Sheets data, parses it, validates it, and transforms it into a SQLite database optimized for the Dash application.

## Task List

### Phase 2.1: Project Structure & Configuration

- [x] Create library module structure
  - [x] Create `lib/__init__.py`
  - [x] Create `lib/cli.py` for Click CLI commands
  - [x] Create `lib/config.py` for configuration loading
  - [x] Create `lib/fetcher.py` for Google Sheets data fetching
  - [x] Create `lib/parser.py` for raw data parsing
  - [x] Create `lib/validator.py` for data validation logic
  - [x] Create `lib/transformer.py` for data transformations
  - [x] Create `lib/database.py` for SQLite database operations
  - [x] Create `lib/models.py` for data models/types

- [x] Implement configuration loader
  - [x] Load values from `config.yaml`
  - [x] Load values from `env/.env` as fallback
  - [x] Create Config class/dataclass with type hints
  - [x] For SHEET_ID: check config.yaml first, then env/.env
  - [x] Required config values: sheet-id, next-day-cutoff-HH-mm-ss (08:00:00), db-path (db.db), timezone (America/New_York), week-start-day (Monday)
  - [x] Handle missing required configuration gracefully

### Phase 2.2: Data Fetching

- [x] Implement Google Sheets fetcher
  - [x] Create function to construct sheet export URL from SHEET_ID
  - [x] Implement HTTP request with proper error handling
  - [x] Handle network errors and timeouts
  - [x] Return raw CSV data as string or pandas DataFrame
  - [x] Add retry logic for transient failures
  - [x] Log fetch attempts and results
  
### Phase 2.3: Data Parsing

- [x] Implement raw data parser
  - [x] Parse CSV into pandas DataFrame
  - [x] Extract and normalize column names (uses original column names directly)
  - [x] Map columns to standardized names (handled in parsing logic)

- [x] Parse datetime fields
  - [x] Parse `Timestamp` column (format: "1/30/2021 1:36:16")
  - [x] Parse `Retro: Time` (format: "1:00:00 AM")
  - [x] Parse `Retro: Date` (format: "1/31/2021")
  - [x] Combine retro date and time into single datetime
  - [x] Handle malformed dates gracefully

- [x] Determine effective date for events
  - [x] For "now" events: use timestamp
  - [x] For "retro" events: use combined retro datetime
  - [x] Apply next-day cutoff logic from config:
    - If event time is between 00:00:00 and cutoff time (e.g., 08:00:00)
    - Then assign to previous day
  - [x] Store both actual datetime and effective date

### Phase 2.4: Data Validation

- [x] Implement validation for timespan events
  - [x] Check that Start/Stop events are properly paired
  - [x] Validate that Stop comes after Start
  - [x] Validate that timespan is <= 24 hours
  - [x] Flag unpaired Start events (no matching Stop)
  - [x] Flag Stop events with no preceding Start
  - [x] Generate validation error objects with details

- [x] Implement validation for event types
  - [x] Validate that start_stop field only populated when expected
  - [x] Check for null/missing critical fields
  - [x] Validate event names are non-empty

- [x] Create error reporting
  - [x] Create ErrorRecord dataclass/model
  - [x] Track row number, error type, error message
  - [x] Collect all errors during validation pass
  - [x] Return list of errors from validation function

### Phase 2.5: Alcohol Use Data Transformation

- [x] Implement alcohol event parser
  - [x] Filter rows where event is "飲み物" (drink)
  - [x] Default to 1 drink per event
  - [x] Parse Comments field for drink quantity overrides
  - [x] Use regex to extract numeric values: `^(\d*\.?\d+)`
  - [x] Handle formats: "1.5", ".5", "0.5"
  - [x] Ignore any text after the number

- [x] Create alcohol consumption data structure
  - [x] Extract: effective_date, drink_count, comments
  - [x] Handle case where drink count parse fails (default to 1)
  - [x] Associate with original row for debugging

- [x] Aggregate alcohol data by week
  - [x] Group by week starting on Monday (use pandas week grouping with Monday as start)
  - [x] Sum drink counts per week
  - [x] Calculate week start date (Monday) and end date (Sunday)
  - [x] Apply EST timezone for date calculations
  - [x] Store in weekly aggregation table

### Phase 2.6: Database Schema Design

- [x] Design raw events table
  ```sql
  CREATE TABLE raw_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT CHECK(event_type IN ('now', 'retro')),
    event_name TEXT NOT NULL,
    start_stop TEXT CHECK(start_stop IN ('Start', 'Stop', NULL)),
    actual_datetime TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    comments TEXT,
    is_valid BOOLEAN NOT NULL DEFAULT 1,
    validation_errors TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  );
  ```

- [x] Design alcohol events table
  ```sql
  CREATE TABLE alcohol_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_event_id INTEGER NOT NULL,
    effective_date TEXT NOT NULL,
    drink_count REAL NOT NULL,
    comments TEXT,
    FOREIGN KEY (raw_event_id) REFERENCES raw_events (id)
  );
  ```

- [x] Design weekly alcohol aggregation table
  ```sql
  CREATE TABLE alcohol_weekly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start_date TEXT NOT NULL UNIQUE,
    week_end_date TEXT NOT NULL,
    total_drinks REAL NOT NULL,
    event_count INTEGER NOT NULL
  );
  ```

- [x] Design metadata table
  ```sql
  CREATE TABLE db_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  );
  ```
  - [x] Store 'last_updated' key with datetime

### Phase 2.7: Database Operations

- [x] Implement database initialization
  - [x] Create database file at path: db.db
  - [x] Create all tables if they don't exist
  - [x] Set up indexes on date columns
  - [x] Initialize metadata table with null last_updated (indicates DB created but not yet populated)
  - [x] Return success/failure status

- [x] Implement database backup
  - [x] Create backup with timestamp: `{db_name}.{timestamp}.backup`
  - [x] Use shutil.copy2 to preserve metadata
  - [x] Clean up old backups (keep last 5)
  - [x] Return backup file path

- [x] Implement database restore
  - [x] Verify backup file exists
  - [x] Delete current database
  - [x] Copy backup to database path
  - [x] Verify restored database integrity

- [x] Implement database update
  - [x] Create backup before update
  - [x] Create temporary new database
  - [x] Fetch latest data from Google Sheets
  - [x] Parse and validate data
  - [x] Transform and insert into temporary database
  - [x] If successful: replace old database with new
  - [x] If failed: restore from backup
  - [x] Update metadata with timestamp
  - [x] Return (success, error_list)

### Phase 2.8: CLI Implementation

- [x] Create Click CLI group
  - [x] Set up main CLI group with `@click.group()`
  - [x] Add help text and documentation

- [x] Implement `init` command
  - [x] Create database if it doesn't exist
  - [x] Initialize schema
  - [x] Initialize metadata
  - [x] Output success message

- [x] Implement `update` command
  - [x] Call update function
  - [x] Display progress indicators
  - [x] Print any validation errors
  - [x] Print success message with timestamp
  - [x] Exit with appropriate status code

- [x] Implement `status` command
  - [x] Check if database exists
  - [x] Display last_updated from metadata
  - [x] Display row counts from tables
  - [x] Display database file size

- [x] Add global options
  - [x] Add `--db-path` option to override database location
  - [x] Add `--verbose` flag for detailed logging
  - [x] Add `--config` option to override config file path

- [x] Configure entry point in `pyproject.toml`
  ```toml
  [project.scripts]
  health-data = "lib.cli:main"
  ```

### Phase 2.9: Error Handling & Logging

- [x] Set up logging
  - [x] Configure logging to console
  - [x] Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
  - [x] Log all major operations (fetch, parse, validate, transform)

- [x] Implement comprehensive error handling
  - [x] Catch and log network errors during fetch
  - [x] Catch and log parsing errors
  - [x] Catch and log database errors
  - [x] Provide user-friendly error messages
  - [x] Include suggestions for fixing common errors

### Phase 2.10: Testing & Documentation

- [x] Create library documentation
  - [x] Document each module's purpose
  - [x] Add docstrings to all public functions
  - [x] Document data models and schemas

## Completion Criteria
- All library modules are implemented and tested
- CLI commands work correctly and provide helpful output
- Data fetching, parsing, and validation are robust
- Alcohol use data is correctly extracted and aggregated
- Database schema supports app requirements
- Update process safely handles errors with backup/restore
- Test coverage is comprehensive
- Code is documented and maintainable
