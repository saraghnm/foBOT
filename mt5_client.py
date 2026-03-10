# mt5_client.py

import MetaTrader5 as mt5
import pandas as pd
import time
from config import MT5_LOGIN, MT5_PASSWORD, MT5_SERVER, SYMBOL
from notifier import notify

MT5_PATH = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
MAX_RETRIES = 5


def connect():
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"🔄 MT5 connection attempt {attempt}/{MAX_RETRIES}...")

        # Try initialize with full path and credentials
        result = mt5.initialize(
            path=MT5_PATH,
            login=MT5_LOGIN,
            password=MT5_PASSWORD,
            server=MT5_SERVER
        )

        if result:
            account = mt5.account_info()
            if account:
                notify(
                    f"✅ MT5 Connected!\n"
                    f"👤 Name: {account.name}\n"
                    f"💰 Balance: ${account.balance:,.2f}\n"
                    f"🏦 Server: {MT5_SERVER}\n"
                    f"🤖 Autotrading: {'✅' if mt5.terminal_info().trade_allowed else '❌'}"
                )
                return True

        error = mt5.last_error()
        print(f"⚠️ Attempt {attempt} failed: {error}")
        mt5.shutdown()

        if attempt < MAX_RETRIES:
            wait = attempt * 10  # 10s, 20s, 30s, 40s
            print(f"⏳ Waiting {wait}s before retry...")
            time.sleep(wait)

    notify(f"❌ MT5 failed after {MAX_RETRIES} attempts!\nLast error: {mt5.last_error()}")
    return False


def disconnect():
    mt5.shutdown()
    print("MT5 disconnected.")


def get_candles(symbol, timeframe, n=100):
    tf_map = {
        "M15": mt5.TIMEFRAME_M15,
        "H1":  mt5.TIMEFRAME_H1,
        "H4":  mt5.TIMEFRAME_H4,
    }
    rates = mt5.copy_rates_from_pos(symbol, tf_map[timeframe], 0, n)
    if rates is None:
        return None
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df


def get_price(symbol):
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return None, None
    return tick.bid, tick.ask


def get_account_info():
    account = mt5.account_info()
    if account is None:
        return None
    return {
        "balance": account.balance,
        "equity": account.equity,
        "margin_free": account.margin_free,
        "leverage": account.leverage,
    }
