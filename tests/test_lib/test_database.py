"""Tests for database operations."""

import os
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from lib.database import (
    backup_database,
    create_database,
    get_last_updated,
    populate_database,
    restore_database,
    update_database,
)
from lib.models import AlcoholEvent, ErrorRecord, RawEvent


class TestCreateDatabase:
    """Tests for create_database function."""

    def test_creates_all_tables(self, tmp_path):
        """Test that all required tables are created."""
        db_path = str(tmp_path / "test.db")
        create_database(db_path)

        # Verify database exists
        assert Path(db_path).exists()

        # Check tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        assert 'raw_events' in tables
        assert 'alcohol_events' in tables
        assert 'alcohol_weekly' in tables
        assert 'db_metadata' in tables

        conn.close()

    def test_initializes_metadata_with_null(self, tmp_path):
        """Test that db_metadata is initialized with null last_updated."""
        db_path = str(tmp_path / "test.db")
        create_database(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM db_metadata WHERE key = 'last_updated'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] is None  # last_updated should be NULL

    def test_creates_indexes(self, tmp_path):
        """Test that indexes are created."""
        db_path = str(tmp_path / "test.db")
        create_database(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}
        conn.close()

        assert 'idx_raw_events_date' in indexes
        assert 'idx_alcohol_events_date' in indexes
        assert 'idx_alcohol_weekly_date' in indexes


class TestBackupDatabase:
    """Tests for backup_database function."""

    def test_creates_backup_with_timestamp(self, tmp_path):
        """Test that backup is created with timestamp."""
        db_path = str(tmp_path / "test.db")
        create_database(db_path)

        backup_path = backup_database(db_path)

        assert backup_path is not None
        assert Path(backup_path).exists()
        assert backup_path.startswith(db_path)
        assert '.backup' in backup_path

    def test_returns_none_for_missing_database(self, tmp_path):
        """Test that backup returns None if database doesn't exist."""
        db_path = str(tmp_path / "nonexistent.db")
        backup_path = backup_database(db_path)

        assert backup_path is None

    @patch('lib.database.datetime')
    def test_keeps_only_last_5_backups(self, mock_datetime, tmp_path):
        """Test that old backups are cleaned up, keeping only last 5."""
        from datetime import datetime
        from pathlib import Path

        db_path = str(tmp_path / "test.db")
        create_database(db_path)

        # Mock datetime.now() to return incrementing timestamps
        timestamps = [
            datetime(2021, 1, 1, 12, 0, i) for i in range(7)
        ]
        mock_datetime.now.side_effect = timestamps

        # Create 7 backups
        backups = []
        for i in range(7):
            backup_path = backup_database(db_path)
            backups.append(backup_path)

        # Check that only 5 most recent backups exist
        backup_dir = tmp_path
        remaining_backups = list(backup_dir.glob("test.db.*.backup"))
        assert len(remaining_backups) == 5

        # Check that the oldest 2 backups were removed
        for old_backup in backups[:2]:
            assert not Path(old_backup).exists()


class TestRestoreDatabase:
    """Tests for restore_database function."""

    def test_restores_from_backup(self, tmp_path):
        """Test that database is restored from backup."""
        db_path = str(tmp_path / "test.db")
        create_database(db_path)

        # Add some data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO raw_events (timestamp, event_type, event_name, "
            "actual_datetime, effective_date) VALUES (?, ?, ?, ?, ?)",
            ("2021-01-01", "now", "Test", "2021-01-01", "2021-01-01")
        )
        conn.commit()
        conn.close()

        # Create backup
        backup_path = backup_database(db_path)

        # Corrupt/modify the database
        Path(db_path).unlink()
        create_database(db_path)

        # Restore from backup
        restore_database(db_path, backup_path)

        # Verify data is back
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM raw_events")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1

    def test_raises_if_backup_missing(self, tmp_path):
        """Test that restore raises FileNotFoundError if backup doesn't exist."""
        db_path = str(tmp_path / "test.db")
        backup_path = str(tmp_path / "nonexistent.backup")

        with pytest.raises(FileNotFoundError):
            restore_database(db_path, backup_path)


