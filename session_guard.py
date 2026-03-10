# session_guard.py

from datetime import datetime, time
import pytz

# Session times in UTC
LONDON_OPEN  = time(8, 0)
LONDON_CLOSE = time(17, 0)
NY_OPEN      = time(13, 0)
NY_CLOSE     = time(22, 0)
FRIDAY_CUTOFF = time(20, 0)

# Daily rollover — brokers pause trading around midnight server time
ROLLOVER_START = time(21, 55)
ROLLOVER_END   = time(22, 10)


def get_utc_now():
    return datetime.now(pytz.utc)


def is_london_session():
    now = get_utc_now().time()
    return LONDON_OPEN <= now <= LONDON_CLOSE


def is_ny_session():
    now = get_utc_now().time()
    return NY_OPEN <= now <= NY_CLOSE


def is_rollover_window():
    now = get_utc_now().time()
    return ROLLOVER_START <= now <= ROLLOVER_END


def is_active_session():
    if is_weekend():
        return False
    if is_friday_cutoff():
        return False
    if is_rollover_window():
        return False
    return is_london_session() or is_ny_session()


def is_friday_cutoff():
    now = get_utc_now()
    return now.weekday() == 4 and now.time() >= FRIDAY_CUTOFF


def is_weekend():
    return get_utc_now().weekday() >= 5


def get_session_status():
    now = get_utc_now()

    if is_weekend():
        return "WEEKEND", "😴 Market closed — Weekend"

    if is_friday_cutoff():
        return "FRIDAY_CLOSE", "⚠️ Friday cutoff — No new trades"

    if is_rollover_window():
        return "ROLLOVER", "⏳ Daily rollover — Trading paused"

    if is_london_session() and is_ny_session():
        return "ACTIVE", "🟢 London + NY overlap — Best trading window"

    if is_london_session():
        return "ACTIVE", "🟢 London session active"

    if is_ny_session():
        return "ACTIVE", "🟢 New York session active"

    return "INACTIVE", "🔴 Outside trading hours — Bot resting"
