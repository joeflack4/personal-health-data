"""Data validation logic."""

import logging
from datetime import timedelta
from typing import List, Tuple

from lib.models import ErrorRecord, RawEvent

logger = logging.getLogger(__name__)


def validate_events(events: List[RawEvent]) -> Tuple[List[RawEvent], List[ErrorRecord]]:
    """
    Validate events, particularly Start/Stop pairing for timespan events.

    Args:
        events: List of RawEvent objects

    Returns:
        Tuple of (validated_events, error_records)
    """
    errors = []
    validated_events = []

    # Group events by name for pairing validation
    start_events = {}  # {event_name: list of (index, event)}

    for idx, event in enumerate(events):
        # Skip Start/Stop validation for alcohol events
        if event.event_name == "飲み物":
            validated_events.append(event)
            continue

        if event.start_stop == 'Start':
            # Track start events
            if event.event_name not in start_events:
                start_events[event.event_name] = []
            start_events[event.event_name].append((idx, event))
            validated_events.append(event)

        elif event.start_stop == 'Stop':
            # Find matching Start event
            if event.event_name in start_events and start_events[event.event_name]:
                # Pop the most recent Start event for this name
                start_idx, start_event = start_events[event.event_name].pop(0)

                # Validate timespan
                time_diff = event.actual_datetime - start_event.actual_datetime

                if time_diff.total_seconds() < 0:
                    # Stop before Start
                    event.is_valid = False
                    event.validation_errors = "Stop time is before Start time"
                    errors.append(
                        ErrorRecord(
                            row_number=idx,
                            error_type="invalid_timespan",
                            error_message=f"Stop time before Start time for event '{event.event_name}'",
                            timestamp=event.actual_datetime.isoformat(),
                        )
                    )
                elif time_diff > timedelta(hours=24):
                    # Timespan > 24 hours
                    event.is_valid = False
                    event.validation_errors = "Timespan exceeds 24 hours"
                    errors.append(
                        ErrorRecord(
                            row_number=idx,
                            error_type="invalid_timespan",
                            error_message=f"Timespan > 24 hours for event '{event.event_name}'",
                            timestamp=event.actual_datetime.isoformat(),
                        )
                    )

                validated_events.append(event)
            else:
                # Stop without matching Start
                event.is_valid = False
                event.validation_errors = "Stop event without matching Start"
                errors.append(
                    ErrorRecord(
                        row_number=idx,
                        error_type="unpaired_stop",
                        error_message=f"Stop event without preceding Start for '{event.event_name}'",
                        timestamp=event.actual_datetime.isoformat(),
                    )
                )
                validated_events.append(event)
        else:
            # Not a Start/Stop event, just add it
            validated_events.append(event)

    # Check for unpaired Start events
    for event_name, remaining_starts in start_events.items():
        for idx, event in remaining_starts:
            event.is_valid = False
            event.validation_errors = "Start event without matching Stop"
            errors.append(
                ErrorRecord(
                    row_number=idx,
                    error_type="unpaired_start",
                    error_message=f"Start event without matching Stop for '{event_name}'",
                    timestamp=event.actual_datetime.isoformat(),
                )
            )

    logger.info(f"Validation complete: {len(errors)} errors found")
    return validated_events, errors