class TestPopulateDatabase:
    """Tests for populate_database function."""

    @patch('lib.database.fetch_sheet_data')
    @patch('lib.database.parse_sheet_data')
    @patch('lib.database.validate_events')
    @patch('lib.database.extract_alcohol_events')
    @patch('lib.database.aggregate_by_week')
    def test_populates_database_successfully(
        self,
        mock_aggregate,
        mock_extract,
        mock_validate,
        mock_parse,
        mock_fetch,
        tmp_path,
        sample_config,
    ):
        """Test successful database population."""
        # Setup mocks
        mock_fetch.return_value = pd.DataFrame()

        raw_event = RawEvent(
            timestamp=pd.Timestamp("2021-01-01 12:00:00"),
            event_type="now",
            event_name="飲み物",
            start_stop=None,
            actual_datetime=pd.Timestamp("2021-01-01 12:00:00"),
            effective_date="2021-01-01",
            comments="1.5",
        )
        mock_parse.return_value = [raw_event]
        mock_validate.return_value = ([raw_event], [])

        alc_event = AlcoholEvent(
            raw_event_id=None,
            effective_date="2021-01-01",
            drink_count=1.5,
            comments="1.5",
        )
        mock_extract.return_value = [alc_event]

        weekly_df = pd.DataFrame({
            'week_start_date': ['2021-01-04'],
            'week_end_date': ['2021-01-10'],
            'total_drinks': [1.5],
            'event_count': [1],
        })
        mock_aggregate.return_value = weekly_df

        # Create database and populate
        db_path = str(tmp_path / "test.db")
        create_database(db_path)

        with patch('lib.database.load_config', return_value=sample_config):
            errors = populate_database(db_path)

        # Verify data was inserted
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM raw_events")
        assert cursor.fetchone()[0] == 1

        cursor.execute("SELECT COUNT(*) FROM alcohol_weekly")
        assert cursor.fetchone()[0] == 1

        # Verify last_updated was set
        cursor.execute("SELECT value FROM db_metadata WHERE key = 'last_updated'")
        result = cursor.fetchone()
        assert result[0] is not None

        conn.close()
        assert errors == []

    @patch('lib.database.fetch_sheet_data')
    @patch('lib.database.parse_sheet_data')
    @patch('lib.database.validate_events')
    @patch('lib.database.extract_alcohol_events')
    @patch('lib.database.aggregate_by_week')
    def test_returns_validation_errors(
        self,
        mock_aggregate,
        mock_extract,
        mock_validate,
        mock_parse,
        mock_fetch,
        tmp_path,
        sample_config,
    ):
        """Test that validation errors are returned."""
        # Setup mocks
        mock_fetch.return_value = pd.DataFrame()
        mock_parse.return_value = []

        error = ErrorRecord(
            row_number=1,
            error_type="unpaired_stop",
            error_message="Stop without Start",
        )
        mock_validate.return_value = ([], [error])
        mock_extract.return_value = []
        mock_aggregate.return_value = pd.DataFrame(columns=[
            'week_start_date', 'week_end_date', 'total_drinks', 'event_count'
        ])

        # Create database and populate
        db_path = str(tmp_path / "test.db")
        create_database(db_path)

        with patch('lib.database.load_config', return_value=sample_config):
            errors = populate_database(db_path)

        assert len(errors) == 1
        assert errors[0].error_type == "unpaired_stop"


class TestUpdateDatabase:
    """Tests for update_database function."""

    @patch('lib.database.populate_database')
    def test_creates_backup_before_update(
        self,
        mock_populate,
        tmp_path,
    ):
        """Test that backup is created before update."""
        db_path = str(tmp_path / "test.db")
        create_database(db_path)

        mock_populate.return_value = []

        success, errors = update_database(db_path)

        # Check that backup was created
        backup_dir = tmp_path
        backups = list(backup_dir.glob("test.db.*.backup"))
        assert len(backups) == 1
        assert success is True

    @patch('lib.database.populate_database')
    def test_restores_on_error(
        self,
        mock_populate,
        tmp_path,
    ):
        """Test that database is restored from backup on error."""
        db_path = str(tmp_path / "test.db")
        create_database(db_path)

        # Add some data to original DB
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO raw_events (timestamp, event_type, event_name, "
            "actual_datetime, effective_date) VALUES (?, ?, ?, ?, ?)",
            ("2021-01-01", "now", "Test", "2021-01-01", "2021-01-01")
        )
        conn.commit()
        conn.close()

        # Make populate_database raise an error
        mock_populate.side_effect = Exception("Test error")

        success, errors = update_database(db_path)

        # Verify update failed
        assert success is False

        # Verify original data is still there (restored from backup)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM raw_events")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1


class TestGetLastUpdated:
    """Tests for get_last_updated function."""

    def test_returns_none_for_missing_database(self, tmp_path):
        """Test that None is returned for missing database."""
        db_path = str(tmp_path / "nonexistent.db")
        result = get_last_updated(db_path)
        assert result is None

    def test_returns_none_for_null_value(self, tmp_path):
        """Test that None is returned when last_updated is NULL."""
        db_path = str(tmp_path / "test.db")
        create_database(db_path)

        result = get_last_updated(db_path)
        assert result is None

    def test_returns_timestamp_when_set(self, tmp_path):
        """Test that timestamp is returned when last_updated is set."""
        db_path = str(tmp_path / "test.db")
        create_database(db_path)

        # Set last_updated
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE db_metadata SET value = ? WHERE key = 'last_updated'",
            ("2021-01-01T12:00:00",)
        )
        conn.commit()
        conn.close()

        result = get_last_updated(db_path)
        assert result == "2021-01-01T12:00:00"
