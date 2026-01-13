.PHONY: help run start serve init update status clean test format lint

# Default target
help:
	@echo "Personal Health Data - Available Commands:"
	@echo ""
	@echo "  make serve       - Start the Dash app and open in browser"
	@echo "  make run         - Start the Dash app (alias: start)"
	@echo "  make start       - Start the Dash app (alias for run)"
	@echo ""
	@echo "  make init        - Initialize database"
	@echo "  make update      - Update database with latest data"
	@echo "  make status      - Show database status"
	@echo ""
	@echo "  make test        - Run tests"
	@echo "  make format      - Format code with black"
	@echo "  make lint        - Lint code with ruff"
	@echo "  make clean       - Remove database and backups"

# Start app without opening browser
run:
	@echo "Starting Dash app at http://127.0.0.1:8050"
	uv run python -m app.main

# Alias for run
start: run
serve: run

## Start app and open in browser
#serve:
#	@echo "Starting Dash app and opening browser..."
#	@(uv run python -m app.main &); sleep 2; open http://127.0.0.1:8050

# Database commands
init:
	@echo "Initializing database..."
	uv run python -m lib.cli init

update:
	@echo "Updating database..."
	uv run python -m lib.cli update

status:
	@echo "Checking database status..."
	uv run python -m lib.cli status

# Development commands
test:
	@echo "Running tests..."
	uv run pytest

format:
	@echo "Formatting code..."
	uv run black lib/ app/ tests/

lint:
	@echo "Linting code..."
	uv run ruff check lib/ app/ tests/

# Clean up
clean:
	@echo "Cleaning up database and backups..."
	rm -f db.db
	rm -f db.db.*.backup
	@echo "Done!"
