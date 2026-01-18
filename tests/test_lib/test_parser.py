"""Tests for parser module."""

import pandas as pd
import pytest
from datetime import datetime

from lib.config import Config
from lib.parser import parse_sheet_data, apply_next_day_cutoff


def test_parse_sheet_data_with_drink_events():
    """Test that drink events are parsed correctly."""
    # Create sample data matching the actual CSV structure
    data = {
        'Timestamp': ['1/28/2021 2:06:51', '1/30/2021 1:08:59'],
        'A) Report event (今)': ['飲み物', '飲み物'],
        'Is now the stop or start time?': [None, None],
        'B) Report event (別時)': [None, None],
        'Retro: stop or start time?': [None, None],
        'Retro: Time': [None, None],
        'Retro: Date': [None, None],
        'Comments': [None, None],
    }
    df = pd.DataFrame(data)

    config = Config(
        sheet_id='test',
        next_day_cutoff='08:00:00',
        db_path='test.db',
        timezone='America/New_York',
        week_start_day='Monday'
    )

    events = parse_sheet_data(df, config)

    assert len(events) == 2, f"Expected 2 events, got {len(events)}"
    assert events[0].event_name == '飲み物'
    assert events[1].event_name == '飲み物'


def test_parse_sheet_data_with_retro_events():
    """Test that retrospective events are parsed correctly."""
    data = {
        'Timestamp': ['1/31/2021 1:32:34'],
        'A) Report event (今)': [None],
        'Is now the stop or start time?': [None],
        'B) Report event (別時)': ['飲み物'],
        'Retro: stop or start time?': [None],
        'Retro: Time': ['10:00:00 PM'],
        'Retro: Date': ['1/31/2021'],
        'Comments': [None],
    }
    df = pd.DataFrame(data)

    config = Config(
        sheet_id='test',
        next_day_cutoff='08:00:00',
        db_path='test.db',
        timezone='America/New_York',
        week_start_day='Monday'
    )

    events = parse_sheet_data(df, config)

    assert len(events) == 1
    assert events[0].event_name == '飲み物'
    assert events[0].event_type == 'retro'


def test_next_day_cutoff_logic():
    """Test that events before cutoff are assigned to previous day."""
    # Event at 2:06 AM should be assigned to previous day
    dt = datetime(2021, 1, 28, 2, 6, 51)
    effective_date = apply_next_day_cutoff(dt, '08:00:00', 'America/New_York')

    assert effective_date == '2021-01-27', f"Expected 2021-01-27, got {effective_date}"

    # Event at 3:17 AM should be assigned to previous day
    dt = datetime(2021, 1, 30, 3, 17, 52)
    effective_date = apply_next_day_cutoff(dt, '08:00:00', 'America/New_York')

    assert effective_date == '2021-01-29', f"Expected 2021-01-29, got {effective_date}"

    # Event at 10:00 PM should stay on same day
    dt = datetime(2021, 1, 31, 22, 0, 0)
    effective_date = apply_next_day_cutoff(dt, '08:00:00', 'America/New_York')

    assert effective_date == '2021-01-31', f"Expected 2021-01-31, got {effective_date}"


def test_parse_retro_event_with_blank_date():
    """Test that retro events with blank Retro: Date fall back to timestamp.

    This tests Problem 1: When Retro: Date is blank, use timestamp's effective date.
    """
    data = {
        'Timestamp': ['1/28/2021 7:00:00'],  # 7am - before 8am cutoff, so effective date is Jan 27
        'A) Report event (今)': [None],
        'Is now the stop or start time?': [None],
        'B) Report event (別時)': ['飲み物'],
        'Retro: stop or start time?': [None],
        'Retro: Time': ['10:00:00 PM'],  # 10pm
        'Retro: Date': [None],  # BLANK - should fall back to timestamp's date
        'Comments': ['1.5'],
    }
    df = pd.DataFrame(data)

    config = Config(
        sheet_id='test',
        next_day_cutoff='08:00:00',
        db_path='test.db',
        timezone='America/New_York',
        week_start_day='Monday'
    )

    events = parse_sheet_data(df, config)

    assert len(events) == 1, f"Expected 1 event, got {len(events)}"
    assert events[0].event_name == '飲み物'
    assert events[0].event_type == 'retro'
    # Should use timestamp's date (Jan 28) with retro time (10pm)
    # 10pm is after 8am cutoff, so effective date should be Jan 28
    assert events[0].actual_datetime.day == 28
    assert events[0].actual_datetime.hour == 22  # 10pm
    assert events[0].effective_date == '2021-01-28'


