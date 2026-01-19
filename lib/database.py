"""Database operations for SQLite and PostgreSQL."""

import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from lib.config import load_config
from lib.db_connection import (
    get_connection,
    get_database_type,
    should_migrate_from_sqlite,
)
from lib.fetcher import fetch_sheet_data
from lib.models import AlcoholEvent, ErrorRecord, RawEvent
from lib.parser import parse_sheet_data
from lib.transformer import aggregate_by_week, extract_alcohol_events
from lib.validator import validate_events

logger = logging.getLogger(__name__)


def _get_placeholder(db_type: str) -> str:
    """Get the appropriate SQL placeholder for the database type."""
    return "?" if db_type == "sqlite" else "%s"


def _execute_with_params(cursor, query: str, params: tuple, db_type: str):
    """Execute a parameterized query with the correct placeholder syntax."""
    if db_type == "postgresql":
        # Replace ? with %s for PostgreSQL
        query = query.replace("?", "%s")
    cursor.execute(query, params)


def is_database_initialized(db_path: Optional[str] = None) -> bool:
    """
    Check if the database has been initialized.

    For SQLite: checks if the database file exists and has db_metadata with last_updated.
    For PostgreSQL: checks if db_metadata table exists and has last_updated value.

    Args:
        db_path: Path to SQLite database file (ignored for PostgreSQL)

    Returns:
        True if database is initialized, False otherwise
    """
    db_type = get_database_type()

    try:
        if db_type == "sqlite":
            if not db_path:
                return False

            db_file = Path(db_path)
            if not db_file.exists():
                return False

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check if db_metadata table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='db_metadata'"
            )
            if not cursor.fetchone():
                conn.close()
                return False

            # Check if last_updated exists and is not null
            cursor.execute("SELECT value FROM db_metadata WHERE key = 'last_updated'")
            result = cursor.fetchone()
            conn.close()

            return result is not None and result[0] is not None

        else:  # postgresql
            import psycopg2

            conn = get_connection(db_path)
            cursor = conn.cursor()

            # Check if db_metadata table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'db_metadata'
                )
            """)
            table_exists = cursor.fetchone()[0]

            if not table_exists:
                conn.close()
                return False

            # Check if last_updated exists and is not null
            cursor.execute("SELECT value FROM db_metadata WHERE key = 'last_updated'")
            result = cursor.fetchone()
            conn.close()

            return result is not None and result[0] is not None

    except Exception as e:
        logger.error(f"Error checking database initialization: {e}")
        return False


def drop_all_tables(db_path: Optional[str] = None) -> None:
    """
    Drop all tables in the database.

    Used for PostgreSQL sync operations and for cleaning up failed initializations.

    Args:
        db_path: Path to SQLite database file (ignored for PostgreSQL)
    """
    db_type = get_database_type()
    conn = get_connection(db_path)
    cursor = conn.cursor()

    tables = ["alcohol_weekly", "alcohol_events", "raw_events", "db_metadata"]

    try:
        for table in tables:
            if db_type == "postgresql":
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            else:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")

        conn.commit()
        logger.info(f"Dropped all tables from {db_type} database")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error dropping tables: {e}")
        raise
    finally:
        conn.close()


def create_database(db_path: Optional[str] = None) -> None:
    """
    Create database with all required tables.

    Works with both SQLite and PostgreSQL using compatible schema.

    Args:
        db_path: Path to SQLite database file (ignored for PostgreSQL)
    """
    db_type = get_database_type()
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Determine the correct PRIMARY KEY syntax
    if db_type == "postgresql":
        pk_syntax = "SERIAL PRIMARY KEY"
        bool_default = "TRUE"
    else:
        pk_syntax = "INTEGER PRIMARY KEY AUTOINCREMENT"
        bool_default = "1"

    try:
        # Raw events table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS raw_events (
                id {pk_syntax},
                timestamp TEXT NOT NULL,
                event_type TEXT CHECK(event_type IN ('now', 'retro')),
                event_name TEXT NOT NULL,
                start_stop TEXT CHECK(start_stop IN ('Start', 'Stop', NULL)),
                actual_datetime TEXT NOT NULL,
                effective_date TEXT NOT NULL,
                comments TEXT,
                is_valid BOOLEAN NOT NULL DEFAULT {bool_default},
                validation_errors TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Alcohol events table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS alcohol_events (
                id {pk_syntax},
                raw_event_id INTEGER NOT NULL,
                effective_date TEXT NOT NULL,
                drink_count REAL NOT NULL,
                comments TEXT,
                FOREIGN KEY (raw_event_id) REFERENCES raw_events (id)
            )
        """)

        # Weekly alcohol aggregation table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS alcohol_weekly (
                id {pk_syntax},
                week_start_date TEXT NOT NULL UNIQUE,
                week_end_date TEXT NOT NULL,
                total_drinks REAL NOT NULL,
                event_count INTEGER NOT NULL
            )
        """)

        # Metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS db_metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_raw_events_date ON raw_events(effective_date)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_alcohol_events_date ON alcohol_events(effective_date)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_alcohol_weekly_date ON alcohol_weekly(week_start_date)"
        )

        # Initialize metadata with null last_updated
        if db_type == "postgresql":
            cursor.execute("""
                INSERT INTO db_metadata (key, value, updated_at)
                VALUES ('last_updated', NULL, CURRENT_TIMESTAMP)
                ON CONFLICT (key) DO NOTHING
            """)
        else:
            cursor.execute("""
                INSERT OR IGNORE INTO db_metadata (key, value, updated_at)
                VALUES ('last_updated', NULL, CURRENT_TIMESTAMP)
            """)

        conn.commit()
        logger.info(f"Database created ({db_type})")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating database: {e}")
        raise
    finally:
        conn.close()


def backup_database(db_path: str) -> Optional[str]:
    """
    Create a timestamped backup of the SQLite database.

    Only applicable to SQLite. PostgreSQL uses drop/recreate strategy.

    Args:
        db_path: Path to database file

    Returns:
        Path to backup file, or None if database doesn't exist or not using SQLite
    """
    db_type = get_database_type()
    if db_type != "sqlite":
        logger.info("Backups not applicable for PostgreSQL")
        return None

    db_file = Path(db_path)
    if not db_file.exists():
        logger.warning(f"Database {db_path} does not exist, skipping backup")
        return None

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.{timestamp}.backup"

    shutil.copy2(db_path, backup_path)
    logger.info(f"Database backed up to {backup_path}")

    return backup_path


def delete_all_backups(db_path: str) -> None:
    """
    Delete all backup files for the SQLite database.

    Only applicable to SQLite.

    Args:
        db_path: Path to database file
    """
    db_type = get_database_type()
    if db_type != "sqlite":
        return

    db_file = Path(db_path)
    backup_dir = db_file.parent
    backups = list(backup_dir.glob(f"{db_file.name}.*.backup"))

    for backup in backups:
        backup.unlink()
        logger.debug(f"Removed backup: {backup}")

    if backups:
        logger.info(f"Deleted {len(backups)} backup file(s)")


def restore_database(db_path: str, backup_path: str) -> None:
    """
    Restore SQLite database from backup.

    Only applicable to SQLite.

    Args:
        db_path: Path to database file
        backup_path: Path to backup file
    """
    db_type = get_database_type()
    if db_type != "sqlite":
        logger.warning("Restore not applicable for PostgreSQL")
        return

    backup_file = Path(backup_path)
    if not backup_file.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    shutil.copy2(backup_path, db_path)
    logger.info(f"Database restored from {backup_path}")


def migrate_sqlite_to_postgresql(sqlite_db_path: str) -> List[ErrorRecord]:
    """
    Migrate data from SQLite database to PostgreSQL.

    Args:
        sqlite_db_path: Path to SQLite database file

    Returns:
        List of error records (empty for migration)
    """
    logger.info(f"Migrating data from SQLite ({sqlite_db_path}) to PostgreSQL...")

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_cursor = sqlite_conn.cursor()

    # Connect to PostgreSQL
    pg_conn = get_connection(None)
    pg_cursor = pg_conn.cursor()

    try:
        # Migrate raw_events
        logger.info("Migrating raw_events...")
        sqlite_cursor.execute("SELECT * FROM raw_events ORDER BY id")
        rows = sqlite_cursor.fetchall()

        for row in rows:
            pg_cursor.execute("""
                INSERT INTO raw_events (
                    timestamp, event_type, event_name, start_stop,
                    actual_datetime, effective_date, comments,
                    is_valid, validation_errors, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, row[1:])  # Skip the id column

        # Migrate alcohol_events
        logger.info("Migrating alcohol_events...")
        sqlite_cursor.execute("SELECT * FROM alcohol_events ORDER BY id")
        rows = sqlite_cursor.fetchall()

        for row in rows:
            pg_cursor.execute("""
                INSERT INTO alcohol_events (
                    raw_event_id, effective_date, drink_count, comments
                ) VALUES (%s, %s, %s, %s)
            """, row[1:])  # Skip the id column

        # Migrate alcohol_weekly
        logger.info("Migrating alcohol_weekly...")
        sqlite_cursor.execute("SELECT * FROM alcohol_weekly ORDER BY id")
        rows = sqlite_cursor.fetchall()

        for row in rows:
            pg_cursor.execute("""
                INSERT INTO alcohol_weekly (
                    week_start_date, week_end_date, total_drinks, event_count
                ) VALUES (%s, %s, %s, %s)
            """, row[1:])  # Skip the id column

        # Migrate db_metadata
        logger.info("Migrating db_metadata...")
        sqlite_cursor.execute("SELECT * FROM db_metadata")
        rows = sqlite_cursor.fetchall()

        for row in rows:
            pg_cursor.execute("""
                INSERT INTO db_metadata (key, value, updated_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at
            """, row)

        pg_conn.commit()
        logger.info("Migration completed successfully")

    except Exception as e:
        pg_conn.rollback()
        logger.error(f"Error during migration: {e}")
        raise
    finally:
        sqlite_conn.close()
        pg_conn.close()

    return []


