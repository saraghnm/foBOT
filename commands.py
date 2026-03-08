# commands.py
# Handles all incoming Telegram commands for the Halal Forex Bot

from notifier import notify
from mt5_client import get_account_info, get_price
from trade_executor import get_open_positions, close_trade, close_all_positions
from entry_scanner import scan_entry
from risk_engine import get_trade_parameters, get_atr
from session_guard import get_session_status, is_active_session
from news_filter import is_freeze_window, get_upcoming_events
from config import SYMBOL, RISK_PCT, MAX_POSITIONS
import MetaTrader5 as mt5

# Pause flag — set by /pause, cleared by /resume
_paused = False


def is_paused():
    return _paused


def handle_message(text):
    global _paused

    parts = text.strip().split()
    if not parts:
        return
    command = parts[0].lower()

    # ── /status ──────────────────────────────────────────────────────────────
    if command == "/status":
        account = get_account_info()
        positions = get_open_positions()
        session = get_session_status()
        frozen, news_title, news_currency = is_freeze_window()

        if account:
            equity_pct = ((account["equity"] - account["balance"]) / account["balance"]) * 100
            msg = (
                f"📊 BOT STATUS\n"
                f"━━━━━━━━━━━━━━━\n"
                f"💰 Balance:  ${account['balance']:,.2f}\n"
                f"📈 Equity:   ${account['equity']:,.2f} ({equity_pct:+.2f}%)\n"
                f"🔓 Margin:   ${account['margin_free']:,.2f} free\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🕐 Session:  {session[1]}\n"
                f"🤖 Auto-trade: {'PAUSED ⚠️' if _paused else 'ACTIVE ✅'}\n"
                f"📰 News:     {'FREEZE ⛔ — ' + news_title if frozen else 'Clear ✅'}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📂 Open positions: {len(positions)}\n"
            )

            if positions:
                for p in positions:
                    ptype = "🟢 BUY" if p.type == mt5.ORDER_TYPE_BUY else "🔴 SELL"
                    price = get_price(p.symbol)
                    pnl = p.profit
                    emoji = "✅" if pnl >= 0 else "🔻"
                    msg += (
                        f"\n{ptype} {p.symbol} #{p.ticket}\n"
                        f"  Entry: {p.price_open} | Now: {price}\n"
                        f"  SL: {p.sl} | TP: {p.tp}\n"
                        f"  {emoji} P&L: ${pnl:.2f}\n"
                    )

            notify(msg)
        else:
            notify("❌ Could not connect to MT5")

    # ── /price ───────────────────────────────────────────────────────────────
    elif command == "/price":
        symbol = parts[1].upper() if len(parts) > 1 else SYMBOL
        price = get_price(symbol)
        if price:
            notify(f"💲 {symbol}: {round(price[0], 5)}")
        else:
            notify(f"❌ Could not get price for {symbol}")

    # ── /balance ─────────────────────────────────────────────────────────────
    elif command == "/balance":
        account = get_account_info()
        if account:
            notify(
                f"💰 ACCOUNT BALANCE\n"
                f"━━━━━━━━━━━━━━━\n"
                f"Balance: ${account['balance']:,.2f}\n"
                f"Equity:  ${account['equity']:,.2f}\n"
                f"Margin:  ${account['margin_free']:,.2f} free\n"
                f"Server:  {account.get('server', 'MetaQuotes-Demo')}"
            )
        else:
            notify("❌ Could not get account info")

    # ── /signal ──────────────────────────────────────────────────────────────
    elif command == "/signal":
        notify("🔍 Scanning for signal...")
        signal, bias, details = scan_entry()

        if signal == "NONE":
            notify(
                f"👁️ No signal right now\n"
                f"H4 Bias: {bias}\n"
                f"Watching and waiting..."
            )
        else:
            params, status = get_trade_parameters(signal, details["price"])
            if params:
                emoji = "🟢" if signal == "BUY" else "🔴"
                notify(
                    f"{emoji} SIGNAL: {signal} {SYMBOL}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"Entry:  {params['entry']}\n"
                    f"SL:     {params['sl']} ({params['sl_pips']} pips)\n"
                    f"TP:     {params['tp']}\n"
                    f"Lots:   {params['lot_size']}\n"
                    f"R:R     1:2 ✅\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"Use /trade to execute"
                )
            else:
                notify(f"⚠️ Signal found but blocked: {status}")

    # ── /trade ───────────────────────────────────────────────────────────────
    elif command == "/trade":
        if _paused:
            notify("⏸ Bot is paused! Use /resume first")
            return

        if not is_active_session():
            notify("🕐 Market session is closed — no trading now")
            return

        frozen, title, currency = is_freeze_window()
        if frozen:
            notify(f"📰 News freeze active: {title} ({currency}) — trading paused")
            return

        notify("🔍 Scanning for entry signal...")
        signal, bias, details = scan_entry()

        if signal == "NONE":
            notify(f"👁️ No valid signal right now\nH4 Bias: {bias}\nBot is watching...")
            return

        params, status = get_trade_parameters(signal, details["price"])
        if not params:
            notify(f"⚠️ Trade blocked: {status}")
            return

        emoji = "🟢" if signal == "BUY" else "🔴"
        notify(f"{emoji} Placing {signal} order on {SYMBOL}...")

        ticket = place_order(
            signal=params["signal"],
            lot_size=params["lot_size"],
            entry_price=params["entry"],
            sl=params["sl"],
            tp=params["tp"],
        )

        if not ticket:
            notify("❌ Order failed — check MT5 logs")

    # ── /close <ticket> ──────────────────────────────────────────────────────
    elif command == "/close":
        if len(parts) < 2:
            notify("Usage: /close <ticket_number>\nExample: /close 12345678")
            return
        try:
            ticket = int(parts[1])
            notify(f"⚠️ Closing position #{ticket}...")
            close_trade(ticket)
        except ValueError:
            notify("❌ Invalid ticket number")

    # ── /closeall ────────────────────────────────────────────────────────────
    elif command == "/closeall":
        positions = get_open_positions()
        if not positions:
            notify("ℹ️ No open positions to close")
            return
        notify(f"⚠️ Closing all {len(positions)} position(s)...")
        close_all_positions()

    # ── /pause ───────────────────────────────────────────────────────────────
    elif command == "/pause":
        _paused = True
        notify(
            "⏸ Bot PAUSED\n"
            "No new trades will be placed.\n"
            "Existing positions are still monitored.\n"
            "Use /resume to restart."
        )

    # ── /resume ──────────────────────────────────────────────────────────────
    elif command == "/resume":
        _paused = False
        notify("▶️ Bot RESUMED — scanning for trades again")

    # ── /risk ────────────────────────────────────────────────────────────────
    elif command == "/risk":
        atr = get_atr()
        account = get_account_info()
        if account and atr:
            risk_amount = account["balance"] * (RISK_PCT / 100)
            notify(
                f"⚙️ RISK SETTINGS\n"
                f"━━━━━━━━━━━━━━━\n"
                f"Risk per trade: {RISK_PCT}%\n"
                f"Risk amount:    ${risk_amount:,.2f}\n"
                f"Max positions:  {MAX_POSITIONS}\n"
                f"Current ATR:    {atr}\n"
                f"Symbol:         {SYMBOL}"
            )
        else:
            notify("❌ Could not get risk info")

    # ── /news ────────────────────────────────────────────────────────────────
    elif command == "/news":
        frozen, title, currency = is_freeze_window()
        upcoming = get_upcoming_events(hours=24)

        if frozen:
            msg = f"⛔ NEWS FREEZE ACTIVE\n{title} ({currency})\n\n"
        else:
            msg = "✅ No freeze — trading allowed\n\n"

        if upcoming:
            msg += "📅 Upcoming HIGH impact (24h):\n━━━━━━━━━━━━━━━\n"
            for e in upcoming:
                msg += f"🔴 {e['currency']} — {e['title']}\n⏰ {e['time'].strftime('%a %H:%M UTC')}\n\n"
        else:
            msg += "📅 No high-impact events in next 24h"

        notify(msg)

    # ── /session ─────────────────────────────────────────────────────────────
    elif command == "/session":
        session = get_session_status()
        active = is_active_session()
        notify(
            f"🕐 SESSION STATUS\n"
            f"━━━━━━━━━━━━━━━\n"
            f"{session[1]}\n"
            f"Active for trading: {'✅ YES' if active else '❌ NO'}"
        )

    # ── /report ──────────────────────────────────────────────────────────────
    elif command == "/report":
        account = get_account_info()
        positions = get_open_positions()
        total_pnl = sum(p.profit for p in positions)
        atr = get_atr()

        if account:
            notify(
                f"📈 DAILY REPORT\n"
                f"━━━━━━━━━━━━━━━\n"
                f"Balance:       ${account['balance']:,.2f}\n"
                f"Equity:        ${account['equity']:,.2f}\n"
                f"Floating P&L:  ${total_pnl:,.2f}\n"
                f"Open trades:   {len(positions)}\n"
                f"ATR (M15):     {atr}\n"
                f"Symbol:        {SYMBOL}"
            )
        else:
            notify("❌ Could not generate report")

    # ── /help ────────────────────────────────────────────────────────────────
    elif command == "/help":
        notify(
            "🤖 Halal Forex Bot Commands\n"
            "━━━━━━━━━━━━━━━\n"
            "📊 MONITORING:\n"
            "/status — full bot status\n"
            "/balance — account balance\n"
            "/price [SYMBOL] — current price\n"
            "/session — market session info\n"
            "/news — upcoming high-impact events\n"
            "/risk — risk settings & ATR\n"
            "/report — daily P&L report\n"
            "\n"
            "📈 TRADING:\n"
            "/signal — scan for entry signal\n"
            "/trade — scan + execute trade\n"
            "/close <ticket> — close a position\n"
            "/closeall — close all positions\n"
            "\n"
            "⚙️ CONTROL:\n"
            "/pause — pause new trades\n"
            "/resume — resume trading\n"
            "/help — show this message"
        )

    # ── Unknown ───────────────────────────────────────────────────────────────
    else:
        notify(f"❓ Unknown command: {command}\nSend /help for all commands")