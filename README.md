# CRYPTO SCALP BOT V3

Fixed Scalp V2 main loop and added transparent runtime diagnostics.

Core:
5m context -> 1m closed-candle trigger -> sweep -> reaction -> displacement -> local BOS -> fresh entry.

Filters:
- anti-chase
- minimum room 0.50%
- maximum room 0.70%
- risk <= 1.50%
- RR >= 1.15
- SL beyond sweep
- TP from recent liquidity when available
- Telegram only confirmed signals
- default leverage 30x

Important Railway variables:
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID

Optional:
SYMBOLS
SCAN_SECONDS=30
COOLDOWN_SECONDS=900
MIN_ROOM=0.005
MAX_ROOM=0.007
LEVERAGE=30
HEARTBEAT_SECONDS=300
