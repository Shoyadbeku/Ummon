# Synthesize SFX track (whooshes, impacts, riser) aligned to the timeline.
import numpy as np, json, wave
SR = 44100; tl = json.load(open("/opt/work/rv/public/timeline.json")); N = int(SR * tl["total"]) + SR
rng = np.random.default_rng(3); out = np.zeros((N, 2))
def lp(x, a):  # one-pole lowpass with time-varying coefficient
    y = np.zeros_like(x); s = 0.0
    for i in range(len(x)): s += a[i] * (x[i] - s); y[i] = s
    return y
def whoosh(d=0.7, peak=.55):
    n = int(SR*d); t = np.arange(n)/n; env = np.where(t < peak, (t/peak)**2, ((1-t)/(1-peak))**1.5)
    a = 0.02 + 0.25*env; x = lp(rng.uniform(-1, 1, n), a) * env * 3
    pan = np.linspace(-1, 1, n); return np.stack([x*(1-pan)/2*1.4, x*(1+pan)/2*1.4], 1)
def impact(d=1.6):
    n = int(SR*d); t = np.arange(n)/SR
    x = np.sin(2*np.pi*(45 + 90*np.exp(-t*18))*t) * np.exp(-t*3.2) + lp(rng.uniform(-1,1,n), np.full(n,.15))*np.exp(-t*12)*.8
    return np.stack([x, x], 1)
def riser(d=1.4):
    n = int(SR*d); t = np.arange(n)/n; env = t**2
    x = lp(rng.uniform(-1,1,n), 0.01 + 0.3*t) * env * 2 + np.sin(2*np.pi*(200 + 900*t**2)*np.arange(n)/SR)*env*.15
    return np.stack([x, x], 1)
def add(sig, at, g):
    s = int(at*SR); e = min(N, s+len(sig)); out[s:e] += sig[:e-s]*g
fps = tl["fps"]
for k in range(4):  # hook shots every 20 frames
    add(impact(1.0), k*20/fps, .55); add(whoosh(.45, .3), k*20/fps - .05 if k else 0, .5)
add(riser(1.2), 86/fps - 1.2 + .3, .5)
add(impact(2.4), 86/fps, .9)
add(whoosh(1.0, .6), tl["hook"] - .7, .55)
prev = None
for s in tl["scenes"]:
    if prev and s["era"] != prev: add(whoosh(.8, .6), s["start"] - .5, .6); add(impact(1.4), s["start"], .35)
    prev = s["era"]
for c in tl["cards"]: add(whoosh(.5, .4), c["start"], .25)
add(impact(3.0), tl["total"] - 4.2, .6)
out /= max(1e-9, np.abs(out).max()) / .9
with wave.open("/opt/work/music/sfx.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype(np.int16).tobytes())
