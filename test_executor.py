# test_executor.py

from mt5_client import connect, disconnect
from entry_scanner import scan_entry
from risk_engine import get_trade_parameters
from trade_executor import place_order, get_open_positions, close_all_positions
from notifier import notify

if connect():
    signal, bias, details = scan_entry()

    if signal == "NONE":
        notify(
            f"👁️ No signal right now\n"
            f"H4 Bias: {bias}\n"
            f"Watching and waiting..."
        )
    else:
        params, status = get_trade_parameters(signal, details["price"])

        if params:
            notify(f"🚀 Signal confirmed! Placing {signal} order...")

            ticket = place_order(
                signal    = params["signal"],
                lot_size  = params["lot_size"],
                entry_price = params["entry"],
                sl        = params["sl"],
                tp        = params["tp"],
            )

            if ticket:
                notify(f"✅ Trade live on demo! Ticket #{ticket}")

                # Show open positions
                positions = get_open_positions()
                notify(f"📊 Open positions: {len(positions)}")
        else:
            notify(f"⚠️ Trade blocked: {status}")

    disconnect()