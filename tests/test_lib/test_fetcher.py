"""Tests for Google Sheet fetcher."""

from __future__ import annotations

from typing import List

import pandas as pd
import pytest
import requests

from lib import fetcher


class DummyResponse:
    """Simple stand-in for requests.Response."""

    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code
        self.encoding = None

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def test_get_sheet_url_builds_csv_export_url():
    sheet_id = "abc123"
    expected = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

    assert fetcher.get_sheet_url(sheet_id) == expected


def test_fetch_sheet_data_success(monkeypatch, sample_sheet_csv):
    """fetch_sheet_data should parse CSV text into a DataFrame on success."""
    requested_urls: List[str] = []

    def fake_get(url, timeout):
        requested_urls.append(url)
        return DummyResponse(sample_sheet_csv, status_code=200)

    monkeypatch.setattr(fetcher.requests, "get", fake_get)

    df = fetcher.fetch_sheet_data("sheet-123", max_retries=1)

    assert requested_urls == [fetcher.get_sheet_url("sheet-123")]
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]['A) Report event (今)'] == '飲み物'


def test_fetch_sheet_data_retries_and_raises(monkeypatch):
    """fetch_sheet_data should retry and raise the final exception after failures."""
    call_count = 0

    def fake_get(url, timeout):
        nonlocal call_count
        call_count += 1
        raise requests.RequestException("boom")

    monkeypatch.setattr(fetcher.requests, "get", fake_get)

    with pytest.raises(requests.RequestException):
        fetcher.fetch_sheet_data("sheet-123", max_retries=2, retry_delay=0)

    assert call_count == 2

