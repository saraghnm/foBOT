# news_filter.py

import requests
from datetime import datetime, timedelta
import pytz
from notifier import notify


FOREXFACTORY_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

HIGH_IMPACT_CURRENCIES = ["USD", "EUR"]
FREEZE_MINUTES = 30


def fetch_calendar():
    try:
        response = requests.get(FOREXFACTORY_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Calendar fetch error: {e}")
        return []


def get_high_impact_events():
    events = fetch_calendar()
    high_impact = []

    for event in events:
        if event.get("impact") != "High":
            continue
        if event.get("currency") not in HIGH_IMPACT_CURRENCIES:
            continue

        # Parse event time
        try:
            event_time = datetime.strptime(
                event["date"], "%Y-%m-%dT%H:%M:%S%z"
            )
            high_impact.append({
                "title":    event["title"],
                "currency": event["currency"],
                "time":     event_time,
            })
        except Exception:
            continue

    return high_impact


def is_freeze_window():
    now = datetime.now(pytz.utc)
    events = get_high_impact_events()

    for event in events:
        diff = abs((event["time"] - now).total_seconds() / 60)
        if diff <= FREEZE_MINUTES:
            return True, event["title"], event["currency"]

    return False, None, None


def get_upcoming_events(hours=4):
    now = datetime.now(pytz.utc)
    upcoming = []
    events = get_high_impact_events()

    for event in events:
        diff_minutes = (event["time"] - now).total_seconds() / 60
        if 0 <= diff_minutes <= hours * 60:
            upcoming.append(event)

    return upcoming