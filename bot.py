import os, time, traceback

print("=== CRYPTO SCALP BOT V3 STARTING ===", flush=True)

try:
    import ccxt
    import requests
    print("Imports OK", flush=True)
except Exception as e:
    print("IMPORT ERROR:", repr(e), flush=True)
    raise

SYMBOLS = [s.strip() for s in os.getenv(
    "SYMBOLS",
    "BTC/USDT:USDT,ETH/USDT:USDT,SOL/USDT:USDT,XRP/USDT:USDT,"
    "HBAR/USDT:USDT,FET/USDT:USDT,JUP/USDT:USDT,LINK/USDT:USDT,VIRTUAL/USDT:USDT"
).split(",") if s.strip()]

SCAN_SECONDS = max(15, int(os.getenv("SCAN_SECONDS", "30")))
COOLDOWN_SECONDS = max(60, int(os.getenv("COOLDOWN_SECONDS", "900")))
MIN_ROOM = float(os.getenv("MIN_ROOM", "0.005"))
MAX_ROOM = float(os.getenv("MAX_ROOM", "0.007"))
LEVERAGE = int(os.getenv("LEVERAGE", "30"))
HEARTBEAT_SECONDS = max(60, int(os.getenv("HEARTBEAT_SECONDS", "300")))
TG = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT = os.getenv("TELEGRAM_CHAT_ID", "").strip()
last_sent = {}
last_heartbeat = 0.0

print("Symbols:", ", ".join(SYMBOLS), flush=True)
print("Telegram configured:", bool(TG and CHAT), flush=True)
print("Chat ID configured:", CHAT if CHAT else "<empty>", flush=True)

ex = ccxt.mexc({"enableRateLimit": True, "options": {"defaultType": "swap"}})

def send(text):
    if not TG or not CHAT:
        print("[TG] NOT CONFIGURED", flush=True)
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TG}/sendMessage",
            json={"chat_id": CHAT, "text": text, "parse_mode": "HTML",
                  "disable_web_page_preview": True},
            timeout=10,
        )
        print(f"[TG] HTTP {r.status_code}", flush=True)
        if not r.ok:
            print("[TG] RESPONSE", r.text[:500], flush=True)
            return False
        return True
    except Exception as e:
        print("[TG ERROR]", repr(e), flush=True)
        return False

def fetch(symbol, timeframe, limit):
    try:
        return ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    except Exception as e:
        print(f"[FETCH ERROR] {symbol} {timeframe}: {e}", flush=True)
        return None

def ema(values, period):
    if not values:
        return 0.0
    k = 2.0 / (period + 1)
    x = float(values[0])
    for v in values[1:]:
        x = float(v) * k + x * (1 - k)
    return x

def context_5m(rows):
    closed = rows[:-1]
    if len(closed) < 60:
        return "NEUTRAL"
    closes = [r[4] for r in closed]
    e20 = ema(closes[-50:], 20)
    e50 = ema(closes[-60:], 50)
    return "LONG" if e20 > e50 else "SHORT" if e20 < e50 else "NEUTRAL"

