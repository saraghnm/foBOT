# test_news.py

from mt5_client import connect, disconnect
from news_filter import is_freeze_window, get_upcoming_events
from notifier import notify

if connect():
    # Check freeze window
    frozen, title, currency = is_freeze_window()

    if frozen:
        message = (
            f"🚫 NEWS FREEZE ACTIVE\n"
            f"━━━━━━━━━━━━━━━\n"
            f"Event: {title}\n"
            f"Currency: {currency}\n"
            f"Trading paused ±30 min around event"
        )
    else:
        message = "✅ No news freeze — Trading allowed"

    print(message)
    notify(message)

    # Show upcoming high impact events
    upcoming = get_upcoming_events(hours=24)
    if upcoming:
        events_msg = "📅 Upcoming HIGH impact events (24h):\n━━━━━━━━━━━━━━━\n"
        for e in upcoming:
            events_msg += f"🔴 {e['currency']} — {e['title']}\n⏰ {e['time'].strftime('%a %H:%M UTC')}\n\n"
        print(events_msg)
        notify(events_msg)
    else:
        notify("📅 No high impact events in next 24 hours")

    disconnect()