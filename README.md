# CRYPTO SCALP BOT V5.1 — POI / LIQUIDITY

V5.1 is an audited refinement of V5 using the observed 10m examples.

Sequence:
LIQUIDITY SWEEP → POI TEST → REACTION → DISPLACEMENT → CHoCH/BOS → IMB → 0.50–0.70% MOVE

Changes from V5:
- search recent 1m sweeps over ~60 closed candles instead of ~20
- prefer the newest sweep matching the 5m EMA context
- use the first qualifying displacement after the selected sweep
- use the first POI retest instead of the latest retest
- use the first reaction after the POI retest
- unfinished 1m candle excluded
- TP1 0.50%, TP2 0.70%, structural SL unchanged
- Telegram only confirmed entries
- default leverage 30x

This does not modify V5.1 into a guaranteed predictor; it is an experimental refinement and should be validated from live logs.

Environment variables: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SYMBOLS, SCAN_SECONDS, COOLDOWN_SECONDS, TP1_PCT, TP2_PCT, MAX_RISK_PCT, MAX_CHASE_PCT, LEVERAGE, HEARTBEAT_SECONDS.
