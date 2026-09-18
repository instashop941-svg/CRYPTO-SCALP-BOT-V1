import os, time, traceback

print('=== CRYPTO SCALP BOT V2 STARTING ===', flush=True)
print('Python process started', flush=True)

try:
    import ccxt
    import requests
    print('Imports OK', flush=True)
except Exception as e:
    print('IMPORT ERROR:', repr(e), flush=True)
    traceback.print_exc()
    raise

SYMBOLS = [s.strip() for s in os.getenv('SYMBOLS', 'BTC/USDT:USDT,ETH/USDT:USDT,SOL/USDT:USDT,XRP/USDT:USDT,HBAR/USDT:USDT,FET/USDT:USDT,JUP/USDT:USDT,LINK/USDT:USDT,VIRTUAL/USDT:USDT').split(',') if s.strip()]
SCAN_SECONDS = max(10, int(os.getenv('SCAN_SECONDS', '20')))
COOLDOWN_SECONDS = max(60, int(os.getenv('COOLDOWN_SECONDS', '900')))
MIN_ROOM = float(os.getenv('MIN_ROOM', '0.005'))
MAX_ROOM = float(os.getenv('MAX_ROOM', '0.007'))
LEVERAGE = int(os.getenv('LEVERAGE', '30'))
TG = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
CHAT = os.getenv('TELEGRAM_CHAT_ID', '').strip()
last_sent = {}

print('Symbols:', ', '.join(SYMBOLS), flush=True)
print('Telegram configured:', bool(TG and CHAT), flush=True)
print('Chat ID configured:', CHAT if CHAT else '<empty>', flush=True)

ex = ccxt.mexc({'enableRateLimit': True, 'options': {'defaultType': 'swap'}})


def send(text):
    if not TG or not CHAT:
        print('[TG] NOT CONFIGURED', flush=True)
        print(text, flush=True)
        return False
    try:
        r = requests.post(
            f'https://api.telegram.org/bot{TG}/sendMessage',
            json={'chat_id': CHAT, 'text': text, 'parse_mode': 'HTML'},
            timeout=10,
        )
        print(f'[TG] HTTP {r.status_code}', flush=True)
        if not r.ok:
            print('[TG] RESPONSE', r.text[:500], flush=True)
            return False
        return True
    except Exception as e:
        print('[TG ERROR]', repr(e), flush=True)
        return False


def fetch(symbol, timeframe, limit):
    try:
        rows = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        return rows
    except Exception as e:
        print(f'[FETCH ERROR] {symbol} {timeframe}: {e}', flush=True)
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
        return 'NEUTRAL'
    closes = [r[4] for r in closed]
    e20 = ema(closes[-50:], 20)
    e50 = ema(closes[-60:], 50)
    return 'LONG' if e20 > e50 else 'SHORT' if e20 < e50 else 'NEUTRAL'