def test_parse_retro_event_with_blank_date_and_blank_time():
    """Test that retro events with blank Retro: Date and Time use timestamp as-is."""
    data = {
        'Timestamp': ['1/28/2021 7:00:00'],  # 7am - before 8am cutoff
        'A) Report event (今)': [None],
        'Is now the stop or start time?': [None],
        'B) Report event (別時)': ['飲み物'],
        'Retro: stop or start time?': [None],
        'Retro: Time': [None],  # BLANK
        'Retro: Date': [None],  # BLANK
        'Comments': ['2.0'],
    }
    df = pd.DataFrame(data)

    config = Config(
        sheet_id='test',
        next_day_cutoff='08:00:00',
        db_path='test.db',
        timezone='America/New_York',
        week_start_day='Monday'
    )

    events = parse_sheet_data(df, config)

    assert len(events) == 1, f"Expected 1 event, got {len(events)}"
    assert events[0].event_name == '飲み物'
    assert events[0].event_type == 'retro'
    # Should use timestamp as-is: Jan 28, 7am
    # 7am is before 8am cutoff, so effective date should be Jan 27
    assert events[0].actual_datetime.day == 28
    assert events[0].actual_datetime.hour == 7
    assert events[0].effective_date == '2021-01-27'


def test_parse_week_with_11_alcohol_events():
    """Test parsing a specific week that should have 11 total drinks.

    This tests the week of 2024-02-26 to 2024-03-03, which contains 11
    alcohol events totaling 11 drinks. This test ensures our parsing logic correctly:
    1. Handles retro events with blank dates (falls back to timestamp)
    2. Applies next-day cutoff logic correctly
    3. Extracts drink counts from comments (where numeric)
    4. Aggregates by week correctly

    Note: Natural language in comments like "half glass of wine" or "Beer and mixed drink"
    are not parsed; only numeric values at the start of comments are extracted.
    """
    import os
    from lib.transformer import extract_alcohol_events, aggregate_by_week

    csv_path = 'tests/test_lib/input/alc-2024-02-26--2024-03-03-16events.csv'

    if not os.path.exists(csv_path):
        pytest.skip(f"Test CSV file not found: {csv_path}")

    # Read the CSV
    df = pd.read_csv(csv_path)

    config = Config(
        sheet_id='test',
        next_day_cutoff='08:00:00',
        db_path='test.db',
        timezone='America/New_York',
        week_start_day='Monday'
    )

    # Parse events
    events = parse_sheet_data(df, config)

    # Extract alcohol events
    alcohol_events = extract_alcohol_events(events)

    # Filter to the specific week (2024-02-26 to 2024-03-03)
    week_start = '2024-02-26'
    week_end = '2024-03-03'

    week_alcohol_events = [
        e for e in alcohol_events
        if week_start <= e.effective_date <= week_end
    ]

    # Debug output
    print(f"\n=== Week 2024-02-26 to 2024-03-03 Analysis ===")
    print(f"Total rows in CSV: {len(df)}")
    print(f"Total events parsed: {len(events)}")
    print(f"Total alcohol events: {len(alcohol_events)}")
    print(f"Alcohol events in target week: {len(week_alcohol_events)}")
    print(f"\nAlcohol events by date:")

    from collections import defaultdict
    events_by_date = defaultdict(list)
    for event in week_alcohol_events:
        events_by_date[event.effective_date].append(event.drink_count)

    for date in sorted(events_by_date.keys()):
        drinks = events_by_date[date]
        total = sum(drinks)
        print(f"  {date}: {len(drinks)} events, {total:.1f} total drinks")

    # Calculate total drinks
    total_drinks = sum(e.drink_count for e in week_alcohol_events)
    print(f"\nTotal drinks in week: {total_drinks:.1f}")

    # Aggregate by week to double-check
    weekly_df = aggregate_by_week(alcohol_events)
    target_week = weekly_df[weekly_df['week_start_date'] == week_start]

    if not target_week.empty:
        agg_total = target_week.iloc[0]['total_drinks']
        agg_count = target_week.iloc[0]['event_count']
        print(f"Weekly aggregation: {agg_count} events, {agg_total:.1f} total drinks")

    # Assert the expected 11 total drinks
    assert total_drinks == 11.0, (
        f"Expected 11 total drinks in week 2024-02-26 to 2024-03-03, "
        f"but got {total_drinks:.1f}"
    )


def test_parse_sheet_data_with_actual_csv():
    """Test parsing with actual CSV data."""
    # Load the actual CSV we downloaded
    import os
    csv_path = '_archive/temp/health_data_sample.csv'

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)

        config = Config(
            sheet_id='test',
            next_day_cutoff='08:00:00',
            db_path='test.db',
            timezone='America/New_York',
            week_start_day='Monday'
        )

        events = parse_sheet_data(df, config)

        print(f"\nParsed {len(events)} events from {len(df)} rows")
        print(f"First few column names: {list(df.columns[:5])}")

        # Should have at least some drink events
        drink_events = [e for e in events if e.event_name == '飲み物']
        print(f"Found {len(drink_events)} drink events")

        assert len(events) > 0, "Should parse at least some events from actual data"
        assert len(drink_events) > 0, "Should find at least some drink events"
