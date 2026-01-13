# AGENTS.md
This repo is all about personal health data analyses.

## What this project does
- Scrapes a Google Sheet of personal health logs via CSV export, normalizes the events, and stores them in an on-disk SQLite database.
- Derives alcohol-consumption focused aggregates and exposes them through both a CLI (`lib/cli.py`) and a Dash dashboard (`app/main.py`).
- Relies on `uv` for dependency management, `click` for CLI ergonomics, and Plotly Dash + dash-bootstrap-components for UI.

## Environment & tooling expectations
- Python 3.12 with [`uv`](https://github.com/astral-sh/uv) available on the PATH. Run `uv sync` after cloning to install dependencies.
- Configuration lives in `config.yaml` (committed) and `env/.env` (local secrets). `SHEET_ID` must exist in *one* of those files before any pipeline command will work.
- Primary entry points:
  - CLI: `uv run python -m lib.cli <command>` or `uv run health-data <command>`.
  - App: `uv run python -m app.main` or `make run` / `make serve`.
- Tests: `uv run pytest`. Linting (`ruff`), formatting (`black`), and type-checking (`mypy`) are configured—see `Makefile` for shortcuts.

## Key directories & files
- `lib/`: data access/pipeline modules. `lib/database.py` orchestrates fetch → parse → validate → transform → persist, and wraps backups.
- `app/`: Dash application. `app/main.py` wires callbacks, uses helpers from `app/database.py`, and spawns background CLI updates when users click "Initialize"/"Sync".
- `notes/`: legacy MVP implementation guides in case deeper spec history is helpful.
- `config.yaml`, `env/.env`: runtime configuration. `db.db`: generated SQLite DB (gitignored).
- `tests/`: smoketests for parsing and a pipeline integration test (talks to the live Google Sheet).

## Expectations for future agents
1. **Respect the data contract.** Columns referenced in `lib/parser.py`/`lib/transformer.py` are anchored to the Google Sheet headers. Any schema assumptions should be documented in `README.md` and ideally captured in tests.
2. **Keep the CLI/app paths in sync.** App callbacks shell out to `lib.cli`. If you add new database operations or flags, bubble them through both the CLI and Dash buttons.
3. **Backups must remain safe.** `lib/database.update_database` currently backs up before destructive work and retains the last 5 snapshots. Preserve or improve that behavior when touching update flows.
4. **Testing guidance.** `tests/test_lib/test_integration.py` hits the actual Sheet. Add mocking or fixtures if you need deterministic CI, but do not silently change the production sheet URL.
5. **Document user-facing changes.** Update `README.md` and, if necessary, this `AGENTS.md` whenever workflows, dependencies, or expectations change.
6. **Known gaps / TODOs.**
   - `lib/database.populate_database` mis-associates alcohol events with raw event IDs (uses a single `lastrowid`). Fix requires capturing IDs per insert before writing child rows.
   - `lib.transformer.aggregate_by_week` ignores the configurable `week_start_day` value; it always starts weeks on Monday.
   - Tests rely on real HTTP requests; consider adding a mocked path for offline runs.

Use this document as a quick orientation for new contributions.
