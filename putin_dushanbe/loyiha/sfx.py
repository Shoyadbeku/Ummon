"""Synthesized SFX track (impacts, whooshes, risers, ticks) from storyboard cues."""
import sys, numpy as np
sys.path.insert(0, sys.argv[1])
import sb
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
SR = 48000; N = int(sb.TOTAL * SR); out = np.zeros((N, 2)); rng = np.random.default_rng(11)
def add(t, sig, pan=0.0):
    i = int(t * SR); j = min(N, i + len(sig)); s = sig[:j - i]
    out[i:j, 0] += s * (1 - max(0, pan)); out[i:j, 1] += s * (1 + min(0, pan))
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)
def impact():
    L = int(2.2 * SR); te = np.arange(L) / SR
    f = 38 + 90 * np.exp(-te * 18)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-te * 2.6)
    noise = bp(rng.standard_normal(L), 80, 3000) * np.exp(-te * 14) * .5
    tail = bp(rng.standard_normal(L), 200, 900) * np.exp(-te * 1.8) * .12
    return (body + noise + tail) * .9
def whoosh(d=.55):
    L = int(d * SR); te = np.arange(L) / SR; x = rng.standard_normal(L)
    env = np.sin(np.pi * te / d) ** 2
    lo = sosfilt(butter(2, 1800, 'low', fs=SR, output='sos'), x); hi = sosfilt(butter(2, 2500, 'high', fs=SR, output='sos'), x)
    mix = lo * (1 - te / d) + hi * (te / d) * .6
    return mix * env * .35
def riser(d):
    L = int(d * SR); te = np.arange(L) / SR; x = rng.standard_normal(L)
    y = np.zeros(L); seg = int(.05 * SR)
    for k in range(0, L, seg):
        p = k / L; fc = 300 + 5000 * p ** 2
        y[k:k + seg] = bp(x[k:k + seg], fc * .7, min(fc * 1.4, 20000))
    sweep = np.sin(2 * np.pi * np.cumsum(120 + 600 * (te / d) ** 2) / SR) * .25
    return (y * .5 + sweep) * (te / d) ** 2 * .45
def ticks(d):
    L = int(d * SR); y = np.zeros(L); n = int(d * 14)
    for k in range(n):
        i = int(k / 14 * SR); l = int(.012 * SR)
        if i + l < L: y[i:i + l] += np.sin(2 * np.pi * 2400 * np.arange(l) / SR) * np.exp(-np.arange(l) / SR * 400)
    return y * .25
for t, kind, x in sb.SFX:
    if kind == 'impact': add(t, impact())
    elif kind == 'whoosh': add(t - .15, whoosh(), pan=rng.uniform(-.3, .3))
    elif kind == 'riser': add(t, riser(x))
    elif kind == 'ticks': add(t, ticks(x))
out /= np.max(np.abs(out)) + 1e-9
wavfile.write(sys.argv[2], SR, (out * .9 * 32767).astype(np.int16)); print('sfx', len(sb.SFX))
