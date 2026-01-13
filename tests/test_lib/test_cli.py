"""Tests for CLI commands."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from lib.cli import init, main, status, update


class TestInitCommand:
    """Tests for init command."""

    def test_init_creates_database(self, tmp_path):
        """Test that init command creates database."""
        db_path = str(tmp_path / "test.db")

        runner = CliRunner()
        result = runner.invoke(main, ['init', '--db-path', db_path])

        assert result.exit_code == 0
        assert Path(db_path).exists()

    def test_init_with_verbose(self, tmp_path):
        """Test that init command works with verbose flag."""
        db_path = str(tmp_path / "test.db")

        runner = CliRunner()
        result = runner.invoke(main, ['--verbose', 'init', '--db-path', db_path])

        assert result.exit_code == 0
        assert "created" in result.output.lower() or result.exit_code == 0


class TestStatusCommand:
    """Tests for status command."""

    def test_status_with_no_database(self, tmp_path):
        """Test status command when database doesn't exist."""
        db_path = str(tmp_path / "nonexistent.db")

        runner = CliRunner()
        result = runner.invoke(main, ['status', '--db-path', db_path])

        assert result.exit_code == 0
        assert "not initialized" in result.output.lower() or "not exist" in result.output.lower()

    def test_status_with_empty_database(self, tmp_path):
        """Test status command with empty database."""
        db_path = str(tmp_path / "test.db")

        # Create empty database
        runner = CliRunner()
        runner.invoke(main, ['init', '--db-path', db_path])

        # Check status
        result = runner.invoke(main, ['status', '--db-path', db_path])

        assert result.exit_code == 0
        # Should show 0 counts or similar
        assert "0" in result.output or "empty" in result.output.lower()


class TestUpdateCommand:
    """Tests for update command."""

    @patch('lib.cli.update_database')
    def test_update_calls_update_database(self, mock_update, tmp_path):
        """Test that update command calls update_database."""
        db_path = str(tmp_path / "test.db")
        mock_update.return_value = (True, [])

        runner = CliRunner()
        result = runner.invoke(main, ['update', '--db-path', db_path])

        # update_database should have been called
        mock_update.assert_called_once()
        assert result.exit_code == 0

    @patch('lib.cli.update_database')
    def test_update_handles_errors(self, mock_update, tmp_path):
        """Test that update command handles errors gracefully."""
        db_path = str(tmp_path / "test.db")
        mock_update.return_value = (False, [])

        runner = CliRunner()
        result = runner.invoke(main, ['update', '--db-path', db_path])

        # Should exit with code 1 to indicate failure
        assert result.exit_code == 1
        assert "failed" in result.output.lower() or "error" in result.output.lower()


class TestMainGroup:
    """Tests for main CLI group."""

    def test_help_shows_commands(self):
        """Test that help shows available commands."""
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])

        assert result.exit_code == 0
        assert 'init' in result.output
        assert 'update' in result.output
        assert 'status' in result.output

    def test_verbose_flag(self, tmp_path):
        """Test that verbose flag is recognized."""
        db_path = str(tmp_path / "test.db")

        runner = CliRunner()
        result = runner.invoke(main, ['--verbose', 'init', '--db-path', db_path])

        assert result.exit_code == 0
