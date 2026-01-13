"""Integration tests for the full data pipeline."""

import os
import sqlite3
import tempfile
from io import StringIO
from unittest.mock import patch

import pandas as pd
import pytest

from lib.config import load_config
from lib.database import create_database, populate_database
from lib.parser import parse_sheet_data


@pytest.fixture
def sample_health_data_csv():
    """Provide sample health data CSV matching real schema."""
    return """Timestamp,A) Report event (今),Is now the stop or start time?,B) Report event (別時),Retro: stop or start time?,Retro: Time,Retro: Date,Comments
1/28/2021 2:06:51,飲み物,,,,,,2.0
1/30/2021 1:08:59,飲み物,,,,,,1.5
1/30/2021 3:17:52,飲み物,,,,,,
1/31/2021 1:32:34,,,飲み物,,10:00:00 PM,1/31/2021,0.5
2/01/2021 12:00:00,Test Event,Start,,,,,
2/01/2021 13:00:00,Test Event,Stop,,,,,"""


@patch('lib.database.fetch_sheet_data')
def test_full_pipeline_with_mocked_data(mock_fetch, sample_health_data_csv, sample_config):
    """Test the full data pipeline from fetch to database (offline, with mocked data)."""
    # Mock the fetcher to return sample CSV data
    df = pd.read_csv(StringIO(sample_health_data_csv))
    mock_fetch.return_value = df

    print("\n1. Mocked data fetch...")
    print(f"   Fetched {len(df)} rows")
    print(f"   Columns: {list(df.columns[:8])}")

    # Parse data
    print("\n2. Parsing data...")
    events = parse_sheet_data(df, sample_config)
    print(f"   Parsed {len(events)} events")

    drink_events = [e for e in events if e.event_name == '飲み物']
    print(f"   Found {len(drink_events)} drink events")

    assert len(events) > 0, "Should parse events from sample data"
    assert len(drink_events) > 0, "Should find drink events in sample data"

    # Test database population
    print("\n3. Testing database population...")
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        test_db = f.name

    try:
        create_database(test_db)

        # Mock load_config to return sample_config
        with patch('lib.database.load_config', return_value=sample_config):
            errors = populate_database(test_db, config_path=None)

        print(f"   Database populated with {len(errors)} errors")

        # Check what's in the database
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM raw_events")
        raw_count = cursor.fetchone()[0]
        print(f"   Raw events in DB: {raw_count}")

        cursor.execute("SELECT COUNT(*) FROM alcohol_events")
        alc_count = cursor.fetchone()[0]
        print(f"   Alcohol events in DB: {alc_count}")

        cursor.execute("SELECT COUNT(*) FROM alcohol_weekly")
        weekly_count = cursor.fetchone()[0]
        print(f"   Weekly aggregations in DB: {weekly_count}")

        conn.close()

        assert raw_count > 0, "Should have raw events in database"
        assert alc_count > 0, "Should have alcohol events in database"
        assert weekly_count > 0, "Should have weekly aggregations in database"

    finally:
        if os.path.exists(test_db):
            os.unlink(test_db)


@pytest.mark.integration
@pytest.mark.skip(reason="Requires network access and real Google Sheets credentials")
def test_full_pipeline_with_real_data():
    """Test the full data pipeline with real Google Sheets data (network required)."""
    from lib.fetcher import fetch_sheet_data

    config = load_config()

    # Fetch data
    print("\n1. Fetching data from Google Sheets...")
    df = fetch_sheet_data(config.sheet_id)
    print(f"   Fetched {len(df)} rows")

    # Parse data
    print("\n2. Parsing data...")
    events = parse_sheet_data(df, config)
    print(f"   Parsed {len(events)} events")

    drink_events = [e for e in events if e.event_name == '飲み物']
    print(f"   Found {len(drink_events)} drink events")

    # Test database population
    print("\n3. Testing database population...")
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        test_db = f.name

    try:
        create_database(test_db)
        errors = populate_database(test_db, config_path=None)

        print(f"   Database populated with {len(errors)} errors")

        # Check what's in the database
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM raw_events")
        raw_count = cursor.fetchone()[0]
        print(f"   Raw events in DB: {raw_count}")

        cursor.execute("SELECT COUNT(*) FROM alcohol_events")
        alc_count = cursor.fetchone()[0]
        print(f"   Alcohol events in DB: {alc_count}")

        cursor.execute("SELECT COUNT(*) FROM alcohol_weekly")
        weekly_count = cursor.fetchone()[0]
        print(f"   Weekly aggregations in DB: {weekly_count}")

        conn.close()

        assert raw_count > 0, "Should have raw events in database"
        assert alc_count > 0, "Should have alcohol events in database"
        assert weekly_count > 0, "Should have weekly aggregations in database"

    finally:
        if os.path.exists(test_db):
            os.unlink(test_db)
