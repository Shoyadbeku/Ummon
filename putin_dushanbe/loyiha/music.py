"""Original synthesized news-documentary music bed (no third-party samples).
D minor, 96 BPM. Intensity follows the story sections.
Usage: python3 music.py out.wav total_seconds
"""
import sys, numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile

SR = 48000
OUT, TOTAL = sys.argv[1], float(sys.argv[2])
N = int(TOTAL * SR)
t = np.arange(N) / SR
BPM = 96.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(7)

# intensity keyframes (time, value) – follows storyboard sections
KF = [(0, .95), (16.0, .95), (16.6, .35), (20.0, 1.0), (30.5, .9), (33.0, .45), (59, .5), (94.0, .6),
      (112, .75), (120, .6), (154.0, .75), (179, .85), (192, .65), (217, .55), (253.8, .7), (268, .55),
      (291.2, .65), (325, .8), (346.0, .7), (360, .85), (372, .9), (375.5, .5), (TOTAL, 0.0)]
kt, kv = zip(*KF)
I = np.interp(t, kt, kv)

def lp(x, f, order=2):
    return sosfilt(butter(order, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, order=2):
    return sosfilt(butter(order, f, 'high', fs=SR, output='sos'), x)

def saw(freq, tt, harm=10):
    y = np.zeros_like(tt)
    for k in range(1, harm + 1):
        y += ((-1) ** (k + 1)) * np.sin(2 * np.pi * freq * k * tt) / k
    return y * 2 / np.pi

# progression (Dm, Bb, Gm, A) – root midi notes
PROG = [(50, [50, 53, 57]), (46, [46, 50, 53]), (43, [43, 46, 50]), (45, [45, 49, 52])]
mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12)

pad = np.zeros(N); bass = np.zeros(N); ticks = np.zeros(N); kick = np.zeros(N)
nbars = int(TOTAL / BAR) + 1
for b in range(nbars):
    s0 = int(b * BAR * SR); s1 = min(N, int((b + 1) * BAR * SR) + int(0.3 * SR))
    if s0 >= N: break
    root, chord = PROG[b % 4]
    tt = np.arange(s1 - s0) / SR
    env = np.minimum(1, tt / 0.6) * np.minimum(1, np.maximum(0, (BAR + 0.3 - tt) / 0.5))
    seg = np.zeros_like(tt)
    for m in chord:
        for det in (-0.08, 0.08):
            seg += saw(mtof(m + 12) * (1 + det / 100), tt, 6)
    seg += 0.7 * np.sin(2 * np.pi * mtof(root - 12) * tt)
    pad[s0:s1] += seg * env * 0.18
    # 8th-note pulse bass
    for e in range(8):
        p0 = s0 + int(e * BEAT / 2 * SR)
        L = int(BEAT / 2 * SR)
        if p0 + L > N: break
        te = np.arange(L) / SR
        note = mtof(root) * (2 if e % 4 == 3 else 1)
        bass[p0:p0 + L] += saw(note, te, 8) * np.exp(-te * 9) * (1.0 if e % 2 == 0 else 0.7)
    # 16th ticks + kicks
    for e in range(16):
        p0 = s0 + int(e * BEAT / 4 * SR)
        L = int(0.04 * SR)
        if p0 + L > N: break
        te = np.arange(L) / SR
        ticks[p0:p0 + L] += rng.standard_normal(L) * np.exp(-te * 120) * (1.0 if e % 4 == 0 else 0.45)
    for e in (0, 2):
        p0 = s0 + int(e * BEAT * SR); L = int(0.35 * SR)
        if p0 + L > N: break
        te = np.arange(L) / SR
        f = 45 + 80 * np.exp(-te * 30)
        kick[p0:p0 + L] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-te * 9)

pad = lp(pad, 1800) ; bass = lp(bass, 600); ticks = hp(ticks, 6000)
# slow movement on the pad
pad *= 0.85 + 0.15 * np.sin(2 * np.pi * t / 7.0)

g = lambda lo, hi: np.clip((I - lo) / (hi - lo), 0, 1)
mix = pad * (0.55 + 0.45 * I) + bass * 0.55 * g(.3, .6) + ticks * 0.10 * g(.5, .8) + kick * 0.6 * g(.7, .95)

# sub drone for weight
mix += 0.12 * np.sin(2 * np.pi * mtof(38) * t) * (0.5 + 0.5 * I)
# fade in/out
fade = np.minimum(1, t / 0.05) * np.clip((TOTAL - t) / 3.0, 0, 1)
mix *= fade
# stereo width: small delay on right
d = int(0.012 * SR)
L = mix; R = np.concatenate([np.zeros(d), mix[:-d]]) * 0.97 + 0.03 * mix
st = np.stack([L, R], 1)
st /= np.max(np.abs(st)) + 1e-9
wavfile.write(OUT, SR, (st * 0.89 * 32767).astype(np.int16))
print('ok', OUT, TOTAL)
