"""Tests for transformer module."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from lib.models import AlcoholEvent, RawEvent
from lib.transformer import aggregate_by_week, extract_alcohol_events


def make_raw_event(effective_date: str, comments: str | None = None) -> RawEvent:
    actual_dt = datetime.strptime(effective_date + " 12:00", "%Y-%m-%d %H:%M")
    return RawEvent(
        timestamp=actual_dt,
        event_type="now",
        event_name="飲み物",
        start_stop=None,
        actual_datetime=actual_dt,
        effective_date=effective_date,
        comments=comments,
    )


def test_extract_alcohol_events_default_count():
    events = [make_raw_event("2021-01-01"), make_raw_event("2021-01-02", comments="1.5 beer")]

    alcohol_events = extract_alcohol_events(events)

    assert len(alcohol_events) == 2
    assert alcohol_events[0].drink_count == 1.0
    assert alcohol_events[1].drink_count == 1.5


def test_extract_alcohol_events_handles_invalid_numbers():
    events = [make_raw_event("2021-01-03", comments="abc"), make_raw_event("2021-01-04", comments=".5 more")]

    alcohol_events = extract_alcohol_events(events)

    assert alcohol_events[0].drink_count == 1.0
    assert alcohol_events[1].drink_count == 0.5


def test_aggregate_by_week_groups_on_monday():
    alcohol_events = [
        AlcoholEvent(raw_event_id=None, effective_date="2021-01-04", drink_count=1.0, comments=None),
        AlcoholEvent(raw_event_id=None, effective_date="2021-01-06", drink_count=2.0, comments=None),
        AlcoholEvent(raw_event_id=None, effective_date="2021-01-10", drink_count=3.0, comments=None),
    ]

    weekly = aggregate_by_week(alcohol_events)

    assert isinstance(weekly, pd.DataFrame)
    assert len(weekly) == 1
    assert weekly.iloc[0]['week_start_date'] == '2021-01-04'
    assert weekly.iloc[0]['week_end_date'] == '2021-01-10'
    assert weekly.iloc[0]['total_drinks'] == 6.0
    assert weekly.iloc[0]['event_count'] == 3
