"""
Framework-agnostic ECharts figure builders for the hashtags analyzer.

These functions accept Polars DataFrames and return ECharts option dicts.
They have no dependency on Shiny, Dash, or NiceGUI.
"""

from datetime import datetime

import polars as pl

from analyzers.hashtags.hashtags_base.interface import (
    OUTPUT_COL_GINI,
    OUTPUT_COL_TIMESPAN,
)

MANGO_DARK_ORANGE = "#f3921e"


def _format_date_for_axis(ts: datetime, is_hourly: bool) -> str:
    """Format datetime for x-axis labels based on bin size."""
    if is_hourly:
        return ts.strftime("%b %d, %Y %H:%M")
    return ts.strftime("%b %d, %Y")


def _detect_is_hourly(df: pl.DataFrame) -> bool:
    """Detect if the time bins are hourly (or smaller) vs daily."""
    if len(df) < 2:
        return False
    time_step = df[OUTPUT_COL_TIMESPAN][1] - df[OUTPUT_COL_TIMESPAN][0]
    return time_step.total_seconds() < 86400


def plot_gini_echart(
    df: pl.DataFrame,
    smooth: bool = False,
) -> dict:
    """
    Build a line chart of Gini coefficient over time.

    Args:
        df: Primary output DataFrame with 'timewindow_start' and 'gini' columns.
        smooth: Whether to include a smoothed line (requires 'gini_smooth' column).

    Returns:
        ECharts option dict ready for ui.echart().
    """
    is_hourly = _detect_is_hourly(df)

    series_data = [
        {
            "value": [ts, gini],
            "raw_ts": ts.strftime("%Y-%m-%d %H:%M"),
            "display_ts": _format_date_for_axis(ts, is_hourly),
        }
        for ts, gini in zip(
            df[OUTPUT_COL_TIMESPAN].to_list(),
            df[OUTPUT_COL_GINI].to_list(),
        )
    ]

    series = [
        {
            "name": "Gini coefficient",
            "type": "line",
            "data": series_data,
            "lineStyle": {"color": "black", "width": 1.5},
            "showSymbol": False,
            "symbol": "circle",
            "symbolSize": 4,
            "itemStyle": {"color": "black"},
            "emphasis": {
                "showSymbol": True,
                "itemStyle": {
                    "color": "#d62728",
                    "symbolSize": 12,
                    "shadowBlur": 10,
                    "shadowColor": "rgba(0, 0, 0, 0.3)",
                },
            },
        }
    ]

    if smooth and "gini_smooth" in df.columns:
        smooth_series_data = [
            {
                "value": [ts, gini_s],
                "raw_ts": ts.strftime("%Y-%m-%d %H:%M"),
                "display_ts": _format_date_for_axis(ts, is_hourly),
            }
            for ts, gini_s in zip(
                df[OUTPUT_COL_TIMESPAN].to_list(),
                df["gini_smooth"].to_list(),
            )
            if gini_s is not None
        ]
        series.append(
            {
                "name": "Smoothed",
                "type": "line",
                "data": smooth_series_data,
                "lineStyle": {"color": MANGO_DARK_ORANGE, "width": 2},
                "itemStyle": {"color": MANGO_DARK_ORANGE},
                "showSymbol": False,
                "emphasis": {
                    "showSymbol": True,
                    "itemStyle": {
                        "color": "#d62728",
                        "symbolSize": 12,
                        "shadowBlur": 10,
                        "shadowColor": "rgba(0, 0, 0, 0.3)",
                    },
                },
            }
        )

    return {
        "title": {"text": "Concentration of hashtags over time"},
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"},
            ":formatter": """function(params) {
                if (!params || params.length === 0) return '';
                var p = params[0];
                var displayTs = p.data ? p.data.display_ts : p.axisValue;
                var html = '<b>' + displayTs + '</b><br/>';
                for (var i = 0; i < params.length; i++) {
                    html += params[i].marker + params[i].seriesName + ': '
                          + params[i].value[1].toFixed(3) + '<br/>';
                }
                return html;
            }""",
        },
        "grid": {"left": 60, "right": 30, "top": 70, "bottom": 50},
        "xAxis": {
            "type": "time",
            "name": "Time window (start date)",
            "nameLocation": "middle",
            "nameGap": 30,
            "nameTextStyle": {"fontSize": 13},
            "axisLabel": {
                "fontSize": 11,
                ":formatter": """function(value) {
                    var date = new Date(value);
                    var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                    return months[date.getMonth()] + ' ' + date.getDate() + ', ' + date.getFullYear();
                }""",
            },
        },
        "yAxis": {
            "type": "value",
            "name": "Hashtag Concentration\n(Gini coefficient)",
            "nameLocation": "middle",
            "nameGap": 50,
            "nameTextStyle": {"fontSize": 13},
            "min": 0,
            "max": 1,
            "axisLabel": {
                ":formatter": "function(value) { return value.toFixed(2); }",
                "fontSize": 11,
            },
        },
        "series": series,
    }