def populate_database(db_path: Optional[str] = None, config_path: Optional[str] = None) -> List[ErrorRecord]:
    """
    Fetch data from Google Sheets and populate database.

    Works with both SQLite and PostgreSQL.

    Args:
        db_path: Path to SQLite database file (ignored for PostgreSQL)
        config_path: Optional path to config file

    Returns:
        List of error records from validation
    """
    db_type = get_database_type()

    # Load config
    config = load_config(config_path)

    # Fetch data
    logger.info("Fetching data from Google Sheets...")
    df = fetch_sheet_data(config.sheet_id)

    # Parse data
    logger.info("Parsing data...")
    events = parse_sheet_data(df, config)

    # Validate data
    logger.info("Validating data...")
    validated_events, errors = validate_events(events)

    # Transform data
    logger.info("Transforming data...")
    alcohol_events = extract_alcohol_events(validated_events)
    weekly_data = aggregate_by_week(alcohol_events, config.week_start_day)

    # Insert into database
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        logger.info("Inserting raw events...")
        for event in validated_events:
            query = """
                INSERT INTO raw_events (
                    timestamp, event_type, event_name, start_stop,
                    actual_datetime, effective_date, comments,
                    is_valid, validation_errors
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                event.timestamp.isoformat() if event.timestamp else None,
                event.event_type,
                event.event_name,
                event.start_stop,
                event.actual_datetime.isoformat(),
                event.effective_date,
                event.comments,
                event.is_valid,
                event.validation_errors,
            )
            _execute_with_params(cursor, query, params, db_type)

        logger.info("Inserting alcohol events...")
        # Map effective_date to raw_event_id for alcohol events
        for event in validated_events:
            if event.event_name == "飲み物":
                # Get the last inserted row ID
                if db_type == "postgresql":
                    cursor.execute("SELECT lastval()")
                    raw_event_id = cursor.fetchone()[0]
                else:
                    raw_event_id = cursor.lastrowid

                # Find matching alcohol event
                for alc_event in alcohol_events:
                    if alc_event.effective_date == event.effective_date:
                        query = """
                            INSERT INTO alcohol_events (
                                raw_event_id, effective_date, drink_count, comments
                            ) VALUES (?, ?, ?, ?)
                        """
                        params = (
                            raw_event_id,
                            alc_event.effective_date,
                            alc_event.drink_count,
                            alc_event.comments,
                        )
                        _execute_with_params(cursor, query, params, db_type)
                        break

        logger.info("Inserting weekly aggregations...")
        for _, row in weekly_data.iterrows():
            query = """
                INSERT INTO alcohol_weekly (
                    week_start_date, week_end_date, total_drinks, event_count
                ) VALUES (?, ?, ?, ?)
            """
            params = (
                row['week_start_date'],
                row['week_end_date'],
                row['total_drinks'],
                row['event_count'],
            )
            _execute_with_params(cursor, query, params, db_type)

        # Update last_updated timestamp
        now = datetime.now().isoformat()
        query = """
            UPDATE db_metadata SET value = ?, updated_at = CURRENT_TIMESTAMP
            WHERE key = 'last_updated'
        """
        _execute_with_params(cursor, query, (now,), db_type)

        conn.commit()
        logger.info(f"Database populated successfully. {len(errors)} validation errors found.")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error populating database: {e}")
        raise
    finally:
        conn.close()

    return errors


def update_database(db_path: Optional[str] = None, config_path: Optional[str] = None) -> Tuple[bool, List[ErrorRecord]]:
    """
    Update database with latest data from Google Sheets.

    For SQLite: Creates temporary backup before update, populates new database.
    On success: deletes all backups. On failure: restores from backup.

    For PostgreSQL: Drops all tables and recreates them. On failure: tables remain dropped.

    Args:
        db_path: Path to SQLite database file (ignored for PostgreSQL)
        config_path: Optional path to config file

    Returns:
        Tuple of (success, error_list)
    """
    db_type = get_database_type()

    if db_type == "sqlite":
        # SQLite: use backup/restore strategy
        backup_path = None
        try:
            # Create backup if database exists
            backup_path = backup_database(db_path)

            # Create fresh database
            db_file = Path(db_path)
            if db_file.exists():
                db_file.unlink()

            create_database(db_path)

            # Check if we should migrate from SQLite
            if should_migrate_from_sqlite():
                logger.warning("PG_INIT_MIGRATE_SQLITE is set but we're using SQLite. Ignoring.")

            # Populate database
            errors = populate_database(db_path, config_path)

            # Success - delete all backups
            delete_all_backups(db_path)
            logger.info("Update successful, deleted temporary backups")

            return True, errors

        except Exception as e:
            logger.error(f"Error updating database: {e}")

            # Clean up failed database
            db_file = Path(db_path)
            if db_file.exists():
                try:
                    db_file.unlink()
                    logger.info("Removed failed database")
                except Exception as cleanup_error:
                    logger.error(f"Failed to remove failed database: {cleanup_error}")

            # Restore from backup if it exists
            if backup_path:
                try:
                    restore_database(db_path, backup_path)
                    logger.info("Database restored from backup after error")
                    delete_all_backups(db_path)
                    logger.info("Deleted temporary backups after restore")
                except Exception as restore_error:
                    logger.error(f"Failed to restore database: {restore_error}")

            return False, []

    else:
        # PostgreSQL: drop and recreate strategy
        try:
            # Check if initialized
            initialized = is_database_initialized(db_path)

            if initialized:
                # Drop all existing tables
                logger.info("Dropping existing PostgreSQL tables...")
                drop_all_tables(db_path)

            # Create fresh tables
            create_database(db_path)

            # Check if we should migrate from SQLite
            if should_migrate_from_sqlite():
                logger.info("PG_INIT_MIGRATE_SQLITE is set, migrating from SQLite...")
                sqlite_db_path = load_config(config_path).db_path
                errors = migrate_sqlite_to_postgresql(sqlite_db_path)
            else:
                # Populate database from Google Sheets
                errors = populate_database(db_path, config_path)

            logger.info("PostgreSQL update successful")
            return True, errors

        except Exception as e:
            logger.error(f"Error updating PostgreSQL database: {e}")
            logger.warning("PostgreSQL tables may be in an inconsistent state")
            return False, []


def get_last_updated(db_path: Optional[str] = None) -> Optional[str]:
    """
    Get the last_updated timestamp from database metadata.

    Works with both SQLite and PostgreSQL.

    Args:
        db_path: Path to SQLite database file (ignored for PostgreSQL)

    Returns:
        ISO format datetime string, or None if not set or database doesn't exist
    """
    db_type = get_database_type()

    if db_type == "sqlite":
        if not db_path:
            return None

        db_file = Path(db_path)
        if not db_file.exists():
            return None

    try:
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM db_metadata WHERE key = 'last_updated'")
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            return result[0]
        return None
    except Exception as e:
        logger.error(f"Error getting last_updated: {e}")
        return None
