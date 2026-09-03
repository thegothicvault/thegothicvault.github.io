# -*- coding: utf-8 -*-
"""
ga_stats.py — GA4 traffic for the dashboard, via the Data API (read-only).

collect_metrics.traffic() imports this; if the library or credentials aren't set
up yet it just falls back to "unavailable", so this file is safe to ship early.

One-time setup (Ofer, ~15 min — see the guide I gave you):
  1. pip:  py -3 -m pip install google-analytics-data
  2. Google Cloud → the same project → create a Service Account → add a JSON key,
     download it to an UNSYNCED folder, e.g. C:\\claude-ads\\ga_service.json
  3. GA4 Admin → Property Access Management → add the service-account email
     (…@….iam.gserviceaccount.com) as Viewer.
  4. GA4 Admin → Property Settings → copy the numeric PROPERTY ID (not G-8ECQ…).
  5. Add to scripts/.env:
        GA4_PROPERTY_ID=123456789
        GOOGLE_APPLICATION_CREDENTIALS=C:\\claude-ads\\ga_service.json
"""
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


def fetch(days=28):
    pid = os.getenv("GA4_PROPERTY_ID")
    if not pid:
        raise RuntimeError("GA4_PROPERTY_ID not set")
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        RunReportRequest, DateRange, Dimension, Metric, Filter, FilterExpression)

    client = BetaAnalyticsDataClient()  # uses GOOGLE_APPLICATION_CREDENTIALS
    prop = f"properties/{pid}"
    dr = [DateRange(start_date=f"{days}daysAgo", end_date="today")]

    # overview: visitors + sessions
    ov = client.run_report(RunReportRequest(
        property=prop, date_ranges=dr,
        metrics=[Metric(name="activeUsers"), Metric(name="sessions")]))
    visitors = int(ov.rows[0].metric_values[0].value) if ov.rows else 0
    sessions = int(ov.rows[0].metric_values[1].value) if ov.rows else 0

    # affiliate clicks, broken down per shoe (the event param we emit on each card)
    per_shoe, total_clicks = {}, 0
    try:
        cr = client.run_report(RunReportRequest(
            property=prop, date_ranges=dr,
            dimensions=[Dimension(name="customEvent:shoe")],
            metrics=[Metric(name="eventCount")],
            dimension_filter=FilterExpression(filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(value="affiliate_click")))))
        for r in cr.rows:
            shoe = r.dimension_values[0].value
            n = int(r.metric_values[0].value)
            per_shoe[shoe] = {"clicks": n}
            total_clicks += n
    except Exception:
        # custom dimension "shoe" may not be registered yet — fall back to total only
        cr = client.run_report(RunReportRequest(
            property=prop, date_ranges=dr,
            dimensions=[Dimension(name="eventName")],
            metrics=[Metric(name="eventCount")]))
        for r in cr.rows:
            if r.dimension_values[0].value == "affiliate_click":
                total_clicks = int(r.metric_values[0].value)

    return {"visitors": visitors, "sessions": sessions,
            "clicks": total_clicks, "per_shoe": per_shoe, "window_days": days}


if __name__ == "__main__":
    import json
    print(json.dumps(fetch(), ensure_ascii=False, indent=2))
