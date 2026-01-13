"""Command-line interface for health data management."""

import logging
import sys
from pathlib import Path

import click

from lib.config import load_config
from lib.database import create_database, get_last_updated, update_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
@click.option('--config', 'config_path', default=None, help='Path to config file')
@click.pass_context
def main(ctx, verbose, config_path):
    """Personal Health Data CLI - Manage health data and database."""
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config_path

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")


@main.command()
@click.option('--db-path', default=None, help='Database path (overrides config)')
@click.pass_context
def init(ctx, db_path):
    """Initialize the database with schema."""
    try:
        config_path = ctx.obj.get('config_path')
        config = load_config(config_path)

        db_path = db_path or config.db_path

        if Path(db_path).exists():
            click.echo(f"Database already exists at {db_path}")
            if not click.confirm("Overwrite?"):
                return

        create_database(db_path)
        click.echo(f"✓ Database initialized at {db_path}")
        click.echo("  Run 'health-data update' to populate with data")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--db-path', default=None, help='Database path (overrides config)')
@click.pass_context
def update(ctx, db_path):
    """Update database with latest data from Google Sheets."""
    try:
        config_path = ctx.obj.get('config_path')
        config = load_config(config_path)

        db_path = db_path or config.db_path

        click.echo("Updating database...")
        click.echo("  - Fetching data from Google Sheets")
        click.echo("  - Parsing and validating data")
        click.echo("  - Creating backup")
        click.echo("  - Populating database")

        success, errors = update_database(db_path, config_path)

        if success:
            click.echo(f"✓ Database updated successfully")

            if errors:
                click.echo(f"\n⚠ Found {len(errors)} validation errors:")
                for i, error in enumerate(errors[:10], 1):  # Show first 10 errors
                    click.echo(f"  {i}. Row {error.row_number}: {error.error_message}")
                if len(errors) > 10:
                    click.echo(f"  ... and {len(errors) - 10} more errors")
            else:
                click.echo("  No validation errors found")

            # Show last updated time
            last_updated = get_last_updated(db_path)
            if last_updated:
                click.echo(f"\nLast updated: {last_updated}")

        else:
            click.echo(f"✗ Database update failed", err=True)
            sys.exit(1)

    except Exception as e:
        logger.error(f"Failed to update database: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--db-path', default=None, help='Database path (overrides config)')
@click.pass_context
def status(ctx, db_path):
    """Show database status."""
    try:
        config_path = ctx.obj.get('config_path')
        config = load_config(config_path)

        db_path = db_path or config.db_path
        db_file = Path(db_path)

        click.echo(f"Database Status")
        click.echo(f"=" * 50)

        if not db_file.exists():
            click.echo(f"Status: Not initialized")
            click.echo(f"Path: {db_path}")
            click.echo(f"\nRun 'health-data init' to create the database")
            return

        click.echo(f"Status: Initialized")
        click.echo(f"Path: {db_path}")
        click.echo(f"Size: {db_file.stat().st_size / 1024:.2f} KB")

        # Get last updated
        last_updated = get_last_updated(db_path)
        if last_updated:
            click.echo(f"Last updated: {last_updated}")
        else:
            click.echo(f"Last updated: Never (database created but not populated)")

        # Get row counts
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM raw_events")
        raw_count = cursor.fetchone()[0]
        click.echo(f"\nRow counts:")
        click.echo(f"  Raw events: {raw_count}")

        cursor.execute("SELECT COUNT(*) FROM alcohol_events")
        alc_count = cursor.fetchone()[0]
        click.echo(f"  Alcohol events: {alc_count}")

        cursor.execute("SELECT COUNT(*) FROM alcohol_weekly")
        weekly_count = cursor.fetchone()[0]
        click.echo(f"  Weekly aggregations: {weekly_count}")

        conn.close()

    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main(obj={})
