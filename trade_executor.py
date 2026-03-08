# trade_executor.py

import MetaTrader5 as mt5
from config import SYMBOL, MAGIC
from notifier import notify


    
    
def place_order(signal, lot_size, entry_price, sl, tp):
    # Order type
    order_type = mt5.ORDER_TYPE_BUY if signal == "BUY" else mt5.ORDER_TYPE_SELL

    # Get current price
    tick = mt5.symbol_info_tick(SYMBOL)
    if tick is None:
        notify("❌ Could not get current price!")
        return None

    price = tick.ask if signal == "BUY" else tick.bid

    # Build order request
    request = {
        "action":       mt5.TRADE_ACTION_DEAL,
        "symbol":       SYMBOL,
        "volume":       float(lot_size),
        "type":         order_type,
        "price":        price,
        "sl":           float(sl),
        "tp":           float(tp),
        "deviation":    10,
        "magic":        MAGIC,
        "comment":      "HalalForexBot",
        "type_time":    mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    # Send order
    result = mt5.order_send(request)

    if result is None:
        notify(f"❌ Order failed — no response from MT5!")
        return None

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        notify(
            f"❌ Order failed!\n"
            f"Error code: {result.retcode}\n"
            f"Comment: {result.comment}"
        )
        return None

    # Success!
    emoji = "🟢" if signal == "BUY" else "🔴"
    notify(
        f"{emoji} ORDER PLACED!\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Symbol:   {SYMBOL}\n"
        f"Signal:   {signal}\n"
        f"Lots:     {lot_size}\n"
        f"Entry:    {price}\n"
        f"SL:       {sl}\n"
        f"TP:       {tp}\n"
        f"Ticket:   #{result.order}"
    )
    return result.order


def close_trade(ticket):
    # Get position details
    positions = mt5.positions_get(ticket=ticket)
    if not positions:
        notify(f"⚠️ No position found for ticket #{ticket}")
        return False

    position  = positions[0]
    symbol    = position.symbol
    lot_size  = position.volume
    pos_type  = position.type

    # Close by opposite order
    close_type = mt5.ORDER_TYPE_SELL if pos_type == 0 else mt5.ORDER_TYPE_BUY
    tick       = mt5.symbol_info_tick(symbol)
    price      = tick.bid if pos_type == 0 else tick.ask

    request = {
        "action":       mt5.TRADE_ACTION_DEAL,
        "symbol":       symbol,
        "volume":       lot_size,
        "type":         close_type,
        "position":     ticket,
        "price":        price,
        "deviation":    10,
        "magic":        MAGIC,
        "comment":      "HalalForexBot_Close",
        "type_time":    mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(request)

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        notify(
            f"❌ Close failed!\n"
            f"Ticket: #{ticket}\n"
            f"Error: {result.retcode}"
        )
        return False

    # Calculate P&L
    pnl = position.profit
    emoji = "✅" if pnl >= 0 else "❌"

    notify(
        f"{emoji} POSITION CLOSED\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Ticket:  #{ticket}\n"
        f"Symbol:  {symbol}\n"
        f"P&L:     ${pnl:.2f}"
    )
    return True


def get_open_positions():
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions is None:
        return []
    return list(positions)


def close_all_positions():
    positions = get_open_positions()
    if not positions:
        notify("ℹ️ No open positions to close")
        return

    notify(f"⚠️ Closing all {len(positions)} position(s)...")
    for pos in positions:
        close_trade(pos.ticket)