def detect(symbol):
    m5 = fetch(symbol, '5m', 100)
    m1 = fetch(symbol, '1m', 120)
    if not m5 or not m1 or len(m5) < 70 or len(m1) < 40:
        return

    ctx = context_5m(m5)
    d = m1[:-1]  # ignore unfinished 1m candle
    e = d[-1]
    prev = d[-5:-1]

    highs_12 = [r[2] for r in d[-13:-1]]
    lows_12 = [r[3] for r in d[-13:-1]]
    rh = max(highs_12)
    rl = min(lows_12)

    bull_sweep = (e[3] < rl and e[4] > rl) or any(r[3] < rl and r[4] > rl for r in prev)
    bear_sweep = (e[2] > rh and e[4] < rh) or any(r[2] > rh and r[4] < rh for r in prev)

    bodies = [abs(r[4] - r[1]) for r in d[-24:-4]]
    bodies_sorted = sorted(bodies)
    med = bodies_sorted[len(bodies_sorted)//2] if bodies_sorted else 0
    min_body = max(med * 1.4, e[4] * 0.0007)

    bull_disp = e[4] > e[1] and (e[4] - e[1]) >= min_body
    bear_disp = e[4] < e[1] and (e[1] - e[4]) >= min_body

    prev_high = max(r[2] for r in d[-5:-1])
    prev_low = min(r[3] for r in d[-5:-1])
    bull_bos = e[4] > prev_high
    bear_bos = e[4] < prev_low

    long_ok = ctx == 'LONG' and bull_sweep and bull_disp and bull_bos
    short_ok = ctx == 'SHORT' and bear_sweep and bear_disp and bear_bos
    if not (long_ok or short_ok):
        return

    side = 'LONG' if long_ok else 'SHORT'
    entry = float(e[4])
    sweep_level = float(rl if side == 'LONG' else rh)
    if abs(entry - sweep_level) / sweep_level > 0.0025:
        print(f'[ANTI-CHASE] {symbol} {side}', flush=True)
        return

    if side == 'LONG':
        sweep_lows = [r[3] for r in d if r[3] < rl]
        sl_base = sweep_lows[-1] if sweep_lows else min(r[3] for r in d[-8:])
        sl = sl_base * 0.9985
        future_highs = [r[2] for r in d[-50:-1] if r[2] > entry]
        tp = min(future_highs) if future_highs else entry * (1 + MAX_ROOM)
        tp = min(tp, entry * (1 + MAX_ROOM))
        room = (tp - entry) / entry
    else:
        sweep_highs = [r[2] for r in d if r[2] > rh]
        sl_base = sweep_highs[-1] if sweep_highs else max(r[2] for r in d[-8:])
        sl = sl_base * 1.0015
        future_lows = [r[3] for r in d[-50:-1] if r[3] < entry]
        tp = max(future_lows) if future_lows else entry * (1 - MAX_ROOM)
        tp = max(tp, entry * (1 - MAX_ROOM))
        room = (entry - tp) / entry

    risk = abs(entry - sl) / entry
    if room < MIN_ROOM or risk > 0.015:
        return

    key = (symbol, side, round(entry, 8))
    now = time.time()
    if now - last_sent.get(key, 0) < COOLDOWN_SECONDS:
        return
    last_sent[key] = now

    icon = '🟢' if side == 'LONG' else '🔴'
    msg = (
        f'{icon} CONFIRMED SCALP\n\n{symbol}\n\n{side}\n\n'
        f'Price: {entry:.8g}\n5m Context: {ctx}\n'
        f'Trigger: SWEEP + DISPLACEMENT + REACTION + CHoCH/BOS\n'
        f'Potential room: {room*100:.2f}%\n\n'
        f'Entry: {entry:.8g}\nSL: {sl:.8g}\nTP: {tp:.8g}\n\n'
        f'Leverage: {LEVERAGE}x\n'
        f'TP potential ROI: +{room*LEVERAGE*100:.1f}% (before fees/funding)\n'
        f'SL potential ROI: -{risk*LEVERAGE*100:.1f}% (before fees/funding)\n\nSCALP V2\n\n'
        f'<b>Трейдер Василь Павлів</b>\n'
        f'https://t.me/vasylpavliv'
    )
    print('[SIGNAL]', symbol, side, entry, flush=True)
    send(msg)


print('Connecting to MEXC...', flush=True)
try:
    ex.load_markets()
    print(f'MEXC connected. Markets loaded: {len(ex.markets)}', flush=True)
except Exception as e:
    print('[MEXC INIT ERROR]', repr(e), flush=True)
    traceback.print_exc()

print('=== SCALP BOT V2 RUNNING ===', flush=True)
while True:
    cycle_start = time.time()
    for symbol in SYMBOLS:
        try:
            detect(symbol)
        except Exception as e:
            print(f'[DETECT ERROR] {symbol}: {e}', flush=True)
    elapsed = time.time() - cycle_start
    time.sleep(max(1, SCAN_SECONDS - elapsed))
