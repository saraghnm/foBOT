# test_risk.py

from mt5_client import connect, disconnect
from entry_scanner import scan_entry
from risk_engine import get_trade_parameters
from notifier import notify

if connect():
    signal, bias, details = scan_entry()

    if signal == "NONE":
        notify(
            f"👁️ No signal right now\n"
            f"H4 Bias: {bias}\n"
            f"Bot watching and waiting..."
        )
    else:
        params, status = get_trade_parameters(signal, details["price"])

        if params:
            emoji = "🟢" if signal == "BUY" else "🔴"
            message = (
                f"{emoji} TRADE READY: {signal} EURUSD\n"
                f"━━━━━━━━━━━━━━━\n"
                f"Entry:    {params['entry']}\n"
                f"SL:       {params['sl']} ({params['sl_pips']} pips)\n"
                f"TP:       {params['tp']}\n"
                f"Lot Size: {params['lot_size']}\n"
                f"ATR:      {params['atr']}\n"
                f"Risk:     {params['risk_pct']}% of balance\n"
                f"━━━━━━━━━━━━━━━\n"
                f"R:R = 1:2 ✅"
            )
        else:
            message = f"⚠️ Trade blocked: {status}"

        print(message)
        notify(message)

    disconnect()