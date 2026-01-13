"""Data transformations and aggregations."""

import logging
import re
from typing import List

import pandas as pd

from lib.models import AlcoholEvent, Config, RawEvent

logger = logging.getLogger(__name__)


def extract_alcohol_events(events: List[RawEvent]) -> List[AlcoholEvent]:
    """
    Extract alcohol consumption events from raw events.

    Args:
        events: List of RawEvent objects

    Returns:
        List of AlcoholEvent objects
    """
    alcohol_events = []

    for event in events:
        if event.event_name == "飲み物":  # "drink" in Japanese
            # Default to 1 drink
            drink_count = 1.0

            # Parse comments for quantity override
            if event.comments:
                # Match number at start of comments (e.g., "1.5", ".5", "0.5")
                match = re.match(r'^(\d*\.?\d+)', event.comments.strip())
                if match:
                    try:
                        drink_count = float(match.group(1))
                        logger.debug(
                            f"Parsed drink count from comments: {drink_count} ('{event.comments}')"
                        )
                    except ValueError:
                        logger.warning(f"Failed to parse drink count from '{event.comments}'")
                        drink_count = 1.0

            alcohol_event = AlcoholEvent(
                raw_event_id=None,  # Will be set after DB insertion
                effective_date=event.effective_date,
                drink_count=drink_count,
                comments=event.comments,
            )
            alcohol_events.append(alcohol_event)

    logger.info(f"Extracted {len(alcohol_events)} alcohol events")
    return alcohol_events


def aggregate_by_week(
    alcohol_events: List[AlcoholEvent], week_start_day: str = "Monday"
) -> pd.DataFrame:
    """
    Aggregate alcohol events by week.

    Args:
        alcohol_events: List of AlcoholEvent objects
        week_start_day: Day of week to start weeks (default: "Monday")

    Returns:
        DataFrame with columns: week_start_date, week_end_date, total_drinks, event_count
    """
    if not alcohol_events:
        logger.info("No alcohol events to aggregate")
        return pd.DataFrame(
            columns=['week_start_date', 'week_end_date', 'total_drinks', 'event_count']
        )

    # Convert to DataFrame
    data = []
    for event in alcohol_events:
        data.append(
            {
                'effective_date': event.effective_date,
                'drink_count': event.drink_count,
            }
        )

    df = pd.DataFrame(data)
    df['effective_date'] = pd.to_datetime(df['effective_date'])

    # Calculate week start date (Monday)
    # dt.dayofweek: Monday=0, Sunday=6
    df['week_start'] = df['effective_date'] - pd.to_timedelta(
        df['effective_date'].dt.dayofweek, unit='d'
    )

    # Group by week and aggregate
    weekly = df.groupby('week_start').agg(
        total_drinks=('drink_count', 'sum'), event_count=('drink_count', 'count')
    ).reset_index()

    # Calculate week end date (Sunday)
    weekly['week_end'] = weekly['week_start'] + pd.Timedelta(days=6)

    # Rename and reorder columns
    weekly = weekly.rename(
        columns={'week_start': 'week_start_date', 'week_end': 'week_end_date'}
    )

    # Convert dates to strings
    weekly['week_start_date'] = weekly['week_start_date'].dt.strftime('%Y-%m-%d')
    weekly['week_end_date'] = weekly['week_end_date'].dt.strftime('%Y-%m-%d')

    logger.info(f"Aggregated {len(alcohol_events)} events into {len(weekly)} weeks")
    return weekly
