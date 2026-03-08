# position_monitor.py
# Monitors open positions, manages trailing stops, and enforces the daily drawdown kill switch

import time
import MetaTrader5 as mt5
from mt5_client import get_account_info, get_price
from trade_executor import close_trade, get_open_positions
from notifier import notify
from config import DAILY_DRAWDOWN_LIMIT

# Track trailing stop state per ticket
# { ticket: { "trail_activated": bool, "highest_profit_pips": float, "trail_stop_pips": float } }
_trail_state = {}

POLL_INTERVAL = 30  # seconds between checks
_running = False


def _pips(symbol, price_diff):
    """Convert price difference to pips."""
    if "JPY" in symbol:
        return abs(price_diff) / 0.01
    return abs(price_diff) / 0.0001


def _check_daily_drawdown():
    """
    Kill switch: if equity drops 3% below balance, close ALL positions.
    Returns True if kill switch fired.
    """
    account = get_account_info()
    if not account:
        return False

    balance = account["balance"]
    equity = account["equity"]
    drawdown_pct = ((balance - equity) / balance) * 100
    max_drawdown = DAILY_DRAWDOWN_LIMIT

    if drawdown_pct >= max_drawdown:
        notify(
            f"🚨 KILL SWITCH ACTIVATED\n"
            f"Drawdown: {drawdown_pct:.2f}% ≥ {max_drawdown}% limit\n"
            f"Balance: ${balance:,.2f} | Equity: ${equity:,.2f}\n"
            f"Closing all positions now..."
        )
        positions = get_open_positions()
        for pos in positions:
            close_trade(pos.ticket)  # MT5 object — dot notation
        _trail_state.clear()
        return True

    return False


def _manage_trailing_stop(position):
    """
    Trailing stop logic:
    - Activates when profit pips >= SL pips (1:1 R:R)
    - Trails 1x SL distance behind highest profit
    - Closes trade if price retraces to trail level
    """
    # MT5 position object — dot notation throughout
    ticket     = position.ticket
    symbol     = position.symbol
    trade_type = "buy" if position.type == mt5.ORDER_TYPE_BUY else "sell"
    open_price = position.price_open
    sl         = position.sl

    current_price = get_price(symbol)
    if not current_price:
        return

    # SL distance in pips
    sl_pips = _pips(symbol, abs(open_price - sl)) if sl else 15.0

    # Current profit in pips
    if trade_type == "buy":
        profit_pips = _pips(symbol, current_price - open_price)
        in_profit = current_price > open_price
    else:
        profit_pips = _pips(symbol, open_price - current_price)
        in_profit = current_price < open_price

    # Initialize state for this ticket
    if ticket not in _trail_state:
        _trail_state[ticket] = {
            "trail_activated": False,
            "highest_profit_pips": profit_pips if in_profit else 0,
            "trail_stop_pips": None,
        }

    state = _trail_state[ticket]

    # Update highest profit
    if in_profit and profit_pips > state["highest_profit_pips"]:
        state["highest_profit_pips"] = profit_pips

    # Activate trailing stop at 1:1 R:R
    if not state["trail_activated"] and in_profit and profit_pips >= sl_pips:
        state["trail_activated"] = True
        state["trail_stop_pips"] = profit_pips - sl_pips
        notify(
            f"📈 Trailing stop ACTIVATED\n"
            f"{'🟢 BUY' if trade_type == 'buy' else '🔴 SELL'} {symbol} #{ticket}\n"
            f"Profit: {profit_pips:.1f} pips | Trail buffer: {sl_pips:.1f} pips"
        )

    # If trailing is active, update and check exit
    if state["trail_activated"]:
        new_trail = state["highest_profit_pips"] - sl_pips
        if new_trail > state["trail_stop_pips"]:
            state["trail_stop_pips"] = new_trail

        if not in_profit or profit_pips <= state["trail_stop_pips"]:
            notify(
                f"🔴 Trailing stop hit!\n"
                f"{'🟢 BUY' if trade_type == 'buy' else '🔴 SELL'} {symbol} #{ticket}\n"
                f"Closing at {profit_pips:.1f} pips profit..."
            )
            success = close_trade(ticket)  # single argument — ticket only
            if success:
                _trail_state.pop(ticket, None)


def start_monitor():
    """Main loop. Run in a background thread from bot.py."""
    global _running
    _running = True
    notify("👁️ Position monitor started")

    while _running:
        try:
            if _check_daily_drawdown():
                notify("🛑 Kill switch fired — monitor pausing for 5 minutes")
                time.sleep(300)
                continue

            positions = get_open_positions()
            for pos in positions:
                _manage_trailing_stop(pos)

            # Clean up trail state for positions that closed externally
            open_tickets = {pos.ticket for pos in positions}
            for t in list(_trail_state):
                if t not in open_tickets:
                    _trail_state.pop(t, None)

        except Exception as e:
            notify(f"⚠️ Monitor error: {e}")

        time.sleep(POLL_INTERVAL)


def stop_monitor():
    global _running
    _running = False
    notify("🛑 Position monitor stopped")


if __name__ == "__main__":
    from mt5_client import connect, disconnect

    connect()
    account = get_account_info()
    balance = account["balance"]
    equity = account["equity"]
    drawdown = ((balance - equity) / balance) * 100
    print(f"Balance: ${balance:,.2f} | Equity: ${equity:,.2f} | Drawdown: {drawdown:.2f}%")

    positions = get_open_positions()
    if positions:
        print(f"\n{len(positions)} open position(s):")
        for p in positions:
            ptype = "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL"
            print(f"  #{p.ticket} {ptype} {p.symbol} @ {p.price_open} | SL: {p.sl} | Vol: {p.volume}")
        print("\nRunning one monitor cycle...")
        if not _check_daily_drawdown():
            for pos in positions:
                _manage_trailing_stop(pos)
        print("✅ Done — check Telegram")
    else:
        print("No open positions (market closed / no trades yet)")
        print("✅ Monitor logic loaded OK")

    disconnect()