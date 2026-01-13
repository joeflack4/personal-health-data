"""App layout components."""

from dash import dcc, html
import dash_bootstrap_components as dbc


def create_header() -> dbc.Container:
    """Create header section."""
    return dbc.Container(
        [
            html.H1("Personal Health Data Dashboard", className="text-center mb-2"),
            html.P(
                "Paragraph text / subtitle",
                className="text-center text-muted mb-4",
            ),
        ],
        fluid=True,
        className="py-3 bg-light",
    )


def create_sidebar() -> html.Div:
    """Create collapsible sidebar with navigation."""
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H4("Health Data", id="sidebar-title", className="text-white mb-0"),
                        ],
                        className="px-3 py-3 mb-3",
                    ),
                    dbc.Nav(
                        [
                            dbc.NavLink(
                                [
                                    html.I(className="bi bi-graph-up me-2", style={"fontSize": "1.5rem"}),
                                    html.Span("Dashboard", id="nav-dashboard-text"),
                                ],
                                href="/",
                                id="nav-dashboard",
                                active="exact",
                                className="text-white text-center",
                                style={"padding": "0.75rem"},
                            ),
                            dbc.NavLink(
                                [
                                    html.I(className="bi bi-gear me-2", style={"fontSize": "1.5rem"}),
                                    html.Span("Options", id="nav-options-text"),
                                ],
                                href="/options",
                                id="nav-options",
                                active="exact",
                                className="text-white text-center",
                                style={"padding": "0.75rem"},
                            ),
                        ],
                        vertical=True,
                        pills=True,
                    ),
                ],
                id="sidebar-content",
            ),
        ],
        id="sidebar",
        style={
            "position": "fixed",
            "top": 0,
            "left": 0,
            "bottom": 0,
            "width": "4rem",  # Collapsed width (icon only)
            "padding": "0",
            "background-color": "#2c3e50",
            "transition": "width 0.3s ease",
            "overflow": "hidden",
            "z-index": 1000,
        },
    )


def create_init_status_component(page_id: str) -> html.Div:
    """
    Create reusable initialization status component.

    This component is shown on both Dashboard and Options pages
    when the database is not initialized or is being updated.

    Args:
        page_id: Unique identifier for the page ('dashboard' or 'options')
    """
    return html.Div(id=f'{page_id}-init-status')


def create_layout() -> html.Div:
    """
    Create main app layout with sidebar and page routing.

    Handles three database states:
    1. No database - show Initialize button
    2. Database exists, last_updated is null - show "update in progress"
    3. Database exists, last_updated has value - show data
    """
    return html.Div(
        [
            # Location component for URL routing
            dcc.Location(id='url', refresh=False),
            # Interval component for polling when update is in progress
            dcc.Interval(
                id='poll-interval',
                interval=30 * 1000,  # 30 seconds
                n_intervals=0,
                disabled=True,  # Start disabled
            ),
            # Store for tracking database state
            dcc.Store(id='db-state'),
            # Store for sidebar collapse state (default collapsed)
            dcc.Store(id='sidebar-collapsed', data=True),
            # Sidebar
            create_sidebar(),
            # Toggle button for sidebar (fixed position)
            html.Button(
                html.I(className="bi bi-list"),
                id="sidebar-toggle",
                style={
                    "position": "fixed",
                    "top": "1rem",
                    "left": "4.5rem",  # Just right of collapsed sidebar
                    "z-index": 1001,
                    "border": "none",
                    "background-color": "#2c3e50",
                    "color": "white",
                    "font-size": "1.5rem",
                    "cursor": "pointer",
                    "padding": "0.25rem 0.5rem",
                    "border-radius": "0.25rem",
                    "transition": "left 0.3s ease",
                },
            ),
            # Page content (right of sidebar)
            html.Div(
                id='page-content',
                style={
                    "margin-left": "5rem",  # Collapsed sidebar width + padding
                    "padding": "2rem",
                    "transition": "margin-left 0.3s ease",
                },
            ),
        ]
    )


def create_data_visualization_content(last_updated: str) -> html.Div:
    """Create content for when data is available."""
    return html.Div(
        [
            # Quick time range selector
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.Label("Show last ", className="mb-0 me-2"),
                                                    dcc.Dropdown(
                                                        id='quick-range-n',
                                                        options=[
                                                            {'label': '3', 'value': 3},
                                                            {'label': '6', 'value': 6},
                                                            {'label': '12', 'value': 12},
                                                        ],
                                                        value=6,
                                                        clearable=False,
                                                        style={'width': '80px', 'display': 'inline-block'},
                                                        className="me-2",
                                                    ),
                                                    dcc.Dropdown(
                                                        id='quick-range-unit',
                                                        options=[
                                                            {'label': 'months', 'value': 'months'},
                                                            {'label': 'years', 'value': 'years'},
                                                        ],
                                                        value='months',
                                                        clearable=False,
                                                        style={'width': '120px', 'display': 'inline-block'},
                                                        className="me-2",
                                                    ),
                                                    dbc.Button("Go", id='quick-range-go', color="primary", size="sm"),
                                                ],
                                                className="d-flex align-items-center",
                                            ),
                                        ]
                                    )
                                ],
                                className="mb-3",
                            )
                        ],
                        width=12,
                    )
                ]
            ),
            # Date range selector
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Or select custom date range:"),
                            dcc.DatePickerRange(
                                id='date-range',
                                display_format='YYYY-MM-DD',
                                start_date_placeholder_text='Start Date',
                                end_date_placeholder_text='End Date',
                                className="mb-3",
                            ),
                        ],
                        width=12,
                    )
                ]
            ),
            # Chart
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dcc.Loading(
                                id="loading-chart",
                                type="default",
                                children=[dcc.Graph(id='weekly-chart')],
                            )
                        ],
                        width=12,
                    )
                ]
            ),
        ]
    )


def create_dashboard_page() -> html.Div:
    """Create Dashboard page layout."""
    return html.Div(
        [
            html.H2("Dashboard", className="mb-4"),
            # Initialization status component (shown when DB not ready)
            create_init_status_component('dashboard'),
            # Main chart content (shown when DB is ready)
            html.Div(id='dashboard-content'),
        ]
    )


def create_options_page() -> html.Div:
    """Create Options page layout."""
    return html.Div(
        [
            html.H2("Options", className="mb-4"),
            # Initialization status component (shown when DB not ready)
            create_init_status_component('options'),
            # Database status section (shown when DB is ready)
            html.Div(id='options-content'),
        ]
    )
