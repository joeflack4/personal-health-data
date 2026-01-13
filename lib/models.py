"""Data models and type definitions."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Config:
    """Application configuration."""

    sheet_id: str
    next_day_cutoff: str  # Format: HH:MM:SS
    db_path: str
    timezone: str
    week_start_day: str


@dataclass
class RawEvent:
    """Represents a raw event from the Google Sheet."""

    timestamp: datetime
    event_type: str  # 'now' or 'retro'
    event_name: str
    start_stop: Optional[str]  # 'Start', 'Stop', or None
    actual_datetime: datetime
    effective_date: str  # Date in YYYY-MM-DD format
    comments: Optional[str]
    is_valid: bool = True
    validation_errors: Optional[str] = None


@dataclass
class AlcoholEvent:
    """Represents an alcohol consumption event."""

    raw_event_id: Optional[int]
    effective_date: str
    drink_count: float
    comments: Optional[str]


@dataclass
class ErrorRecord:
    """Represents a validation or processing error."""

    row_number: int
    error_type: str
    error_message: str
    timestamp: Optional[str] = None
