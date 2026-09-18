# Crypto Scalp Bot V1

Separate experimental scalp bot. Does NOT modify V7.4.

5m context -> 1m trigger: LIQUIDITY -> SWEEP -> REACTION/DISPLACEMENT -> CHoCH/BOS -> FRESH ENTRY -> TP.

- Minimum potential room: 0.50%
- Target room: up to 0.70%
- 30x leverage in signals
- Anti-chase filter
- SL beyond sweep/local liquidity
- Signal-only; manual execution
- Unfinished 1m candle excluded
- Cooldown per event

Environment: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SYMBOLS, SCAN_SECONDS
