# CRYPTO SCALP BOT V5 — POI / LIQUIDITY

Based on Scalp V4, redesigned around the VIRTUALUSDT-style sequence:

LIQUIDITY SWEEP → POI TEST → REACTION → DISPLACEMENT → CHoCH/BOS → IMB → 0.50–0.70% MOVE

## Core
- MEXC Futures via ccxt
- 1m closed candles for trigger
- 5m EMA20/EMA50 context
- SSL/BSL liquidity sweep
- POI detection from the origin candle of the displacement move
- POI retest required after sweep
- reaction required after POI test
- displacement required
- local CHoCH/BOS required
- fresh 3-candle IMB/FVG required after displacement
- anti-chase <= 0.25%
- TP1 = 0.50%
- TP2 = 0.70%
- liquidity-aware SL beyond the sweep / POI invalidation, not a fixed tight stop
- no RR filter: the strategy prioritizes the 0.50–0.70% scalp target while the SL is structural
- maximum structural risk 2.50% by default
- Telegram only confirmed entries
- default leverage 30x

## Important
A wide structural SL does NOT mean risking the same amount of capital as a tight SL. Position sizing should be reduced separately when the structural SL is wider.

## Railway environment variables
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- SYMBOLS
- SCAN_SECONDS (default 30)
- COOLDOWN_SECONDS (default 900)
- TP1_PCT (default 0.005)
- TP2_PCT (default 0.007)
- MAX_RISK_PCT (default 0.025)
- MAX_CHASE_PCT (default 0.0025)
- LEVERAGE (default 30)
- HEARTBEAT_SECONDS (default 300)
