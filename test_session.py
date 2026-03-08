# test_session.py

from mt5_client import connect, disconnect
from session_guard import get_session_status, is_active_session
from notifier import notify

if connect():
    status, message = get_session_status()

    output = (
        f"🕐 Session Check\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{message}\n"
        f"Active for trading: {'✅ YES' if is_active_session() else '❌ NO'}"
    )

    print(output)
    notify(output)

    disconnect()