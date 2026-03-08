# trend_engine.py

import ta
import pandas as pd
from mt5_client import get_candles
from notifier import notify


def get_bias():
    df = get_candles("EURUSD", "H4", 50)
    if df is None or len(df) < 21:
        notify("⚠️ Trend Engine: Not enough candle data!")
        return "NEUTRAL"

    # Calculate SMA(9) and EMA(20)
    df["sma9"]  = ta.trend.sma_indicator(df["close"], window=9)
    df["ema20"] = ta.trend.ema_indicator(df["close"], window=20)

    # Get the last two rows to detect crossover
    prev = df.iloc[-2]
    curr = df.iloc[-1]

    sma_now  = curr["sma9"]
    ema_now  = curr["ema20"]
    sma_prev = prev["sma9"]
    ema_prev = prev["ema20"]

    # Determine bias
    if sma_now > ema_now:
        bias = "BULLISH"
    elif sma_now < ema_now:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"

    return bias


def get_bias_details():
    df = get_candles("EURUSD", "H4", 50)
    if df is None or len(df) < 21:
        return None

    df["sma9"]  = ta.trend.sma_indicator(df["close"], window=9)
    df["ema20"] = ta.trend.ema_indicator(df["close"], window=20)

    curr = df.iloc[-1]
    bias = get_bias()

    emoji = "📈" if bias == "BULLISH" else "📉" if bias == "BEARISH" else "➡️"

    return {
        "bias":     bias,
        "emoji":    emoji,
        "sma9":     round(curr["sma9"],  5),
        "ema20":    round(curr["ema20"], 5),
        "close":    round(curr["close"], 5),
        "time":     curr["time"],
    }