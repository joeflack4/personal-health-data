"""Configuration loader."""

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

from lib.models import Config


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from config.yaml and env/.env.

    For SHEET_ID: checks config.yaml first, then env/.env as fallback.

    Args:
        config_path: Optional path to config.yaml file

    Returns:
        Config object with all required configuration

    Raises:
        FileNotFoundError: If config.yaml is not found
        ValueError: If required configuration is missing
    """
    # Load environment variables from env/.env
    env_path = Path("env/.env")
    if env_path.exists():
        load_dotenv(env_path)

    # Load config.yaml
    if config_path is None:
        config_path = "config.yaml"

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, 'r') as f:
        config_data = yaml.safe_load(f)

    # Get SHEET_ID: check config.yaml first, then env variable
    sheet_id = config_data.get('sheet-id') or config_data.get('sheet_id')
    if not sheet_id:
        sheet_id = os.getenv('SHEET_ID')

    if not sheet_id:
        raise ValueError(
            "SHEET_ID is required but not found in config.yaml or env/.env"
        )

    # Get other required config values
    next_day_cutoff = config_data.get('next-day-cutoff-HH-mm-ss', '08:00:00')
    db_path = config_data.get('db-path', 'db.db')
    timezone = config_data.get('timezone', 'America/New_York')
    week_start_day = config_data.get('week-start-day', 'Monday')

    return Config(
        sheet_id=sheet_id,
        next_day_cutoff=next_day_cutoff,
        db_path=db_path,
        timezone=timezone,
        week_start_day=week_start_day,
    )
