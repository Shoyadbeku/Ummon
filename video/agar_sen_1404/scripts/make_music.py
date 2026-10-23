# Procedural ambient score: Hijaz-mode drone/pad, Karplus-Strong "dutar" plucks, soft frame drum.
import numpy as np, sys, wave
SR = 44100; DUR = float(sys.argv[1]); N = int(SR * DUR)
rng = np.random.default_rng(7); t = np.arange(N) / SR
L = np.zeros(N); R = np.zeros(N)
base = 146.83  # D3
hijaz = [0, 1, 4, 5, 7, 8, 10, 12]  # D Eb F# G A Bb C D
f = lambda semi: base * 2 ** (semi / 12)

# Drone: D + A with slow beating and filtered noise air
drone = sum(np.sin(2*np.pi*f(s)*t*(1+d)) * a for s, d, a in [(-12,0,.5),(-12,.0015,.35),(-5,0,.25),(0,.001,.18)])
drone *= 0.5 + 0.15*np.sin(2*np.pi*t/23)
L += drone*.22; R += drone*.22

# Pad chords that change every 16s (Dm-ish / Eb / Gm / A) built from Hijaz notes
chords = [[0,7,12,15],[1,5,8,13],[5,10,14,17],[7,13,16,19]]
seg = 16.0
for i in range(int(DUR/seg)+1):
    st = int(i*seg*SR); en = min(N, int((i+1.4)*seg*SR))
    if st >= N: break
    tt = np.arange(en-st)/SR; env = np.sin(np.pi*np.clip(tt/((en-st)/SR),0,1))**2
    sig = sum(np.sin(2*np.pi*f(s)*tt + np.sin(2*np.pi*0.2*tt)*0.3) + 0.3*np.sin(4*np.pi*f(s)*tt) for s in chords[i % 4])
    pan = 0.5 + 0.3*np.sin(i)
    L[st:en] += sig*env*.05*(1-pan+.5); R[st:en] += sig*env*.05*(pan+.5)

# Karplus-Strong plucks (dutar-like)
def pluck(freq, dur=2.2, bright=.5):
    n = int(SR*dur); p = int(SR/freq); buf = rng.uniform(-1,1,p); out = np.zeros(n)
    for k in range(n):
        out[k] = buf[k % p]; buf[k % p] = 0.996*(bright*buf[k % p] + (1-bright)*buf[(k+1) % p]) if True else 0
    return out * np.exp(-np.arange(n)/SR*1.2)
cache = {}
beat = 60/72  # 72 bpm
pattern = [0, None, 7, 5, None, 4, 5, None, 1, None, 0, None, 4, 5, 7, None]
k = 0; tm = 8.0
while tm < DUR - 6:
    phrase = (int(tm // (beat*16))) % 4
    s = pattern[k % 16]
    if s is not None and rng.random() < .8:
        note = hijaz[(hijaz.index(s) + [0,2,-1,1][phrase]) % len(hijaz)] if s in hijaz else s
        key = note
        if key not in cache: cache[key] = pluck(f(note+12))
        x = cache[key]*(.10 + .04*rng.random()); st = int(tm*SR); en = min(N, st+len(x))
        pan = .3 + .4*rng.random(); L[st:en] += x[:en-st]*(1.2-pan); R[st:en] += x[:en-st]*(.2+pan)
    tm += beat/2; k += 1

# Soft frame drum (doira): dum on 1, tak on 3
def dum(n=int(SR*.5)):
    tt = np.arange(n)/SR; return np.sin(2*np.pi*(70+60*np.exp(-tt*30))*tt)*np.exp(-tt*7)
def tak(n=int(SR*.15)):
    tt = np.arange(n)/SR; return rng.uniform(-1,1,n)*np.exp(-tt*40)*.5 + np.sin(2*np.pi*330*tt)*np.exp(-tt*35)*.4
D, T = dum(), tak(); tm = 16.0; bar = beat*4; i = 0
while tm < DUR - 10:
    for off, x, g in [(0,D,.20),(beat*1.5,T,.05),(beat*2,D,.12),(beat*3,T,.07),(beat*3.5,T,.04)]:
        st = int((tm+off)*SR); en = min(N, st+len(x)); L[st:en] += x[:en-st]*g; R[st:en] += x[:en-st]*g
    tm += bar; i += 1

# Simple stereo reverb (multi-tap feedback delays)
def verb(x):
    y = x.copy()
    for d, g in [(0.031,.35),(0.047,.3),(0.071,.25),(0.113,.2),(0.167,.15),(0.241,.1)]:
        s = int(d*SR); z = np.zeros_like(x); z[s:] = x[:-s]*g; y += z
    return y
L, R = verb(L), verb(R[::-1])[::-1]*0 + verb(R)
fade = np.minimum(1, np.minimum(t/4, (DUR-t)/6)); L *= fade; R *= fade
m = max(np.abs(L).max(), np.abs(R).max()); L, R = L/m*.9, R/m*.9
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.stack([L, R], 1)*32767).astype(np.int16).tobytes())
