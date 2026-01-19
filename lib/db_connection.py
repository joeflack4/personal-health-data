"""Database connection management for SQLite and PostgreSQL."""

import logging
import os
import sqlite3
from pathlib import Path
from typing import Literal, Optional, Union

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Database backend type
DatabaseType = Literal["sqlite", "postgresql"]


def load_db_env() -> None:
    """Load database environment variables from env/.env."""
    env_path = Path("env/.env")
    if env_path.exists():
        load_dotenv(env_path)


def get_active_env() -> str:
    """
    Get the active environment.

    Returns 'production' by default if ACTIVE_ENV is not set.

    Returns:
        Active environment name: local, production, staging, test, etc.
    """
    load_db_env()
    return os.getenv("ACTIVE_ENV", "production").lower()


def should_use_sqlite() -> bool:
    """
    Determine if SQLite should be used instead of PostgreSQL.

    Returns:
        True if USE_SQLITE is set to True (case-insensitive), False otherwise
    """
    load_db_env()
    use_sqlite = os.getenv("USE_SQLITE", "False")
    return use_sqlite.strip().lower() == "true"


def get_database_type() -> DatabaseType:
    """
    Determine which database backend to use.

    Returns:
        'sqlite' or 'postgresql'
    """
    return "sqlite" if should_use_sqlite() else "postgresql"


def get_pg_connection_url() -> str:
    """
    Get the appropriate PostgreSQL connection URL based on active environment.

    - production, staging, test → use internal URL
    - all other environments → use external URL

    Returns:
        PostgreSQL connection URL

    Raises:
        ValueError: If PostgreSQL is required but connection URL is not configured
    """
    load_db_env()
    active_env = get_active_env()

    if active_env in ["production", "staging", "test"]:
        url = os.getenv("PG_CONNECTION_URL_INTERNAL")
        if not url:
            raise ValueError(
                f"PG_CONNECTION_URL_INTERNAL is required for environment '{active_env}' "
                "but not found in env/.env"
            )
        logger.info(f"Using PostgreSQL internal connection for environment: {active_env}")
        return url
    else:
        url = os.getenv("PG_CONNECTION_URL_EXTERNAL")
        if not url:
            raise ValueError(
                f"PG_CONNECTION_URL_EXTERNAL is required for environment '{active_env}' "
                "but not found in env/.env"
            )
        logger.info(f"Using PostgreSQL external connection for environment: {active_env}")
        return url


def get_sqlite_connection(db_path: str):
    """
    Get a SQLite database connection.

    Args:
        db_path: Path to SQLite database file

    Returns:
        SQLite connection object
    """
    return sqlite3.connect(db_path)


def get_pg_connection():
    """
    Get a PostgreSQL database connection.

    Returns:
        PostgreSQL connection object (psycopg2 connection)

    Raises:
        ImportError: If psycopg2 is not installed
        ValueError: If connection URL is not configured
    """
    try:
        import psycopg2
    except ImportError:
        raise ImportError(
            "psycopg2-binary is required for PostgreSQL support. "
            "Install it with: uv add psycopg2-binary"
        )

    connection_url = get_pg_connection_url()
    return psycopg2.connect(connection_url)


def get_connection(db_path: Optional[str] = None):
    """
    Get a database connection based on configuration.

    Args:
        db_path: Path to SQLite database file (ignored if using PostgreSQL)

    Returns:
        Database connection object (sqlite3.Connection or psycopg2 connection)

    Raises:
        ValueError: If SQLite is selected but db_path is not provided
    """
    db_type = get_database_type()

    if db_type == "sqlite":
        if not db_path:
            raise ValueError("db_path is required when using SQLite")
        logger.info(f"Using SQLite database: {db_path}")
        return get_sqlite_connection(db_path)
    else:
        logger.info("Using PostgreSQL database")
        return get_pg_connection()


def should_migrate_from_sqlite() -> bool:
    """
    Check if SQLite data should be migrated to PostgreSQL on initialization.

    Returns:
        True if PG_INIT_MIGRATE_SQLITE is set to True (case-insensitive)
    """
    load_db_env()
    migrate = os.getenv("PG_INIT_MIGRATE_SQLITE", "False")
    return migrate.strip().lower() == "true"
