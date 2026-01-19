"""Database query functions for the app."""

import logging
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

from lib.db_connection import get_connection, get_database_type
from lib.database import is_database_initialized

logger = logging.getLogger(__name__)


def database_exists(db_path: Optional[str] = None) -> bool:
    """
    Check if database exists and is initialized.

    For SQLite: checks if file exists.
    For PostgreSQL: checks if tables exist.

    Args:
        db_path: Path to SQLite database file (ignored for PostgreSQL)

    Returns:
        True if database exists and is initialized
    """
    return is_database_initialized(db_path)


def get_last_updated(db_path: Optional[str] = None) -> Optional[str]:
    """
    Get last_updated timestamp from database.

    Works with both SQLite and PostgreSQL.

    Args:
        db_path: Path to SQLite database file (ignored for PostgreSQL)

    Returns:
        ISO format datetime string, or None if not set or database doesn't exist
    """
    if not database_exists(db_path):
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


def get_weekly_alcohol_data(
    db_path: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Query weekly alcohol consumption data.

    Works with both SQLite and PostgreSQL.

    Args:
        db_path: Path to SQLite database file (ignored for PostgreSQL)
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)

    Returns:
        DataFrame with weekly data
    """
    empty_df = pd.DataFrame(columns=['week_start_date', 'week_end_date', 'total_drinks', 'event_count'])

    if not database_exists(db_path):
        return empty_df

    try:
        db_type = get_database_type()
        conn = get_connection(db_path)

        # Build query with appropriate placeholder
        placeholder = "?" if db_type == "sqlite" else "%s"

        query = "SELECT week_start_date, week_end_date, total_drinks, event_count FROM alcohol_weekly"
        conditions = []
        params = []

        if start_date:
            conditions.append(f"week_start_date >= {placeholder}")
            params.append(start_date)

        if end_date:
            conditions.append(f"week_start_date <= {placeholder}")
            params.append(end_date)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY week_start_date"

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        return df

    except Exception as e:
        logger.error(f"Error querying weekly data: {e}")
        return empty_df