def detect(symbol):
    m5 = fetch(symbol, "5m", 120)
    m1 = fetch(symbol, "1m", 150)
    if not m5 or not m1 or len(m5) < 75 or len(m1) < 45:
        return None

    ctx = context_5m(m5)
    d = m1[:-1]
    e = d[-1]
    prev4 = d[-5:-1]

    highs = [r[2] for r in d[-13:-1]]
    lows = [r[3] for r in d[-13:-1]]
    rh, rl = max(highs), min(lows)

    bull_sweep = (e[3] < rl and e[4] > rl) or any(r[3] < rl and r[4] > rl for r in prev4)
    bear_sweep = (e[2] > rh and e[4] < rh) or any(r[2] > rh and r[4] < rh for r in prev4)

    bodies = sorted(abs(r[4] - r[1]) for r in d[-24:-4])
    med = bodies[len(bodies)//2] if bodies else 0.0
    min_body = max(med * 1.4, e[4] * 0.0007)
    bull_disp = e[4] > e[1] and (e[4] - e[1]) >= min_body
    bear_disp = e[4] < e[1] and (e[1] - e[4]) >= min_body

    bull_reaction = e[4] > e[1] and e[4] > rl
    bear_reaction = e[4] < e[1] and e[4] < rh

    prev_high = max(r[2] for r in prev4)
    prev_low = min(r[3] for r in prev4)
    bull_bos = e[4] > prev_high
    bear_bos = e[4] < prev_low

    long_ok = ctx == "LONG" and bull_sweep and bull_reaction and bull_disp and bull_bos
    short_ok = ctx == "SHORT" and bear_sweep and bear_reaction and bear_disp and bear_bos
    if not (long_ok or short_ok):
        return None

    side = "LONG" if long_ok else "SHORT"
    entry = float(e[4])
    sweep_level = float(rl if side == "LONG" else rh)
    chase = abs(entry - sweep_level) / sweep_level
    if chase > 0.0025:
        print(f"[ANTI-CHASE] {symbol} {side} chase={chase*100:.2f}%", flush=True)
        return None

    if side == "LONG":
        sweep_lows = [r[3] for r in d[-13:] if r[3] < rl]
        sweep_low = min(sweep_lows, default=rl)
        sl = sweep_low * 0.9985
        candidates = [r[2] for r in d[-60:-1] if r[2] > entry and r[2] > rh]
        tp = min(candidates) if candidates else entry * (1 + MAX_ROOM)
        tp = min(tp, entry * (1 + MAX_ROOM))
        room = (tp - entry) / entry
    else:
        sweep_highs = [r[2] for r in d[-13:] if r[2] > rh]
        sweep_high = max(sweep_highs, default=rh)
        sl = sweep_high * 1.0015
        candidates = [r[3] for r in d[-60:-1] if r[3] < entry and r[3] < rl]
        tp = max(candidates) if candidates else entry * (1 - MAX_ROOM)
        tp = max(tp, entry * (1 - MAX_ROOM))
        room = (entry - tp) / entry

    risk = abs(entry - sl) / entry
    if room < MIN_ROOM:
        print(f"[FILTER ROOM] {symbol} {side} room={room*100:.2f}%", flush=True)
        return None
    if risk > 0.015:
        print(f"[FILTER RISK] {symbol} {side} risk={risk*100:.2f}%", flush=True)
        return None
    if risk > 0 and room / risk < 1.15:
        print(f"[FILTER RR] {symbol} {side} RR={room/risk:.2f}", flush=True)
        return None

    key = (symbol, side, round(entry, 8))
    now = time.time()
    if now - last_sent.get(key, 0) < COOLDOWN_SECONDS:
        return None
    last_sent[key] = now

    icon = "🟢" if side == "LONG" else "🔴"
    msg = (
        f"{icon} <b>CONFIRMED SCALP V3</b>\n\n"
        f"<b>{symbol}</b>\n\n<b>{side}</b>\n\n"
        f"Price: {entry:.8g}\n5m Context: {ctx}\n"
        f"Trigger: SWEEP + REACTION + DISPLACEMENT + CHoCH/BOS\n"
        f"Potential room: {room*100:.2f}%\n\n"
        f"Entry: {entry:.8g}\nSL: {sl:.8g}\nTP: {tp:.8g}\n\n"
        f"Leverage: {LEVERAGE}x\n"
        f"TP potential ROI: +{room*LEVERAGE*100:.1f}% (before fees/funding)\n"
        f"SL potential ROI: -{risk*LEVERAGE*100:.1f}% (before fees/funding)\n\n"
        f"<b>SCALP V3</b>\n\n<b>Трейдер Василь Павлів</b>\n"
        f"https://t.me/vasylpavliv"
    )
    print(f"[SIGNAL] {symbol} {side} entry={entry:.8g} tp={tp:.8g} sl={sl:.8g}", flush=True)
    send(msg)
    return True

def heartbeat():
    global last_heartbeat
    now = time.time()
    if now - last_heartbeat >= HEARTBEAT_SECONDS:
        last_heartbeat = now
        print(f"[HEARTBEAT] Scalp V3 alive | symbols={len(SYMBOLS)} | scan={SCAN_SECONDS}s", flush=True)

print("Connecting to MEXC...", flush=True)
try:
    ex.load_markets()
    print(f"MEXC connected. Markets loaded: {len(ex.markets)}", flush=True)
except Exception as e:
    print("[MEXC INIT ERROR]", repr(e), flush=True)
    traceback.print_exc()
    raise

print("=== SCALP BOT V3 RUNNING ===", flush=True)

while True:
    cycle_start = time.time()
    for symbol in SYMBOLS:
        try:
            detect(symbol)
        except Exception as e:
            print(f"[DETECT ERROR] {symbol}: {e}", flush=True)
            traceback.print_exc()

    heartbeat()
    elapsed = time.time() - cycle_start
    sleep_for = max(1, SCAN_SECONDS - elapsed)
    print(f"[CYCLE] completed in {elapsed:.1f}s | sleep {sleep_for:.1f}s", flush=True)
    time.sleep(sleep_for)
