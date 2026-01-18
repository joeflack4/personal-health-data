"""Tests for validator module."""

from __future__ import annotations

from datetime import datetime, timedelta

from lib.validator import validate_events


def test_validate_events_happy_path(raw_event_factory):
    """Start followed by Stop within 24h should yield no errors."""
    start = raw_event_factory(
        event_name="Sleep",
        start_stop="Start",
        actual_datetime=datetime(2021, 1, 1, 22, 0, 0),
    )
    stop = raw_event_factory(
        event_name="Sleep",
        start_stop="Stop",
        actual_datetime=datetime(2021, 1, 2, 6, 0, 0),
    )

    validated, errors = validate_events([start, stop])

    assert errors == []
    assert all(event.is_valid for event in validated)


def test_validate_events_flags_unpaired_stop(raw_event_factory):
    """Stop events without a prior Start should be flagged as errors."""
    stop = raw_event_factory(
        event_name="Gaming",
        start_stop="Stop",
        actual_datetime=datetime(2021, 1, 1, 10, 0, 0),
    )

    validated, errors = validate_events([stop])

    assert len(errors) == 1
    assert errors[0].error_type == "unpaired_stop"
    assert validated[-1].is_valid is False
    assert validated[-1].validation_errors == "Stop event without matching Start"


def test_validate_events_rejects_long_timespans(raw_event_factory):
    """Durations beyond 24 hours should log an invalid_timespan error."""
    start = raw_event_factory(
        event_name="Meditation",
        start_stop="Start",
        actual_datetime=datetime(2021, 1, 1, 8, 0, 0),
    )
    stop = raw_event_factory(
        event_name="Meditation",
        start_stop="Stop",
        actual_datetime=datetime(2021, 1, 2, 12, 0, 0) + timedelta(hours=12),
    )

    validated, errors = validate_events([start, stop])

    assert len(errors) == 1
    assert errors[0].error_type == "invalid_timespan"
    assert "Timespan > 24 hours" in errors[0].error_message
    assert validated[-1].is_valid is False


def test_validate_events_ignores_start_stop_for_alcohol_events(raw_event_factory):
    """Test that alcohol events with Start/Stop are not validated (Problem 2).

    Alcohol events should skip Start/Stop validation entirely, even if they
    have a Start/Stop value set. They are point-in-time events, not timespans.
    """
    # Alcohol event with "Start" - should be ignored and not flagged as unpaired
    alcohol_start = raw_event_factory(
        event_name="飲み物",
        start_stop="Start",
        actual_datetime=datetime(2021, 1, 1, 20, 0, 0),
    )

    # Alcohol event with "Stop" - should be ignored and not flagged as unpaired
    alcohol_stop = raw_event_factory(
        event_name="飲み物",
        start_stop="Stop",
        actual_datetime=datetime(2021, 1, 1, 22, 0, 0),
    )

    # Regular alcohol event without Start/Stop
    alcohol_regular = raw_event_factory(
        event_name="飲み物",
        start_stop=None,
        actual_datetime=datetime(2021, 1, 2, 19, 0, 0),
    )

    validated, errors = validate_events([alcohol_start, alcohol_stop, alcohol_regular])

    # No errors should be generated for alcohol events
    assert len(errors) == 0, f"Expected no errors, got {errors}"
    # All events should be valid
    assert len(validated) == 3
    assert all(event.is_valid for event in validated)


def test_validate_events_ignores_unpaired_alcohol_start(raw_event_factory):
    """Test that unpaired alcohol Start events are not flagged as errors."""
    # Alcohol event with "Start" but no matching Stop
    alcohol = raw_event_factory(
        event_name="飲み物",
        start_stop="Start",
        actual_datetime=datetime(2021, 1, 1, 20, 0, 0),
    )

    # Non-alcohol event with unpaired Start (should be flagged)
    sleep = raw_event_factory(
        event_name="Sleep",
        start_stop="Start",
        actual_datetime=datetime(2021, 1, 1, 22, 0, 0),
    )

    validated, errors = validate_events([alcohol, sleep])

    # Only 1 error for the Sleep event, not for alcohol
    assert len(errors) == 1
    assert errors[0].error_type == "unpaired_start"
    assert "Sleep" in errors[0].error_message
    assert "飲み物" not in errors[0].error_message

    # Alcohol event should be valid
    assert validated[0].is_valid is True
    # Sleep event should be invalid
    assert validated[1].is_valid is False

