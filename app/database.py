"""Database query functions for the app."""

import logging
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def database_exists(db_path: str) -> bool:
    """Check if database file exists."""
    return Path(db_path).exists()


def get_last_updated(db_path: str) -> Optional[str]:
    """
    Get last_updated timestamp from database.

    Returns:
        ISO format datetime string, or None if not set or database doesn't exist
    """
    if not database_exists(db_path):
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


def get_weekly_alcohol_data(
    db_path: str, start_date: Optional[str] = None, end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Query weekly alcohol consumption data.

    Args:
        db_path: Path to database
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)

    Returns:
        DataFrame with weekly data
    """
    if not database_exists(db_path):
        return pd.DataFrame(columns=['week_start_date', 'week_end_date', 'total_drinks', 'event_count'])

    try:
        conn = sqlite3.connect(db_path)

        query = "SELECT week_start_date, week_end_date, total_drinks, event_count FROM alcohol_weekly"
        conditions = []
        params = []

        if start_date:
            conditions.append("week_start_date >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("week_start_date <= ?")
            params.append(end_date)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY week_start_date"

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        return df

    except Exception as e:
        logger.error(f"Error querying weekly data: {e}")
        return pd.DataFrame(columns=['week_start_date', 'week_end_date', 'total_drinks', 'event_count'])
