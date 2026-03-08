# entry_scanner.py

import ta
import pandas as pd
from mt5_client import get_candles
from trend_engine import get_bias
from notifier import notify


# RSI thresholds
RSI_OVERSOLD  = 40  # buy signal threshold
RSI_OVERBOUGHT = 60  # sell signal threshold


def get_rsi(df):
    return ta.momentum.RSIIndicator(df["close"], window=14).rsi()


def get_ema20(df):
    return ta.trend.ema_indicator(df["close"], window=20)


def scan_entry():
    # Step 1 — Get H4 bias first
    bias = get_bias()

    if bias == "NEUTRAL":
        return "NONE", "NEUTRAL", None

    # Step 2 — Get M15 candles
    df = get_candles("EURUSD", "M15", 100)
    if df is None or len(df) < 21:
        notify("⚠️ Entry Scanner: Not enough M15 data!")
        return "NONE", bias, None

    # Step 3 — Calculate indicators
    df["rsi"]   = get_rsi(df)
    df["ema20"] = get_ema20(df)

    curr = df.iloc[-1]
    prev = df.iloc[-2]

    rsi   = curr["rsi"]
    price = curr["close"]
    ema20 = curr["ema20"]

    # Step 4 — Check signal conditions
    if bias == "BULLISH":
        # Look for BUY — price pulled back to EMA, RSI oversold
        price_near_ema = price <= ema20 * 1.001  # within 0.1% of EMA
        rsi_oversold   = rsi < RSI_OVERSOLD
        if price_near_ema and rsi_oversold:
            return "BUY", bias, {
                "price": round(price, 5),
                "ema20": round(ema20, 5),
                "rsi":   round(rsi, 2),
            }

    elif bias == "BEARISH":
        # Look for SELL — price pulled back to EMA, RSI overbought
        price_near_ema  = price >= ema20 * 0.999  # within 0.1% of EMA
        rsi_overbought  = rsi > RSI_OVERBOUGHT
        if price_near_ema and rsi_overbought:
            return "SELL", bias, {
                "price": round(price, 5),
                "ema20": round(ema20, 5),
                "rsi":   round(rsi, 2),
            }

    return "NONE", bias, None