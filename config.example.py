# config.example.py
# Copy this file, rename it to config.py, and fill in your credentials
# NEVER push config.py to git — it's in .gitignore

TELEGRAM_TOKEN = "your_telegram_bot_token_here"
TELEGRAM_CHAT_ID = "your_telegram_chat_id_here"

# MT5 Credentials
MT5_LOGIN = 0  # your MT5 login number
MT5_PASSWORD = "your_mt5_password_here"
MT5_SERVER = "MetaQuotes-Demo"  # or your broker's server name

# Trading Settings
SYMBOL = "EURUSD"
RISK_PCT = 1.5          # risk per trade as % of balance
MAX_POSITIONS = 2       # maximum simultaneous open trades
DAILY_DRAWDOWN_LIMIT = 3.0  # bot shuts off if daily loss exceeds this %
MAGIC = 20260305        # unique ID to identify our bot's trades