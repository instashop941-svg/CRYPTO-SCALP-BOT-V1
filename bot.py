import os,time
import ccxt,pandas as pd,requests

SYMBOLS=[s.strip() for s in os.getenv('SYMBOLS','BTC/USDT:USDT,ETH/USDT:USDT,SOL/USDT:USDT,XRP/USDT:USDT,HBAR/USDT:USDT').split(',') if s.strip()]
LEVERAGE=30; MIN_ROOM=.005; MAX_ROOM=.007; ANTI_CHASE=.0025
SCAN=int(os.getenv('SCAN_SECONDS','20')); COOLDOWN=int(os.getenv('COOLDOWN_SECONDS','900'))
TG=os.getenv('TELEGRAM_BOT_TOKEN',''); CHAT=os.getenv('TELEGRAM_CHAT_ID',''); last={}
ex=ccxt.mexc({'enableRateLimit':True,'options':{'defaultType':'swap'}})

def fetch(s,tf,n):
    for k in range(3):
        try:return pd.DataFrame(ex.fetch_ohlcv(s,timeframe=tf,limit=n),columns=['ts','open','high','low','close','volume'])
        except Exception as e:
            if k==2: print('[FETCH]',s,tf,e)
            time.sleep(1.5*(k+1))

def send(m):
    if not TG or not CHAT: print(m); return
    try: requests.post(f'https://api.telegram.org/bot{TG}/sendMessage',json={'chat_id':CHAT,'text':m},timeout=8)
    except Exception as e: print('[TG]',e)

def ctx(df):
    d=df.iloc[:-1]
    e20=d.close.ewm(span=20).mean().iloc[-1]; e50=d.close.ewm(span=50).mean().iloc[-1]
    return 'LONG' if e20>e50 else 'SHORT' if e20<e50 else 'NEUTRAL'

def detect(s):
    m5=fetch(s,'5m',100); m1=fetch(s,'1m',120)
    if m5 is None or m1 is None or len(m5)<30 or len(m1)<40:return
    c=ctx(m5); d=m1.iloc[:-1].copy()
    e=d.iloc[-1]; prev=d.iloc[-5:-1]
    rh=d.high.iloc[-13:-1].max(); rl=d.low.iloc[-13:-1].min()
    bull_s=(e.low<rl and e.close>rl) or ((prev.low<rl)&(prev.close>rl)).any()
    bear_s=(e.high>rh and e.close<rh) or ((prev.high>rh)&(prev.close<rh)).any()
    med=(d.open-d.close).abs().iloc[-24:-4].median()
    bull_d=e.close>e.open and e.close-e.open>=max(med*1.4,e.close*.0007)
    bear_d=e.close<e.open and e.open-e.close>=max(med*1.4,e.close*.0007)
    bull_b=e.close>d.high.iloc[-5:-1].max(); bear_b=e.close<d.low.iloc[-5:-1].min()
    long_ok=c=='LONG' and bull_s and bull_d and bull_b
    short_ok=c=='SHORT' and bear_s and bear_d and bear_b
    if not(long_ok or short_ok):return
    side='LONG' if long_ok else 'SHORT'; entry=float(e.close)
    sweep_level=float(rl if side=='LONG' else rh)
    if abs(entry-sweep_level)/sweep_level>ANTI_CHASE:return
    if side=='LONG':
        lows=d.loc[d.low<rl,'low']; sl=float(lows.iloc[-1])*.9985 if len(lows) else float(d.low.iloc[-8:].min())*.9985
        highs=d.high.iloc[-50:-1]; cand=highs[highs>entry]
        tp=float(cand.min()) if len(cand) else entry*(1+MAX_ROOM); tp=min(tp,entry*(1+MAX_ROOM)); room=(tp-entry)/entry
    else:
        highs=d.loc[d.high>rh,'high']; sl=float(highs.iloc[-1])*1.0015 if len(highs) else float(d.high.iloc[-8:].max())*1.0015
        lows=d.low.iloc[-50:-1]; cand=lows[lows<entry]
        tp=float(cand.max()) if len(cand) else entry*(1-MAX_ROOM); tp=max(tp,entry*(1-MAX_ROOM)); room=(entry-tp)/entry
    risk=abs(entry-sl)/entry
    if room<MIN_ROOM or risk>.015:return
    key=(s,side,round(entry,8)); now=time.time()
    if now-last.get(key,0)<COOLDOWN:return
    last[key]=now
    send(('🟢 CONFIRMED SCALP' if side=='LONG' else '🔴 CONFIRMED SCALP')+f'''\n\n{s}\n\n{side}\n\nPrice: {entry:.8g}\n5m Context: {c}\nTrigger: SWEEP + REACTION + CHoCH/BOS\nPotential room: {room*100:.2f}%\n\nEntry: {entry:.8g}\nSL: {sl:.8g}\nTP: {tp:.8g}\n\nLeverage: {LEVERAGE}x\nTP potential ROI: +{room*LEVERAGE*100:.1f}% (before fees/funding)\nSL potential ROI: -{risk*LEVERAGE*100:.1f}% (before fees/funding)\n\nSCALP V1''')

def main():
    print('SCALP V1 started',SYMBOLS)
    while True:
        for s in SYMBOLS:
            try: detect(s)
            except Exception as e: print('[ERR]',s,e)
            time.sleep(.5)
        time.sleep(SCAN)
if __name__=='__main__':main()
