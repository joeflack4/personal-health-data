# MVP Phase 3: Dash Application

## Overview
This phase implements the Python Dash web application that displays alcohol consumption data with interactive visualizations, including a line graph with date range selection and trend lines.

## Task List

### Phase 3.1: Application Structure

- [x] Create app module structure
  - [x] Create `app/__init__.py`
  - [x] Create `app/main.py` for application entry point
  - [x] Create `app/layout.py` for UI layout components
  - [x] Create `app/database.py` for database queries
  - [x] Create `app/plots.py` for visualization generation
  - [x] Create `app/config.py` for app configuration

- [x] Set up application configuration
  - [x] Load database path from config.yaml (db.db)
  - [x] Configure Dash app settings (title, assets, etc.)
  - [x] Set host and port (default: 127.0.0.1:8050 for local development)
  - [x] Configure debug mode based on environment

### Phase 3.2: Database Interface

- [x] Implement database connection
  - [x] Create SQLite connection with proper error handling
  - [x] Handle database file not found gracefully
  - [x] Close connections properly

- [x] Implement database existence check
  - [x] Function to check if database file exists
  - [x] Function to check if database is initialized (has tables)
  - [x] Function to check if database has data

- [x] Implement metadata queries
  - [x] Query `last_updated` from db_metadata table
  - [x] Handle case where metadata table doesn't exist
  - [x] Handle case where last_updated is null (indicates update in progress)
  - [x] Return formatted datetime string or None if null

- [x] Implement alcohol data queries
  - [x] Query weekly alcohol consumption data
  - [x] Support date range filtering (start_date, end_date)
  - [x] Return as pandas DataFrame
  - [x] Handle empty results gracefully

### Phase 3.3: Data Visualization

- [x] Implement weekly drinks line chart
  - [x] Use plotly.graph_objects or plotly.express
  - [x] X-axis: week_start_date
  - [x] Y-axis: total_drinks
  - [x] Add markers for data points
  - [x] Add hover text with detailed info
  - [x] Style line (color, width)
  - [x] Configure axes labels and title

- [x] Implement trend line calculation
  - [x] Calculate linear regression using numpy or scipy
  - [x] Add trend line to chart as separate trace
  - [x] Style differently from data line (dashed, different color)
  - [x] Add hover text showing trend equation
  - [x] Handle edge cases (< 2 data points)

- [x] Enhance chart interactivity
  - [x] Enable zoom and pan
  - [x] Enable hover tooltips with detailed information
  - [x] Configure responsive layout
  - [x] Set appropriate margins and padding

- [x] Create chart styling
  - [x] Use consistent color scheme
  - [x] Set font sizes for readability
  - [x] Configure grid lines
  - [x] Add legend if multiple traces
  - [x] Ensure mobile responsiveness

### Phase 3.4: UI Layout

- [x] Create main layout structure
  - [x] Use dash-bootstrap-components for styling
  - [x] Choose Bootstrap theme (e.g., BOOTSTRAP, FLATLY, DARKLY)
  - [x] Create container with proper spacing
  - [x] Implement responsive grid layout

- [x] Implement header section
  - [x] Add app title
  - [x] Add subtitle/description
  - [x] Style header appropriately (user commented it out)

- [x] Implement database status section
  - [x] Show "Initialize Database" button if DB doesn't exist
  - [x] If DB exists and last_updated is null: show "Database update in progress, check back in a few minutes"
  - [x] If DB exists and last_updated has datetime: show last updated datetime and Sync button
  - [x] Display last_updated datetime when available
  - [x] Add Sync button (only shown when last_updated has datetime)

- [x] Implement date range selector
  - [x] Add DatePickerRange component
  - [x] Set sensible default range (e.g., last 6 months)
  - [x] Update chart when date range changes

- [x] Implement visualization section
  - [x] Add dcc.Graph component for line chart
  - [x] Add loading spinner while chart renders
  - [x] Add empty state message when no data in range
  - [x] Ensure proper sizing and responsiveness

### Phase 3.5: Interactive Callbacks

- [x] Implement Initialize Database button callback
  - [x] When clicked: create database with schema
  - [x] Set last_updated to null in metadata
  - [x] Immediately show message: "Database is being built, check back in a few minutes"
  - [x] Trigger background process to fetch and populate data
  - [x] When complete, update last_updated to current datetime
  - [x] Handle initialization errors

- [x] Implement Sync button callback
  - [x] When clicked: create backup of current DB
  - [x] Create fresh database with schema
  - [x] Set last_updated to null in metadata
  - [x] Show message: "Database update in progress, check back in a few minutes"
  - [x] Trigger background process to fetch and populate data
  - [x] When complete, update last_updated to current datetime
  - [x] If error occurs: restore from backup
  - [x] Handle errors and display messages

