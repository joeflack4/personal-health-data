"""Tests for app.database helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from app import database


def test_database_exists(tmp_path):
    db_file = tmp_path / "db.db"
    assert database.database_exists(str(db_file)) is False
    db_file.write_text("")
    assert database.database_exists(str(db_file)) is True


def test_get_last_updated_returns_value(tmp_path):
    db_file = tmp_path / "db.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE db_metadata (key TEXT PRIMARY KEY, value TEXT)")
    cursor.execute("INSERT INTO db_metadata (key, value) VALUES ('last_updated', '2021-01-01T00:00:00')")
    conn.commit()
    conn.close()

    assert database.get_last_updated(str(db_file)) == "2021-01-01T00:00:00"


def test_get_weekly_alcohol_data_filters_range(tmp_path):
    db_file = tmp_path / "db.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE alcohol_weekly (
            week_start_date TEXT,
            week_end_date TEXT,
            total_drinks REAL,
            event_count INTEGER
        )
        """
    )
    cursor.executemany(
        "INSERT INTO alcohol_weekly VALUES (?, ?, ?, ?)",
        [
            ("2021-01-04", "2021-01-10", 3.0, 2),
            ("2021-01-11", "2021-01-17", 5.0, 3),
        ],
    )
    conn.commit()
    conn.close()

    df = database.get_weekly_alcohol_data(str(db_file), start_date="2021-01-05", end_date="2021-01-12")

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]['total_drinks'] == 5.0

