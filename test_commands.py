# test_commands.py
# Fires every command at the bot and checks Telegram output

from mt5_client import connect, disconnect
from commands import handle_message

connect()

commands = [
    "/help",
    "/balance",
    "/price",
    "/price EURUSD",
    "/session",
    "/news",
    "/risk",
    "/status",
    "/signal",
    "/report",
    "/pause",
    "/status",   # should show paused = YES
    "/resume",
    "/close 99999",       # fake ticket — should say "no position found"
    "/closeall",          # no positions — should say "nothing to close"
    "randomtext",         # unknown command
]

print(f"Firing {len(commands)} commands at Telegram...\n")
for cmd in commands:
    print(f"→ {cmd}")
    handle_message(cmd)

disconnect()
print("\n🏁 All commands sent — check Telegram!")