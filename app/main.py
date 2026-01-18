"""Main Dash application."""

import logging
import subprocess
import sys
import threading
from datetime import datetime, timedelta
from typing import Optional

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback_context, dcc, html

from app import database as db_module
from app.config import APP_DEBUG, APP_HOST, APP_PORT, APP_TITLE, DB_PATH
from app.layout import (
    create_dashboard_page,
    create_data_visualization_content,
    create_layout,
    create_options_page,
)
from app.plots import create_weekly_drinks_chart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css",
    ],
    title=APP_TITLE,
    suppress_callback_exceptions=True,
)

# Expose Flask server for production WSGI servers (e.g., Gunicorn)
server = app.server

# Set layout
app.layout = create_layout()


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')],
)
def display_page(pathname):
    """Route to different pages based on URL."""
    if pathname == '/options':
        return create_options_page()
    else:
        # Default to dashboard
        return create_dashboard_page()


@app.callback(
    [
        Output('sidebar', 'style'),
        Output('sidebar-toggle', 'style'),
        Output('page-content', 'style'),
        Output('sidebar-collapsed', 'data'),
        Output('sidebar-title', 'style'),
        Output('nav-dashboard-text', 'style'),
        Output('nav-options-text', 'style'),
    ],
    [Input('sidebar-toggle', 'n_clicks')],
    [State('sidebar-collapsed', 'data')],
)
def toggle_sidebar(n_clicks, is_collapsed):
    """Toggle sidebar between collapsed and expanded states."""
    if n_clicks is None:
        # Initial state (collapsed)
        sidebar_style = {
            "position": "fixed",
            "top": 0,
            "left": 0,
            "bottom": 0,
            "width": "4rem",
            "padding": "0",
            "background-color": "#2c3e50",
            "transition": "width 0.3s ease",
            "overflow": "hidden",
            "z-index": 1000,
        }
        toggle_style = {
            "position": "fixed",
            "top": "1rem",
            "left": "4.5rem",
            "z-index": 1001,
            "border": "none",
            "background-color": "#2c3e50",
            "color": "white",
            "font-size": "1.5rem",
            "cursor": "pointer",
            "padding": "0.25rem 0.5rem",
            "border-radius": "0.25rem",
            "transition": "left 0.3s ease",
        }
        content_style = {
            "margin-left": "5rem",
            "padding": "2rem",
            "transition": "margin-left 0.3s ease",
        }
        # Hide text in collapsed state
        text_style = {"display": "none"}
        return sidebar_style, toggle_style, content_style, True, text_style, text_style, text_style

    # Toggle state
    new_collapsed = not is_collapsed

    if new_collapsed:
        # Collapsed state
        sidebar_style = {
            "position": "fixed",
            "top": 0,
            "left": 0,
            "bottom": 0,
            "width": "4rem",
            "padding": "0",
            "background-color": "#2c3e50",
            "transition": "width 0.3s ease",
            "overflow": "hidden",
            "z-index": 1000,
        }
        toggle_style = {
            "position": "fixed",
            "top": "1rem",
            "left": "4.5rem",
            "z-index": 1001,
            "border": "none",
            "background-color": "#2c3e50",
            "color": "white",
            "font-size": "1.5rem",
            "cursor": "pointer",
            "padding": "0.25rem 0.5rem",
            "border-radius": "0.25rem",
            "transition": "left 0.3s ease",
        }
        content_style = {
            "margin-left": "5rem",
            "padding": "2rem",
            "transition": "margin-left 0.3s ease",
        }
        # Hide text in collapsed state
        text_style = {"display": "none"}
    else:
        # Expanded state
        sidebar_style = {
            "position": "fixed",
            "top": 0,
            "left": 0,
            "bottom": 0,
            "width": "16rem",
            "padding": "0",
            "background-color": "#2c3e50",
            "transition": "width 0.3s ease",
            "overflow": "hidden",
            "z-index": 1000,
        }
        toggle_style = {
            "position": "fixed",
            "top": "1rem",
            "left": "16.5rem",
            "z-index": 1001,
            "border": "none",
            "background-color": "#2c3e50",
            "color": "white",
            "font-size": "1.5rem",
            "cursor": "pointer",
            "padding": "0.25rem 0.5rem",
            "border-radius": "0.25rem",
            "transition": "left 0.3s ease",
        }
        content_style = {
            "margin-left": "17rem",
            "padding": "2rem",
            "transition": "margin-left 0.3s ease",
        }
        # Show text in expanded state
        text_style = {"display": "inline"}

    return sidebar_style, toggle_style, content_style, new_collapsed, text_style, text_style, text_style


def run_database_operation(operation: str) -> None:
    """
    Run database operation in background.

    Args:
        operation: 'init' or 'update'
    """
    try:
        logger.info(f"Starting background database {operation}")
        cmd = [sys.executable, "-m", "lib.cli", operation, "--db-path", DB_PATH]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode == 0:
            logger.info(f"Database {operation} completed successfully")
        else:
            logger.error(f"Database {operation} failed: {result.stderr}")

    except Exception as e:
        logger.error(f"Error running database {operation}: {e}")


