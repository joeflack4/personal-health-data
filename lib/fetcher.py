"""Google Sheets data fetcher."""

import logging
import time
from typing import Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)


def fetch_sheet_data(
    sheet_id: str, max_retries: int = 3, retry_delay: float = 2.0
) -> pd.DataFrame:
    """
    Fetch data from a public Google Sheet as CSV.

    Args:
        sheet_id: The Google Sheet ID
        max_retries: Maximum number of retry attempts
        retry_delay: Delay in seconds between retries

    Returns:
        pandas DataFrame with the sheet data

    Raises:
        requests.RequestException: If fetching fails after all retries
        pd.errors.ParserError: If CSV parsing fails
    """
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

    last_exception = None
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching data from Google Sheets (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Explicitly set encoding to UTF-8 for proper Japanese character handling
            response.encoding = 'utf-8'

            # Parse CSV data into DataFrame
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))

            logger.info(f"Successfully fetched {len(df)} rows from Google Sheets")
            return df

        except (requests.RequestException, pd.errors.ParserError) as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1} failed: {e}")

            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

    # If we get here, all retries failed
    logger.error(f"Failed to fetch data after {max_retries} attempts")
    raise last_exception


def get_sheet_url(sheet_id: str) -> str:
    """
    Get the CSV export URL for a Google Sheet.

    Args:
        sheet_id: The Google Sheet ID

    Returns:
        The CSV export URL
    """
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
