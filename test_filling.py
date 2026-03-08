# test_filling.py

import MetaTrader5 as mt5
from mt5_client import connect, disconnect

if connect():
    info = mt5.symbol_info("EURUSD")
    print(f"Filling mode value: {info.filling_mode}")
    
    # Try all modes and print which ones are supported
    modes = {
        "FILLING_FOK":    mt5.ORDER_FILLING_FOK,
        "FILLING_IOC":    mt5.ORDER_FILLING_IOC,
        "FILLING_RETURN": mt5.ORDER_FILLING_RETURN,
    }
    
    for name, mode in modes.items():
        request = {
            "action":       mt5.TRADE_ACTION_DEAL,
            "symbol":       "EURUSD",
            "volume":       0.01,
            "type":         mt5.ORDER_TYPE_SELL,
            "price":        mt5.symbol_info_tick("EURUSD").bid,
            "sl":           0.0,
            "tp":           0.0,
            "deviation":    10,
            "magic":        12345,
            "comment":      "test",
            "type_time":    mt5.ORDER_TIME_GTC,
            "type_filling": mode,
        }
        result = mt5.order_check(request)
        print(f"{name}: retcode = {result.retcode} — {result.comment}")
    
    disconnect()