# MVP Phase 1: Setup

## Overview
This phase sets up the project environment, dependencies, directory structure, and necessary configuration for the personal health data analysis project.

## Task List

### Environment Setup
- [x] Initialize Python project with `uv`
  - [x] Install `uv` if not already installed
  - [x] Run `uv init` to initialize project
  - [x] Configure `uv` to use Python 3.12

- [x] Create project directory structure
  - [x] Create `app/` directory for Dash application
  - [x] Create `lib/` directory for data processing modules
  - [x] Create `env/` directory for environment variables
  - [x] Verify `notes/` directory exists

- [x] Set up `.gitignore`
  - [x] Add `env/.env` to .gitignore (already present)
  - [x] Add `*.db` and `*.sqlite` to .gitignore (for SQLite databases)
  - [x] Add `*.db.backup` to .gitignore (for database backups)
  - [x] Add standard Python ignores (`.venv/`, `__pycache__/`, `*.pyc`, etc.) (already present)
  - [x] Add `.uv/` if using uv's local cache (not needed)

### Dependencies Installation
- [x] Add core dependencies via `uv`
  - [x] Add `click` for CLI interface
  - [x] Add `pandas` for data manipulation
  - [x] Add `requests` for fetching Google Sheets data
  - [x] Add `dash` for web application framework
  - [x] Add `plotly` for interactive visualizations (included with Dash)
  - [x] Add `dash-bootstrap-components` for UI styling

- [x] Add development dependencies
  - [x] Add `pytest` for testing
  - [x] Add `black` for code formatting
  - [x] Add `ruff` for linting
  - [x] Add `mypy` for type checking

### Configuration Setup
- [x] Update `config.yaml`
  - [x] Add `sheet-id` parameter (not needed - already in env/.env) @user
  - [x] Verify `next-day-cutoff-HH-mm-ss` is set correctly (currently 08:00:00)
  - [x] Add `db-path` parameter: `db.db`
  - [x] Add `timezone` parameter: `America/New_York` (EST)
  - [x] Add `week-start-day` parameter: `Monday`
  - [x] Add any other app configuration (port, host, etc.) (handled in app/config.py instead)

- [x] Create `env/.env.example` template
  - [x] Add `SHEET_ID=` placeholder as fallback if not in config.yaml
  - [x] Document in comments what each variable is for

- [x] Ensure `env/.env` file exists
  - [x] Copy from `.env.example` if needed (already exists with SHEET_ID)
  - [x] Note: Configuration loader should check config.yaml first, then env/.env for SHEET_ID

### Project Metadata
- [x] Create/update `README.md`
  - [x] Add project description
  - [x] Add setup instructions
  - [x] Add usage instructions for CLI
  - [x] Add usage instructions for running the Dash app locally

- [x] Create `pyproject.toml` configuration
  - [x] Set project name, version, description
  - [x] Define entry points for CLI commands
  - [x] Configure tool settings (black, ruff, mypy, pytest)

### Google Sheets Access
- [x] Sheet is public - use export URL
  - [x] Get SHEET_ID from config.yaml or env/.env
  - [x] Test access to sheet with provided SHEET_ID
  - [x] CSV export URL format: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv`

## Completion Criteria
- All directories exist with correct structure
- All dependencies are installed and importable
- Configuration files are in place with required values (db-path: db.db, timezone: EST, week-start-day: Monday)
- `.gitignore` properly excludes sensitive and generated files (db.db, env/.env, backups)
- Documentation is sufficient for another developer to set up the project
- Google Sheets access is verified (public sheet)
- Mock data is created for testing
- Focus is on local development only (no deployment setup needed)