def create_init_ui() -> html.Div:
    """Create initialization UI component (reusable)."""
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H4("Database Not Initialized", className="text-warning"),
                    html.P("Click the button below to create and populate the database."),
                    dbc.Button(
                        "Initialize Database",
                        id="init-button",
                        color="primary",
                        size="lg",
                        className="mt-2",
                    ),
                    html.Div(id='init-feedback', className="mt-3"),
                ]
            )
        ],
        className="mb-4",
    )


def create_updating_ui() -> html.Div:
    """Create updating in progress UI component (reusable)."""
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H4("Database Update In Progress", className="text-info"),
                    dbc.Spinner(color="primary", size="lg"),
                    html.P(
                        "The database is being populated with data from Google Sheets. "
                        "This may take a few minutes. Please check back shortly.",
                        className="mt-3",
                    ),
                    html.P(
                        "This page will automatically refresh every 30 seconds to check for completion.",
                        className="text-muted small",
                    ),
                ]
            )
        ],
        className="mb-4",
    )


@app.callback(
    [
        Output('dashboard-init-status', 'children'),
        Output('dashboard-content', 'children'),
        Output('poll-interval', 'disabled'),
        Output('db-state', 'data'),
    ],
    [Input('poll-interval', 'n_intervals'), Input('url', 'pathname')],
    [State('db-state', 'data')],
)
def update_dashboard(n_intervals, pathname, db_state_data):
    """
    Update Dashboard page based on database state.

    Three states:
    1. Database doesn't exist - show Initialize button
    2. Database exists, last_updated is null - show "update in progress"
    3. Database exists, last_updated has value - show data visualization
    """
    # Only update if we're on the dashboard page
    if pathname != '/' and pathname != None:
        return html.Div(), html.Div(), True, db_state_data or {}

    db_exists = db_module.database_exists(DB_PATH)
    last_updated = db_module.get_last_updated(DB_PATH) if db_exists else None

    # Determine state
    if not db_exists:
        # State 1: No database
        init_status = create_init_ui()
        main_content = html.Div()
        poll_disabled = True
        state = "no_db"

    elif last_updated is None:
        # State 2: Database exists but update in progress
        init_status = create_updating_ui()
        main_content = html.Div()
        poll_disabled = False  # Enable polling
        state = "updating"

    else:
        # State 3: Database ready with data
        init_status = html.Div()  # Hide init status
        main_content = create_data_visualization_content(last_updated)
        poll_disabled = True  # Disable polling
        state = "ready"

    return init_status, main_content, poll_disabled, {'state': state}


@app.callback(
    [
        Output('options-init-status', 'children'),
        Output('options-content', 'children'),
    ],
    [Input('poll-interval', 'n_intervals'), Input('url', 'pathname')],
    [State('db-state', 'data')],
)
def update_options(n_intervals, pathname, db_state_data):
    """
    Update Options page based on database state.

    Three states:
    1. Database doesn't exist - show Initialize button
    2. Database exists, last_updated is null - show "update in progress"
    3. Database exists, last_updated has value - show database status
    """
    # Only update if we're on the options page
    if pathname != '/options':
        return html.Div(), html.Div()

    db_exists = db_module.database_exists(DB_PATH)
    last_updated = db_module.get_last_updated(DB_PATH) if db_exists else None

    # Determine state
    if not db_exists:
        # State 1: No database
        init_status = create_init_ui()
        options_content = html.Div()

    elif last_updated is None:
        # State 2: Database exists but update in progress
        init_status = create_updating_ui()
        options_content = html.Div()

    else:
        # State 3: Database ready with data
        init_status = html.Div()  # Hide init status

        # Parse last_updated
        try:
            last_updated_dt = datetime.fromisoformat(last_updated)
            last_updated_str = last_updated_dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            last_updated_str = last_updated

        options_content = dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H4("Database Status", className="text-success"),
                        html.P([html.Strong("Last Updated: "), last_updated_str]),
                        dbc.Button(
                            "Sync Data",
                            id="sync-button",
                            color="primary",
                            className="mt-2",
                        ),
                        html.Div(id='sync-feedback', className="mt-3"),
                    ]
                )
            ],
            className="mb-4",
        )

    return init_status, options_content


@app.callback(
    Output('init-feedback', 'children'),
    [Input('init-button', 'n_clicks')],
    prevent_initial_call=True,
)
def initialize_database(n_clicks):
    """Handle Initialize Database button click."""
    if n_clicks:
        logger.info("Initialize button clicked")

        # Create database with schema
        from lib.database import create_database

        try:
            create_database(DB_PATH)

            # Start background data population
            thread = threading.Thread(target=run_database_operation, args=('update',))
            thread.daemon = True
            thread.start()

            return dbc.Alert(
                [
                    html.H5("Database initialization in progress.", className="alert-heading"),
                    html.P(
                        "The database has been initialized and data fetch has started. "
                        "Please refresh this page in a few minutes to see your data."
                    ),
                ],
                color="success",
                dismissable=True,
            )

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return dbc.Alert(
                f"Error initializing database: {e}",
                color="danger",
                dismissable=True,
            )

    return html.Div()


