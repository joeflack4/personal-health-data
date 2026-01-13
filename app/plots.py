"""Visualization generation."""

import logging

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

logger = logging.getLogger(__name__)


def create_weekly_drinks_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create line chart for weekly alcohol consumption with trend line.

    Args:
        df: DataFrame with columns: week_start_date, total_drinks

    Returns:
        Plotly Figure object
    """
    if df.empty:
        # Return empty chart
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20),
        )
        fig.update_layout(
            title="Weekly Alcohol Consumption",
            xaxis_title="Week",
            yaxis_title="Total Drinks",
            template="plotly_white",
        )
        return fig

    # Convert dates to datetime for proper plotting
    df['week_start_date'] = pd.to_datetime(df['week_start_date'])

    # Create figure
    fig = go.Figure()

    # Add main data line
    fig.add_trace(
        go.Scatter(
            x=df['week_start_date'],
            y=df['total_drinks'],
            mode='lines+markers',
            name='Drinks per Week',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=8),
            hovertemplate='<b>Week of %{x|%Y-%m-%d}</b><br>Total Drinks: %{y:.1f}<extra></extra>',
        )
    )

    # Add trend line if we have enough data points
    if len(df) >= 2:
        # Convert dates to numeric values for regression
        x_numeric = np.arange(len(df))
        y_values = df['total_drinks'].values

        # Calculate linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_numeric, y_values)
        trend_line = slope * x_numeric + intercept

        # Add trend line
        fig.add_trace(
            go.Scatter(
                x=df['week_start_date'],
                y=trend_line,
                mode='lines',
                name='Trend Line',
                line=dict(color='red', width=2, dash='dash'),
                hovertemplate=f'<b>Trend</b><br>y = {slope:.2f}x + {intercept:.2f}<br>R² = {r_value**2:.3f}<extra></extra>',
            )
        )

    # Update layout
    fig.update_layout(
        title='Weekly Alcohol Consumption',
        xaxis_title='Week Start Date',
        yaxis_title='Total Drinks',
        template='plotly_white',
        hovermode='x unified',
        showlegend=True,
        height=500,
        margin=dict(l=60, r=40, t=80, b=60),
    )

    # Format x-axis
    fig.update_xaxes(
        tickformat='%Y-%m-%d',
        tickangle=-45,
    )

    return fig
