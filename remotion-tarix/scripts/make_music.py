"""Mualliflik huquqisiz (o'zimiz sintez qilgan) hujjatli film uslubidagi fon musiqasi.
Ishlatish: python3 scripts/make_music.py <davomiylik_soniya> public/music.wav
"""
import sys, wave
import numpy as np

SR = 44100
dur = float(sys.argv[1]) if len(sys.argv) > 1 else 720
out = sys.argv[2] if len(sys.argv) > 2 else "public/music.wav"
n = int(SR * dur)
t = np.arange(n) / SR
rng = np.random.default_rng(7)

def midi(m): return 440.0 * 2 ** ((m - 69) / 12)

# D minor progression: Dm - Bb - F - C  (har biri 8 s)
chords = [[50, 57, 62, 65], [46, 53, 58, 62], [41, 53, 57, 60], [48, 55, 60, 64]]
bar = 8.0
mix = np.zeros(n)

def pad(freq, start, length):
    i0, i1 = int(start * SR), min(n, int((start + length) * SR))
    if i0 >= n: return
    tt = np.arange(i1 - i0) / SR
    env = np.minimum(1, tt / 2.5) * np.minimum(1, (length - tt) / 2.5)
    env = np.clip(env, 0, 1)
    sig = np.zeros_like(tt)
    for det in (-0.12, 0, 0.12):  # detuned "strings"
        f = freq * 2 ** (det / 12)
        ph = 2 * np.pi * f * tt + rng.uniform(0, 6.28)
        sig += np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)
    mix[i0:i1] += sig * env * 0.05

k = 0
s = 0.0
while s < dur:
    ch = chords[k % 4]
    for m in ch:
        pad(midi(m), s, bar + 2.5)
    # past bas
    pad(midi(ch[0] - 12), s, bar + 2.5)
    # yengil "piano" notalari (arpejjio) 2-qismdan boshlab
    if k >= 2:
        for j, m in enumerate([ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12]):
            st = s + j * 2.0
            i0 = int(st * SR); L = int(3.0 * SR)
            if i0 + L > n: continue
            tt = np.arange(L) / SR
            f = midi(m)
            note = (np.sin(2*np.pi*f*tt) + 0.3*np.sin(4*np.pi*f*tt)) * np.exp(-tt * 1.6)
            mix[i0:i0+L] += note * 0.035
    # har 4 taktda past "timpani" zarbasi
    if k % 4 == 0:
        i0 = int(s * SR); L = int(2.5 * SR)
        if i0 + L <= n:
            tt = np.arange(L) / SR
            mix[i0:i0+L] += np.sin(2*np.pi*midi(38)*tt*(1+0.3*np.exp(-tt*8))) * np.exp(-tt*2.2) * 0.12
    s += bar; k += 1

# Oddiy reverb (bir nechta kechikishlar)
rev = mix.copy()
for d, g in ((0.031, 0.5), (0.047, 0.42), (0.071, 0.35), (0.113, 0.28), (0.173, 0.2), (0.257, 0.14)):
    di = int(d * SR)
    rev[di:] += mix[:-di] * g
# Fade in / out
fade = np.ones(n)
fi, fo = int(4 * SR), int(6 * SR)
fade[:fi] = np.linspace(0, 1, fi)
fade[-fo:] = np.linspace(1, 0, fo)
rev *= fade
rev /= np.max(np.abs(rev)) + 1e-9
rev *= 0.8
st = np.stack([rev, np.roll(rev, int(0.012 * SR))], axis=1)  # kenglik
pcm = (st * 32767).astype(np.int16)
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("ok", out, dur)