@app.callback(
    Output('sync-feedback', 'children'),
    [Input('sync-button', 'n_clicks')],
    prevent_initial_call=True,
)
def sync_database(n_clicks):
    """Handle Sync button click."""
    if n_clicks:
        logger.info("Sync button clicked")

        try:
            # Start background update
            thread = threading.Thread(target=run_database_operation, args=('update',))
            thread.daemon = True
            thread.start()

            return dbc.Alert(
                [
                    html.H5("Sync Started!", className="alert-heading"),
                    html.P(
                        "Database sync has been initiated. "
                        "Please refresh this page in a few minutes to see updated data."
                    ),
                ],
                color="info",
                dismissable=True,
            )

        except Exception as e:
            logger.error(f"Failed to sync database: {e}")
            return dbc.Alert(
                f"Error syncing database: {e}",
                color="danger",
                dismissable=True,
            )

    return html.Div()


@app.callback(
    Output('quick-range-n', 'options'),
    [Input('quick-range-unit', 'value')],
)
def update_quick_range_options(unit):
    """Update quick range N options based on selected unit."""
    if unit == 'months':
        return [
            {'label': '3', 'value': 3},
            {'label': '6', 'value': 6},
            {'label': '12', 'value': 12},
        ]
    else:  # years
        # Get data to calculate available years
        try:
            df = db_module.get_weekly_alcohol_data(DB_PATH, None, None)
            if not df.empty:
                df_dates = df['week_start_date'].astype('datetime64[ns]')
                min_date = df_dates.min()
                max_date = df_dates.max()
                years_span = (max_date - min_date).days / 365.25
                max_years = max(1, int(years_span) + 1)

                # Create options for 1 to max_years
                return [{'label': str(i), 'value': i} for i in range(1, max_years + 1)]
            else:
                return [{'label': '1', 'value': 1}]
        except Exception:
            return [{'label': '1', 'value': 1}]


@app.callback(
    [
        Output('date-range', 'start_date'),
        Output('date-range', 'end_date'),
    ],
    [
        Input('quick-range-go', 'n_clicks'),
        Input('url', 'search'),
    ],
    [
        State('quick-range-n', 'value'),
        State('quick-range-unit', 'value'),
    ],
    prevent_initial_call=False,
)
def update_date_range_from_quick_selector(n_clicks, search, n_value, unit):
    """Update date range based on quick selector or URL params."""
    from urllib.parse import parse_qs, urlparse

    ctx = callback_context
    if not ctx.triggered:
        trigger_id = 'url'
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Check if triggered by URL params
    if trigger_id == 'url' and search:
        params = parse_qs(search.lstrip('?'))
        start_date = params.get('alc-weekly-from', [None])[0]
        end_date = params.get('alc-weekly-to', [None])[0]

        if start_date and end_date:
            return start_date, end_date

    # Check if triggered by quick range go button
    if trigger_id == 'quick-range-go' and n_clicks:
        # Get data to calculate date range
        try:
            df = db_module.get_weekly_alcohol_data(DB_PATH, None, None)
            if not df.empty:
                df_dates = df['week_start_date'].astype('datetime64[ns]')
                max_date = df_dates.max()

                if unit == 'months':
                    days = n_value * 30  # Approximate
                else:  # years
                    days = n_value * 365

                min_date = max_date - timedelta(days=days)
                return min_date.strftime('%Y-%m-%d'), max_date.strftime('%Y-%m-%d')
        except Exception:
            pass

    # Default: return no dates (will be set by chart callback)
    return None, None


@app.callback(
    [
        Output('weekly-chart', 'figure'),
        Output('url', 'search'),
    ],
    [
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date'),
    ],
    [State('url', 'search')],
)
def update_chart(start_date, end_date, current_search):
    """Update chart based on date range selection and sync URL params."""
    # Get data
    df = db_module.get_weekly_alcohol_data(DB_PATH, start_date, end_date)

    # Set default date range if not set
    if not start_date and not df.empty:
        # Default to last 6 months
        df_dates = df['week_start_date'].astype('datetime64[ns]')
        max_date = df_dates.max()
        min_date = max_date - timedelta(days=180)
        start_date = min_date.strftime('%Y-%m-%d')
        end_date = max_date.strftime('%Y-%m-%d')

        # Re-query with date range
        df = db_module.get_weekly_alcohol_data(DB_PATH, start_date, end_date)

    # Create chart
    fig = create_weekly_drinks_chart(df)

    # Update URL query params
    if start_date and end_date:
        new_search = f"?alc-weekly-from={start_date}&alc-weekly-to={end_date}"
    else:
        new_search = ""

    return fig, new_search


def main():
    """Run the Dash app."""
    logger.info(f"Starting Dash app at http://{APP_HOST}:{APP_PORT}")
    app.run(host=APP_HOST, port=APP_PORT, debug=APP_DEBUG)


if __name__ == '__main__':
    main()
