# mt5_client.py

import MetaTrader5 as mt5
import pandas as pd
from config import MT5_LOGIN, MT5_PASSWORD, MT5_SERVER, SYMBOL
from notifier import notify


def connect():
    if not mt5.initialize():
        notify("❌ MT5 failed to initialize!")
        return False

    authorized = mt5.login(
        login=MT5_LOGIN,
        password=MT5_PASSWORD,
        server=MT5_SERVER
    )

    if not authorized:
        notify(f"❌ MT5 login failed! Error: {mt5.last_error()}")
        mt5.shutdown()
        return False

    account = mt5.account_info()
    notify(
        f"✅ MT5 Connected!\n"
        f"👤 Name: {account.name}\n"
        f"💰 Balance: ${account.balance:,.2f}\n"
        f"🏦 Server: {MT5_SERVER}"
    )
    return True


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