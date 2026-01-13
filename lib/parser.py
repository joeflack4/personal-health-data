"""Data parser for health tracking data."""

import logging
from datetime import datetime, time, timedelta
from typing import List, Optional

import pandas as pd
import pytz

from lib.models import Config, RawEvent

logger = logging.getLogger(__name__)


def parse_datetime_field(date_str: str, time_str: Optional[str] = None) -> Optional[datetime]:
    """
    Parse datetime from string(s).

    Args:
        date_str: Date string (e.g., "1/30/2021 1:36:16" or "1/31/2021")
        time_str: Optional time string (e.g., "1:00:00 AM")

    Returns:
        datetime object or None if parsing fails
    """
    if pd.isna(date_str) or not date_str:
        return None

    try:
        if time_str and not pd.isna(time_str):
            # Combine date and time
            combined = f"{date_str} {time_str}"
            return pd.to_datetime(combined)
        else:
            return pd.to_datetime(date_str)
    except Exception as e:
        logger.warning(f"Failed to parse datetime: date='{date_str}', time='{time_str}': {e}")
        return None


def apply_next_day_cutoff(dt: datetime, cutoff_time_str: str, tz_str: str) -> str:
    """
    Apply next-day cutoff logic to determine effective date.

    If the event time is between 00:00:00 and cutoff time (e.g., 08:00:00),
    assign to previous day.

    Args:
        dt: The datetime to process
        cutoff_time_str: Cutoff time in HH:MM:SS format (e.g., "08:00:00")
        tz_str: Timezone string (e.g., "America/New_York")

    Returns:
        Effective date in YYYY-MM-DD format
    """
    tz = pytz.timezone(tz_str)
    dt_with_tz = tz.localize(dt) if dt.tzinfo is None else dt.astimezone(tz)

    # Parse cutoff time
    cutoff_hour, cutoff_minute, cutoff_second = map(int, cutoff_time_str.split(':'))
    cutoff = time(cutoff_hour, cutoff_minute, cutoff_second)

    # Check if time is between midnight and cutoff
    event_time = dt_with_tz.time()
    if event_time < cutoff:
        # Assign to previous day
        effective_dt = dt_with_tz - timedelta(days=1)
    else:
        effective_dt = dt_with_tz

    return effective_dt.strftime('%Y-%m-%d')


def parse_sheet_data(df: pd.DataFrame, config: Config) -> List[RawEvent]:
    """
    Parse raw DataFrame into list of RawEvent objects.

    Args:
        df: DataFrame from Google Sheets
        config: Configuration object

    Returns:
        List of RawEvent objects
    """
    events = []

    for idx, row in df.iterrows():
        try:
            # Determine if this is a "now" or "retro" event
            event_now = row.get('A) Report event (今)', '')
            event_retro = row.get('B) Report event (別時)', '')

            if pd.notna(event_now) and event_now:
                # This is a "now" event
                event_type = 'now'
                event_name = str(event_now).strip()
                start_stop = row.get('Is now the stop or start time?')
                start_stop = str(start_stop).strip() if pd.notna(start_stop) else None

                # Parse timestamp
                timestamp_str = row.get('Timestamp')
                actual_dt = parse_datetime_field(timestamp_str)

                if actual_dt is None:
                    logger.warning(f"Row {idx}: Failed to parse timestamp '{timestamp_str}'")
                    continue

            elif pd.notna(event_retro) and event_retro:
                # This is a "retro" event
                event_type = 'retro'
                event_name = str(event_retro).strip()
                start_stop = row.get('Retro: stop or start time?')
                start_stop = str(start_stop).strip() if pd.notna(start_stop) else None

                # Parse retro date and time
                retro_date = row.get('Retro: Date')
                retro_time = row.get('Retro: Time')
                actual_dt = parse_datetime_field(retro_date, retro_time)

                if actual_dt is None:
                    logger.warning(
                        f"Row {idx}: Failed to parse retro datetime date='{retro_date}', time='{retro_time}'"
                    )
                    continue

                # Use timestamp field for reference
                timestamp_str = row.get('Timestamp')
                parse_datetime_field(timestamp_str)  # For validation

            else:
                # Neither event type is populated, skip this row
                continue

            # Apply next-day cutoff to get effective date
            effective_date = apply_next_day_cutoff(
                actual_dt, config.next_day_cutoff, config.timezone
            )

            # Get comments
            comments = row.get('Comments')
            comments = str(comments).strip() if pd.notna(comments) else None

            # Create RawEvent
            event = RawEvent(
                timestamp=parse_datetime_field(row.get('Timestamp')),
                event_type=event_type,
                event_name=event_name,
                start_stop=start_stop,
                actual_datetime=actual_dt,
                effective_date=effective_date,
                comments=comments,
            )

            events.append(event)

        except Exception as e:
            logger.error(f"Row {idx}: Error parsing row: {e}")
            continue

    logger.info(f"Parsed {len(events)} events from {len(df)} rows")
    return events
