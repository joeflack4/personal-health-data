"""Database operations."""

import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from lib.config import load_config
from lib.fetcher import fetch_sheet_data
from lib.models import AlcoholEvent, ErrorRecord, RawEvent
from lib.parser import parse_sheet_data
from lib.transformer import aggregate_by_week, extract_alcohol_events
from lib.validator import validate_events

logger = logging.getLogger(__name__)


def create_database(db_path: str) -> None:
    """
    Create database with all required tables.

    Args:
        db_path: Path to database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Raw events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_events (
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
        )
    """)

    # Alcohol events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alcohol_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_event_id INTEGER NOT NULL,
            effective_date TEXT NOT NULL,
            drink_count REAL NOT NULL,
            comments TEXT,
            FOREIGN KEY (raw_event_id) REFERENCES raw_events (id)
        )
    """)

    # Weekly alcohol aggregation table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alcohol_weekly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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
    cursor.execute("""
        INSERT OR IGNORE INTO db_metadata (key, value, updated_at)
        VALUES ('last_updated', NULL, CURRENT_TIMESTAMP)
    """)

    conn.commit()
    conn.close()
    logger.info(f"Database created at {db_path}")


def backup_database(db_path: str) -> Optional[str]:
    """
    Create a timestamped backup of the database.

    Args:
        db_path: Path to database file

    Returns:
        Path to backup file, or None if database doesn't exist
    """
    db_file = Path(db_path)
    if not db_file.exists():
        logger.warning(f"Database {db_path} does not exist, skipping backup")
        return None

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.{timestamp}.backup"

    shutil.copy2(db_path, backup_path)
    logger.info(f"Database backed up to {backup_path}")

    # Clean up old backups (keep last 5)
    backup_dir = db_file.parent
    backups = sorted(backup_dir.glob(f"{db_file.name}.*.backup"))
    if len(backups) > 5:
        for old_backup in backups[:-5]:
            old_backup.unlink()
            logger.debug(f"Removed old backup: {old_backup}")

    return backup_path


def restore_database(db_path: str, backup_path: str) -> None:
    """
    Restore database from backup.

    Args:
        db_path: Path to database file
        backup_path: Path to backup file
    """
    backup_file = Path(backup_path)
    if not backup_file.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    shutil.copy2(backup_path, db_path)
    logger.info(f"Database restored from {backup_path}")


def populate_database(db_path: str, config_path: Optional[str] = None) -> List[ErrorRecord]:
    """
    Fetch data from Google Sheets and populate database.

    Args:
        db_path: Path to database file
        config_path: Optional path to config file

    Returns:
        List of error records from validation
    """
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
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    logger.info("Inserting raw events...")
    for event in validated_events:
        cursor.execute(
            """
            INSERT INTO raw_events (
                timestamp, event_type, event_name, start_stop,
                actual_datetime, effective_date, comments,
                is_valid, validation_errors
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                event.timestamp.isoformat() if event.timestamp else None,
                event.event_type,
                event.event_name,
                event.start_stop,
                event.actual_datetime.isoformat(),
                event.effective_date,
                event.comments,
                event.is_valid,
                event.validation_errors,
            ),
        )

    logger.info("Inserting alcohol events...")
    # Map effective_date to raw_event_id for alcohol events
    for event in validated_events:
        if event.event_name == "飲み物":
            raw_event_id = cursor.lastrowid
            # Find matching alcohol event
            for alc_event in alcohol_events:
                if alc_event.effective_date == event.effective_date:
                    cursor.execute(
                        """
                        INSERT INTO alcohol_events (
                            raw_event_id, effective_date, drink_count, comments
                        ) VALUES (?, ?, ?, ?)
                    """,
                        (
                            raw_event_id,
                            alc_event.effective_date,
                            alc_event.drink_count,
                            alc_event.comments,
                        ),
                    )
                    break

    logger.info("Inserting weekly aggregations...")
    for _, row in weekly_data.iterrows():
        cursor.execute(
            """
            INSERT INTO alcohol_weekly (
                week_start_date, week_end_date, total_drinks, event_count
            ) VALUES (?, ?, ?, ?)
        """,
            (
                row['week_start_date'],
                row['week_end_date'],
                row['total_drinks'],
                row['event_count'],
            ),
        )

    # Update last_updated timestamp
    now = datetime.now().isoformat()
    cursor.execute(
        """
        UPDATE db_metadata SET value = ?, updated_at = CURRENT_TIMESTAMP
        WHERE key = 'last_updated'
    """,
        (now,),
    )

    conn.commit()
    conn.close()

    logger.info(f"Database populated successfully. {len(errors)} validation errors found.")
    return errors


def update_database(db_path: str, config_path: Optional[str] = None) -> Tuple[bool, List[ErrorRecord]]:
    """
    Update database with latest data from Google Sheets.

    Creates backup, populates new database, and replaces old one.
    If error occurs, restores from backup.

    Args:
        db_path: Path to database file
        config_path: Optional path to config file

    Returns:
        Tuple of (success, error_list)
    """
    try:
        # Create backup if database exists
        backup_path = backup_database(db_path)

        # Create fresh database
        db_file = Path(db_path)
        if db_file.exists():
            db_file.unlink()

        create_database(db_path)

        # Populate database
        errors = populate_database(db_path, config_path)

        return True, errors

    except Exception as e:
        logger.error(f"Error updating database: {e}")

        # Restore from backup if it exists
        if backup_path:
            try:
                restore_database(db_path, backup_path)
                logger.info("Database restored from backup after error")
            except Exception as restore_error:
                logger.error(f"Failed to restore database: {restore_error}")

        return False, []


def get_last_updated(db_path: str) -> Optional[str]:
    """
    Get the last_updated timestamp from database metadata.

    Args:
        db_path: Path to database file

    Returns:
        ISO format datetime string, or None if not set or database doesn't exist
    """
    db_file = Path(db_path)
    if not db_file.exists():
        return None

    try:
        conn = sqlite3.connect(db_path)
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
