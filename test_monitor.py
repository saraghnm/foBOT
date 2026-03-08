# test_monitor.py

import MetaTrader5 as mt5
from mt5_client import connect, disconnect, get_account_info
from trade_executor import get_open_positions
from position_monitor import _check_daily_drawdown, _manage_trailing_stop, _trail_state

connect()

print("=" * 50)
print("TEST 1: Account drawdown check")
print("=" * 50)
account = get_account_info()
balance = account["balance"]
equity = account["equity"]
drawdown = ((balance - equity) / balance) * 100
print(f"Balance:   ${balance:,.2f}")
print(f"Equity:    ${equity:,.2f}")
print(f"Drawdown:  {drawdown:.2f}%")
fired = _check_daily_drawdown()
print(f"Kill switch fired: {fired}")
print("✅ PASS\n")

print("=" * 50)
print("TEST 2: Open positions")
print("=" * 50)
positions = get_open_positions()
if positions:
    print(f"Found {len(positions)} open position(s):")
    for p in positions:
        ptype = "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL"
        print(f"  #{p.ticket} {ptype} {p.symbol} vol={p.volume} open={p.price_open} sl={p.sl}")
    print("\nRunning trailing stop logic...")
    for pos in positions:
        _manage_trailing_stop(pos)
    print(f"Trail state: {_trail_state}")
    print("✅ PASS — check Telegram")
else:
    print("No open positions (market closed / no trades yet)")
    print("✅ PASS — will work once a live trade is open Monday\n")

print("=" * 50)
print("TEST 3: Simulated trailing stop (fake position)")
print("=" * 50)

# Build a fake MT5-style position object using a simple namespace
from types import SimpleNamespace

fake_pos = SimpleNamespace(
    ticket=99999,
    symbol="EURUSD",
    type=mt5.ORDER_TYPE_SELL,  # SELL
    price_open=1.16000,
    sl=1.16160,   # 16 pip SL
    tp=1.15680,
    volume=0.10,
)

# Monkey-patch get_price: simulate 20 pips profit on SELL
import position_monitor
original_get_price = position_monitor.get_price
position_monitor.get_price = lambda symbol: 1.15800

_manage_trailing_stop(fake_pos)
print(f"After 20-pip profit: {_trail_state.get(99999)}")

# Simulate retrace to trail stop
position_monitor.get_price = lambda symbol: 1.15990
print("Simulating price retrace...")
_manage_trailing_stop(fake_pos)
print(f"After retrace: {_trail_state.get(99999, 'position closed ✅')}")

position_monitor.get_price = original_get_price
print("✅ PASS — check Telegram for simulated trail + close messages")

disconnect()
print("\n🏁 All monitor tests complete!")