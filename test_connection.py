# test_connection.py

from mt5_client import connect, disconnect, get_candles, get_price, get_account_info

if connect():
    bid, ask = get_price("EURUSD")
    print(f"EURUSD Price — Bid: {bid} | Ask: {ask}")

    candles = get_candles("EURUSD", "H4", 5)
    print("\nLast 5 H4 candles:")
    print(candles[["time", "open", "high", "low", "close"]])

    account = get_account_info()
    print(f"\nAccount Balance: ${account['balance']:,.2f}")
    print(f"Leverage: 1:{account['leverage']}")

    disconnect()