# risk_engine.py

import ta
import MetaTrader5 as mt5
from mt5_client import get_candles, get_account_info
from notifier import notify
from config import RISK_PCT, MAX_POSITIONS, DAILY_DRAWDOWN_LIMIT, SYMBOL


def get_atr(period=14):
    df = get_candles(SYMBOL, "M15", 100)
    if df is None:
        return None
    atr = ta.volatility.AverageTrueRange(
        df["high"], df["low"], df["close"], window=period
    ).average_true_range()
    return round(atr.iloc[-1], 5)


def get_pip_value():
    # For EURUSD — 1 pip = 0.0001
    # 1 standard lot = 100,000 units
    # Pip value per lot = $10
    return 10.0


def calculate_lot_size(sl_pips):
    account = get_account_info()
    if account is None:
        return None

    balance      = account["balance"]
    risk_amount  = balance * (RISK_PCT / 100)
    pip_value    = get_pip_value()
    lot_size     = risk_amount / (sl_pips * pip_value)

    # Round to 2 decimal places, min 0.01, max 1.0 for safety
    lot_size = max(round(lot_size, 2), 0.01)
    lot_size = min(lot_size, 0.10)  # cap at 1 lot for safety
    return lot_size


def calculate_sl_tp(signal, entry_price, atr_multiplier=1.5):
    atr = get_atr()
    if atr is None:
        return None, None, None

    sl_distance = round(atr * atr_multiplier, 5)
    tp_distance = round(sl_distance * 2, 5)  # 2:1 reward:risk

    if signal == "BUY":
        sl = round(entry_price - sl_distance, 5)
        tp = round(entry_price + tp_distance, 5)
    else:  # SELL
        sl = round(entry_price + sl_distance, 5)
        tp = round(entry_price - tp_distance, 5)

    # Convert SL distance to pips
    sl_pips = round(sl_distance / 0.0001, 1)

    return sl, tp, sl_pips


def check_max_positions():
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions is None:
        return True
    return len(positions) < MAX_POSITIONS


def check_daily_drawdown(daily_pnl):
    account = get_account_info()
    if account is None:
        return False
    balance     = account["balance"]
    drawdown_pct = abs(daily_pnl / balance * 100)
    return drawdown_pct < DAILY_DRAWDOWN_LIMIT


def get_trade_parameters(signal, entry_price):
    # Check max positions
    if not check_max_positions():
        return None, "Max positions reached"

    # Calculate SL, TP, pips
    sl, tp, sl_pips = calculate_sl_tp(signal, entry_price)
    if sl is None:
        return None, "Could not calculate SL/TP"

    # Calculate lot size
    lot_size = calculate_lot_size(sl_pips)
    if lot_size is None:
        return None, "Could not calculate lot size"

    atr = get_atr()

    return {
        "signal":    signal,
        "entry":     entry_price,
        "sl":        sl,
        "tp":        tp,
        "sl_pips":   sl_pips,
        "lot_size":  lot_size,
        "atr":       atr,
        "risk_pct":  RISK_PCT,
    }, "OK"