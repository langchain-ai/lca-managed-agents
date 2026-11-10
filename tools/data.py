"""Data the agent owns (Lab 2).

The weekly stats card is a declared schedule, and declared schedules run as the
agent, so they can't use anyone's personal connections. This tool reads data
the agent owns, bundled with the project, so the schedule always works.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from langchain.tools import tool

METRICS = Path(__file__).resolve().parent.parent / "data" / "weekly_metrics.csv"


@tool
def get_weekly_metrics() -> str:
    """Get this week's and last week's numbers, with the change between them.

    Use this for stats cards and weekly recaps.
    """
    rows = list(csv.DictReader(METRICS.open()))
    this_week, last_week = rows[-1], rows[-2]
    summary = {"this_week": this_week, "last_week": last_week, "change_percent": {}}
    for key, value in this_week.items():
        if key == "week_start":
            continue
        before = float(last_week[key])
        summary["change_percent"][key] = round((float(value) - before) / before * 100, 1) if before else None
    return json.dumps(summary, indent=2)