- [x] Important: Single process limitation
  - [x] No web workers available, single server process
  - [x] User may need to manually refresh page to see updates
  - [x] Provide clear user feedback about when to refresh
  - [x] Consider using dcc.Interval for automatic polling (every 30 seconds) when last_updated is null

- [x] Implement date range change callback
  - [x] Trigger when DatePickerRange changes
  - [x] Validate date range
  - [x] Query filtered data from database
  - [x] Regenerate chart with filtered data
  - [x] Handle empty results

- [x] Implement auto-refresh for last_updated display
  - [x] Update display when sync completes
  - [x] Use dcc.Interval for periodic checks (optional)
  - [x] Format datetime for display

- [x] Implement loading states
  - [x] Show loading spinner during database operations
  - [x] Show loading spinner during chart generation
  - [x] Provide user feedback during long operations

### Phase 3.6: Database Initialization Flow

- [x] Implement three-state database flow
  - [x] State 1: DB doesn't exist
    - [x] Show "Initialize Database" button
    - [x] On click: create DB with null last_updated, start data fetch
  - [x] State 2: DB exists, last_updated is null
    - [x] Show "Database update in progress, check back in a few minutes"
    - [x] Optionally use dcc.Interval to auto-refresh when last_updated becomes non-null
  - [x] State 3: DB exists, last_updated has datetime
    - [x] Show data visualizations
    - [x] Show last updated timestamp
    - [x] Show Sync button for manual updates

- [x] Handle page refresh behavior
  - [x] On refresh, re-check DB state
  - [x] If last_updated still null, continue showing "in progress" message
  - [x] If last_updated now has datetime, show visualizations

- [x] Implement error handling for initialization
  - [x] Catch and display initialization errors
  - [x] Provide actionable error messages
  - [x] Allow retry on failure

### Phase 3.7: Background Task Management

- [x] Implement background data fetching
  - [x] Use threading or subprocess to run data fetch in background
  - [x] Main app process continues to serve requests
  - [x] Background process updates last_updated when complete
  - [x] Use dcc.Interval (30-60 second interval) to poll last_updated status
  - [x] When last_updated changes from null to datetime, refresh layout

### Phase 3.8: Error Handling & User Feedback

- [x] Implement error display component
  - [x] Create dbc.Alert or dcc.ConfirmDialog for errors
  - [x] Show user-friendly error messages
  - [x] Make errors dismissible

- [x] Handle common error scenarios
  - [x] Database file not found
  - [x] Database corrupted or invalid schema
  - [x] Network error during Google Sheets fetch
  - [x] No data available for selected range

- [x] Implement success notifications
  - [x] Show success message after sync completes
  - [x] Auto-dismiss after few seconds (dismissable=True)

### Phase 3.9: Application Entry Point

- [x] Create main.py entry point
  - [x] Initialize Dash app
  - [x] Register layout
  - [x] Register callbacks
  - [x] Configure server settings
  - [x] Add run() function with host/port configuration

### Phase 3.10: Styling & Polish

- [x] Apply consistent styling
  - [x] Choose color scheme (consider accessibility) (using Bootstrap theme)
  - [x] Set font family and sizes (Bootstrap defaults)
  - [x] Add appropriate spacing and padding
  - [x] Ensure mobile responsiveness

- [x] Add loading animations
  - [x] Use dash-bootstrap-components spinners
  - [x] Ensure loading states are clear

### Phase 3.11: Testing

- [x] Create test structure
  - [x] Create `tests/test_app/` directory

### Phase 3.12: Documentation

- [x] Create app documentation
  - [x] Document app structure and architecture
  - [x] Document how to run the app locally
  - [x] Document configuration options
  - [x] Document the three-state database flow

- [x] Create user guide
  - [x] How to sync data
  - [x] How to use date range selector
  - [x] How to interpret visualizations
  - [x] Troubleshooting common issues

- [x] Add code documentation
  - [x] Docstrings for all functions
  - [x] Type hints throughout
  - [x] Comments for complex logic

## Completion Criteria
- Dash app runs locally without errors
- App displays weekly alcohol consumption line chart with trend line (weeks start Monday)
- Date range selector filters data correctly
- Initialize Database button creates DB and starts data fetch
- Sync button updates database and refreshes visualization
- Three-state flow works correctly (no DB, updating, populated)
- Last updated timestamp displays correctly when available
- App handles all database states gracefully
- Polling interval successfully detects when last_updated changes from null to datetime
- App is mobile-responsive
- All interactive features work as expected
- Focus is on local development (deployment handled separately by user)
- Documentation is complete and accurate
