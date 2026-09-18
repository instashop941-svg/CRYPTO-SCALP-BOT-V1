# Crypto Signal Bot V7.4 AUDITED

MEXC Futures Telegram signal scanner.

## Logic
LIQUIDITY → SWEEP → DISPLACEMENT/REACTION → CHoCH/BOS → ROOM CHECK → CONFIRMED

- 🟡 SETUP and 🟠 TRIGGER are calculated internally for the confirmation logic and are not sent to the Telegram group.
- 🟢 CONFIRMED ENTRY: the only signal stage sent to the Telegram group; requires the core sequence, chronological/recent events, higher-timeframe context, anti-chase, and a real opposing swing target with at least 0.70% price room.
- FVG/retest are not mandatory for confirmation.
- The still-forming candle is excluded.
- No synthetic TP is used for CONFIRMED entries.
- SETUP/TRIGGER can still appear in Railway logs for diagnostics; they are not Telegram group alerts.
- Fast scan: every 5 minutes by default.
- Default leverage: 30x.
- No automatic trading.

## Environment variables
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- LEVERAGE (default 30)
- FAST_SECONDS (default 300)
- MIN_MOVE_PCT (default 0.7)
- MAX_CHASE_PCT (default 0.45)
- COOLDOWN (default 1800)
- PAUSE (default 1.5)
- SYMBOLS (optional override)

## Railway
Start command is defined in both `Procfile` and `Dockerfile`:
- `worker: python bot.py`
- `python bot.py`

Keep Telegram variables in Railway Variables. Do not put tokens in the repository.
