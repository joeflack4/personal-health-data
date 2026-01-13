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

