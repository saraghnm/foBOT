# test_trend.py

from mt5_client import connect, disconnect
from trend_engine import get_bias, get_bias_details
from notifier import notify

if connect():
    details = get_bias_details()

    if details:
        message = (
            f"{details['emoji']} H4 Bias: {details['bias']}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"SMA(9):  {details['sma9']}\n"
            f"EMA(20): {details['ema20']}\n"
            f"Close:   {details['close']}\n"
            f"Time:    {details['time']}"
        )
        print(message)
        notify(message)
    else:
        print("Could not get bias details.")

    disconnect()