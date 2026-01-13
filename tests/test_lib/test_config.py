"""Tests for configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from lib.config import load_config


def write_config(tmp_path: Path, content: str) -> Path:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(content)
    return config_path


def test_load_config_prefers_file_sheet_id(tmp_path, monkeypatch):
    """Explicit sheet-id in config.yaml should be returned even if env vars exist."""
    monkeypatch.chdir(tmp_path)
    config_path = write_config(
        tmp_path,
        """sheet-id: sheet-from-config\nnext-day-cutoff-HH-mm-ss: 07:00:00\ndb-path: custom.db\n""",
    )

    monkeypatch.setenv("SHEET_ID", "env-value")

    config = load_config(str(config_path))

    assert config.sheet_id == "sheet-from-config"
    assert config.next_day_cutoff == "07:00:00"
    assert config.db_path == "custom.db"


def test_load_config_falls_back_to_env(tmp_path, monkeypatch):
    """When config lacks sheet id, loader should read SHEET_ID from environment."""
    monkeypatch.chdir(tmp_path)
    config_path = write_config(tmp_path, "next-day-cutoff-HH-mm-ss: 08:00:00\n")

    monkeypatch.setenv("SHEET_ID", "sheet-from-env")

    config = load_config(str(config_path))

    assert config.sheet_id == "sheet-from-env"
    assert config.db_path == "db.db"  # default value


def test_load_config_raises_without_sheet_id(tmp_path, monkeypatch):
    """Missing sheet id in both config and environment should raise ValueError."""
    monkeypatch.chdir(tmp_path)
    config_path = write_config(tmp_path, "next-day-cutoff-HH-mm-ss: 08:00:00\n")

    monkeypatch.delenv("SHEET_ID", raising=False)

    with pytest.raises(ValueError):
        load_config(str(config_path))

