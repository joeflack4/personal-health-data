# Personal Health Data

Dash + SQLite toolchain for analyzing personal health logs that are collected via a Google Forms → Sheets workflow. The current MVP focuses on alcohol consumption: fetch entries from the sheet, normalize them into events, persist them to SQLite, and provide weekly visualizations.

## Capabilities
- **Automated pipeline** – `lib/database.py` orchestrates fetch → parse → validate → transform → persist with backups before any destructive update.
- **CLI + Dash app** – `lib/cli.py` exposes `init`, `update`, and `status` commands; `app/main.py` builds a Dash dashboard with initialize/sync flows and weekly charts.
- **Configurable cutoff logic** – handles late-night events via the `next-day-cutoff-HH-mm-ss` config, plus timezone awareness.
- **Alcohol-specific transforms** – extracts "飲み物" events, parses fractional amounts from comments, and aggregates per week.

## Architecture at a glance
```
config.yaml / env/.env ─▶ lib.config         ┐
                              │             │
Google Sheet CSV ─▶ lib.fetcher ─▶ lib.parser ─▶ lib.validator ─▶ lib.transformer ─▶ lib.database
                                                                            │
                                                                      SQLite (db.db)
                                                                            │
                                                     app.database ─▶ app.main/layout/plots
```
- `lib/`: pipeline modules plus the Click CLI entry point.
- `app/`: Dash UI, callbacks, and DB adapters for visualization.
- `notes/`: legacy MVP planning notes for additional context.
- `tests/`: parser unit tests and an end-to-end pipeline smoke test (hits the live Google Sheet).

## Requirements
- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv) for dependency management
- Access to the Google Sheet used for tracking (public CSV export)

## Setup
1. Install project dependencies:
   ```bash
   uv sync
   ```
2. Copy `env/.env.example` to `env/.env` and set `SHEET_ID` if it is not already provided in `config.yaml`.
3. Review `config.yaml` for `db-path`, timezone, and week start preferences.
4. (Optional) Install `pre-commit` hooks or other tooling as needed.

## Configuration
`lib.config.load_config` merges the following sources (later values override earlier ones):
1. `config.yaml` (committed) – contains `next-day-cutoff-HH-mm-ss`, `db-path`, `timezone`, and `week-start-day`. You can also add `sheet-id` here.
2. `env/.env` – used primarily for `SHEET_ID` or other secrets you do not want in Git.

If `SHEET_ID` is missing in both places, CLI/app operations will raise a `ValueError`.

## Running the project
### Make targets
The `Makefile` wraps common commands:
```bash
make run     # Start Dash app (aliases: make start, make serve)
make init    # Create SQLite schema
make update  # Fetch + populate DB
make status  # Inspect DB stats and last update timestamp
make test    # Run pytest
make format  # black
make lint    # ruff
make clean   # Remove db.db and backups
```

### CLI directly
```bash
uv run python -m lib.cli init                 # Initialize schema (prompts before overwrite)
uv run python -m lib.cli update               # Pull latest sheet data and rebuild db.db
uv run python -m lib.cli status               # Print metadata and row counts
uv run python -m lib.cli --verbose update     # Enable DEBUG logging
```

### Dash dashboard
```bash
uv run python -m app.main
# or: make run
```
Visit http://127.0.0.1:8050. The UI surfaces three states:
1. **No DB** – displays an "Initialize" button that creates schema and kicks off a background `lib.cli update`.
2. **Updating** – shows a spinner when the DB exists but `db_metadata.last_updated` is null; page polls every 30 seconds.
3. **Ready** – exposes date pickers, a weekly drinks chart (with trend line), and a "Sync" button that triggers another background update.

## Data pipeline details
1. **Fetch** (`lib.fetcher.fetch_sheet_data`) – downloads the sheet as UTF-8 CSV with retry/backoff logic.
2. **Parse** (`lib.parser.parse_sheet_data`) – normalizes "now" (今) and "retro" (別時) events, applies next-day cutoff logic, and captures comments.
3. **Validate** (`lib.validator.validate_events`) – pairs Start/Stop events, flags >24 hour spans, and records validation errors.
4. **Transform** (`lib.transformer.extract_alcohol_events` & `aggregate_by_week`) – isolates "飲み物" entries, infers fractional drink counts from comments, and aggregates by week.
5. **Persist** (`lib.database.populate_database`) – writes raw events, derived alcohol events, weekly summaries, and metadata. `update_database` always backs up the current DB, recreates schema, populates new data, and restores the backup if anything fails.

### Database tables
- `raw_events` – normalized source rows plus validation metadata.
- `alcohol_events` – per-event drink counts tied back to `raw_events`.
- `alcohol_weekly` – aggregated totals (`total_drinks`, `event_count`) with week start/end dates.
- `db_metadata` – currently tracks `last_updated`.

## Testing & quality
```bash
uv run pytest     # parser + integration tests (integration test hits live Google Sheet)
uv run ruff check lib/ app/ tests/
uv run black lib/ app/ tests/
uv run mypy lib/ app/
```
- The integration test (`tests/test_lib/test_integration.py`) talks to the real sheet. Expect failures if you lack network access or the sheet schema changes.
- Unit tests focus on parser behavior and next-day cutoff logic. Add more coverage for transformers/database changes as the project grows.

## Troubleshooting
- **Missing SHEET_ID** – ensure either `config.yaml` contains `sheet-id` or `env/.env` contains `SHEET_ID`.
- **Database corruption** – delete `db.db`, rerun `lib.cli init`, then `lib.cli update`. Backups live alongside the main DB as `db.db.*.backup` (last 5 kept).
- **Dash shows "Update In Progress" forever** – verify that `lib.cli update` can reach the Google Sheet and that the process logs a success.

## Additional docs
- `AGENTS.md` – quick orientation for future contributors/agents.
- `notes/issues/...` – legacy planning documents detailing the MVP scope and decisions.
