# CRYPTO SCALP BOT V4

Based on Scalp V3, with more practical scalp room and detailed filter diagnostics.

## Core
- 5m EMA20/EMA50 context
- closed 1m candles only
- liquidity sweep
- reaction
- displacement
- local CHoCH/BOS
- anti-chase <= 0.25%
- minimum potential room 0.35%
- maximum potential room 0.70%
- risk <= 1.50%
- RR >= 1.15
- TP from recent local liquidity when available
- cooldown 15 minutes per symbol/side/entry
- Telegram only for confirmed entries
- default leverage 30x

## Diagnostics
Railway logs now show which confirmation stage filters a candidate:
- FILTER SWEEP
- FILTER REACTION
- FILTER DISPLACEMENT
- FILTER BOS
- FILTER ROOM
- FILTER RISK
- FILTER RR
- ANTI-CHASE
- SIGNAL

This is intended to make it clear why the bot is quiet instead of silently returning.

## Environment variables
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- SYMBOLS
- SCAN_SECONDS (default 30)
- COOLDOWN_SECONDS (default 900)
- MIN_ROOM (default 0.0035 = 0.35%)
- MAX_ROOM (default 0.007 = 0.70%)
- LEVERAGE (default 30)
- HEARTBEAT_SECONDS (default 300)
