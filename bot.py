# bot.py
# Main orchestrator — connects to MT5, starts the position monitor,
# listens for Telegram commands, and runs the auto-trading loop.

import time
import threading
from mt5_client import connect, disconnect
from notifier import notify, get_updates
from commands import handle_message, is_paused
from position_monitor import start_monitor
from entry_scanner import scan_entry
from risk_engine import get_trade_parameters
from trade_executor import place_order
from session_guard import is_active_session
from news_filter import is_freeze_window
from config import SYMBOL

# How often the auto-trading loop scans for signals (seconds)
SCAN_INTERVAL = 60


def auto_trade_loop():
    """
    Runs in a background thread.
    Every 60 seconds: checks session, news, signal → places trade if all clear.
    """
    while True:
        try:
            if is_paused():
                time.sleep(SCAN_INTERVAL)
                continue

            if not is_active_session():
                time.sleep(SCAN_INTERVAL)
                continue

            frozen, title, currency = is_freeze_window()
            if frozen:
                time.sleep(SCAN_INTERVAL)
                continue

            # Scan for entry
            signal, bias, details = scan_entry()
            if signal == "NONE":
                time.sleep(SCAN_INTERVAL)
                continue

            # Calculate trade parameters
            params, status = get_trade_parameters(signal, details["price"])
            if not params:
                notify(f"⚠️ Signal found but blocked: {status}")
                time.sleep(SCAN_INTERVAL)
                continue

            # Place order
            emoji = "🟢" if signal == "BUY" else "🔴"
            notify(f"{emoji} Auto signal: {signal} {SYMBOL} — placing order...")

            place_order(
                signal=params["signal"],
                lot_size=params["lot_size"],
                entry_price=params["entry"],
                sl=params["sl"],
                tp=params["tp"],
            )

        except Exception as e:
            notify(f"⚠️ Auto-trade loop error: {e}")

        time.sleep(SCAN_INTERVAL)


def main():
    # ── 1. Connect to MT5 ────────────────────────────────────────────────────
    if not connect():
        print("❌ Could not connect to MT5 — exiting")
        return

    # ── 2. Start position monitor in background ──────────────────────────────
    monitor_thread = threading.Thread(target=start_monitor, daemon=True)
    monitor_thread.start()

    # ── 3. Start auto-trading loop in background ─────────────────────────────
    trader_thread = threading.Thread(target=auto_trade_loop, daemon=True)
    trader_thread.start()

    # ── 4. Notify online ─────────────────────────────────────────────────────
    notify(
        f"🤖 Halal Forex Bot ONLINE\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Symbol:   {SYMBOL}\n"
        f"Monitor:  ✅ Running\n"
        f"Scanner:  ✅ Running\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Send /help for commands"
    )

    # ── 5. Skip old Telegram messages ────────────────────────────────────────
    initial = get_updates()
    if initial.get("result"):
        offset = initial["result"][-1]["update_id"] + 1
    else:
        offset = None

    # ── 6. Main Telegram polling loop ────────────────────────────────────────
    print("✅ Bot is running — listening for Telegram commands...")
    while True:
        try:
            updates = get_updates(offset)
            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                message = update.get("message", {})
                text = message.get("text", "")
                if text:
                    print(f"📩 {text}")
                    handle_message(text)
        except Exception as e:
            notify(f"⚠️ Polling error: {e}")

        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        notify("🛑 Bot stopped manually")
        disconnect()
        print("👋 Bot stopped")