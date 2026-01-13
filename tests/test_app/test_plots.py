"""Tests for app plotting functions."""

import pandas as pd
import pytest

from app.plots import create_weekly_drinks_chart


class TestCreateWeeklyDrinksChart:
    """Tests for create_weekly_drinks_chart function."""

    def test_creates_chart_with_data(self):
        """Test that chart is created with valid data."""
        df = pd.DataFrame({
            'week_start_date': ['2021-01-04', '2021-01-11', '2021-01-18'],
            'week_end_date': ['2021-01-10', '2021-01-17', '2021-01-24'],
            'total_drinks': [5.0, 8.0, 6.0],
            'event_count': [3, 4, 3],
        })

        fig = create_weekly_drinks_chart(df)

        # Verify figure has data
        assert fig is not None
        assert len(fig.data) >= 1  # At least one trace (line chart)

        # Verify title and labels
        assert fig.layout.title.text == "Weekly Alcohol Consumption"
        assert fig.layout.xaxis.title.text == "Week Start Date"
        assert fig.layout.yaxis.title.text == "Total Drinks"

    def test_creates_trend_line(self):
        """Test that trend line is added when there's enough data."""
        df = pd.DataFrame({
            'week_start_date': ['2021-01-04', '2021-01-11', '2021-01-18', '2021-01-25'],
            'week_end_date': ['2021-01-10', '2021-01-17', '2021-01-24', '2021-01-31'],
            'total_drinks': [5.0, 8.0, 6.0, 7.0],
            'event_count': [3, 4, 3, 3],
        })

        fig = create_weekly_drinks_chart(df)

        # Should have at least 2 traces: main line + trend line
        assert len(fig.data) >= 2

    def test_handles_empty_dataframe(self):
        """Test that chart handles empty DataFrame gracefully."""
        df = pd.DataFrame(columns=[
            'week_start_date', 'week_end_date', 'total_drinks', 'event_count'
        ])

        fig = create_weekly_drinks_chart(df)

        # Should still return a figure, even if empty
        assert fig is not None
        assert fig.layout.title.text == "Weekly Alcohol Consumption"

    def test_handles_single_data_point(self):
        """Test that chart handles single data point."""
        df = pd.DataFrame({
            'week_start_date': ['2021-01-04'],
            'week_end_date': ['2021-01-10'],
            'total_drinks': [5.0],
            'event_count': [3],
        })

        fig = create_weekly_drinks_chart(df)

        # Should have at least one trace
        assert fig is not None
        assert len(fig.data) >= 1
