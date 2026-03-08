# test_entry.py

from mt5_client import connect, disconnect
from entry_scanner import scan_entry
from notifier import notify

if connect():
    signal, bias, details = scan_entry()

    if signal == "NONE":
        message = (
            f"👁️ Entry Scanner\n"
            f"━━━━━━━━━━━━━━━\n"
            f"H4 Bias: {bias}\n"
            f"Signal: No setup found\n"
            f"Bot is watching and waiting..."
        )
    else:
        emoji = "🟢" if signal == "BUY" else "🔴"
        message = (
            f"{emoji} SIGNAL FOUND: {signal}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"H4 Bias:  {bias}\n"
            f"Price:    {details['price']}\n"
            f"EMA(20):  {details['ema20']}\n"
            f"RSI(14):  {details['rsi']}\n"
            f"Waiting for risk engine to size the trade..."
        )

    print(message)
    notify(message)

    disconnect()