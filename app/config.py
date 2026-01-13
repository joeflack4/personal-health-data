"""App configuration."""

import os

from lib.config import load_config

# Load configuration
config = load_config()

# App settings
APP_TITLE = "Personal Health Data Dashboard"
APP_HOST = "127.0.0.1"
APP_PORT = 8050
APP_DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Database path
DB_PATH = config.db_path
