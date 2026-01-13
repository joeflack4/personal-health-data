"""Shared pytest fixtures."""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional

import pytest

from lib.models import Config, RawEvent


@pytest.fixture
def sample_config() -> Config:
    """Return a Config instance with test-friendly defaults."""
    return Config(
        sheet_id="test-sheet",
        next_day_cutoff="08:00:00",
        db_path="test.db",
        timezone="America/New_York",
        week_start_day="Monday",
    )


@pytest.fixture
def sample_sheet_csv() -> str:
    """Provide a minimal CSV string matching the Google Sheet schema."""
    return (
        "Timestamp,A) Report event (今),Is now the stop or start time?,"
        "B) Report event (別時),Retro: stop or start time?,Retro: Time,Retro: Date,Comments\n"
        "1/01/2021 12:00:00,飲み物,,,,,,one drink\n"
    )


@pytest.fixture
def raw_event_factory() -> Callable[..., RawEvent]:
    """Factory to quickly build RawEvent instances for validation tests."""

    def _factory(
        *,
        event_name: str = "Test Event",
        event_type: str = "now",
        start_stop: Optional[str] = None,
        actual_datetime: Optional[datetime] = None,
        comments: Optional[str] = None,
    ) -> RawEvent:
        actual_datetime = actual_datetime or datetime(2021, 1, 1, 12, 0, 0)
        return RawEvent(
            timestamp=actual_datetime,
            event_type=event_type,
            event_name=event_name,
            start_stop=start_stop,
            actual_datetime=actual_datetime,
            effective_date=actual_datetime.strftime("%Y-%m-%d"),
            comments=comments,
        )

    return _factory

