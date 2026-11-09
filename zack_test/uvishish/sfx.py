# "Oyoq uvishishi" videosi uchun tovush effektlari (sintez) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/bvenv/bin/python -I zack_test/uvishish/sfx.py /tmp/claude-0/audio/sfx_uv.wav
# Yordamchi funksiyalar yelim/sfx.py dan.
import sys, wave
import numpy as np

SR = 48000; DUR = 45.2
rng = np.random.default_rng(12)
out = np.zeros(int(SR * DUR))
def T(frame): return (frame - 1) / 24.0             # kadr -> soniya

def t_(d): return np.arange(int(SR * d)) / SR
def env(n, a=0.005, decay=0.3):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / decay)
def lp(x, fc, n=2):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / fc) ** 2) ** (n / 2), len(x))
def hp(x, fc): return x - lp(x, fc, 1)
def bp(x, lo, hi): return hp(lp(x, hi, 2), lo)
def add(at, x, gain=1.0):
    i = int(at * SR); j = min(len(out), i + len(x))
    if j > i: out[i:j] += gain * x[: j - i]
def noise(d): return rng.standard_normal(int(SR * d))
def fade(x, a=0.05, b=0.2):
    n = len(x); e = np.ones(n); na, nb = int(a * SR), int(b * SR)
    e[:na] = np.linspace(0, 1, na); e[n - nb:] = np.linspace(1, 0, nb); return x * e

def thud(f=60, d=0.8, decay=0.25):
    t = t_(d); sweep = f * (1 + 1.5 * np.exp(-t / 0.03))
    return np.sin(2 * np.pi * np.cumsum(sweep) / SR) * env(len(t), 0.002, decay) + 0.3 * lp(noise(d), 400) * env(len(t), 0.002, 0.05)
def whoosh(d=0.7, fc=1400, peak=0.7):
    n = noise(d); t = t_(d); shape = np.exp(-((t / d - peak) ** 2) / 0.03)
    return hp(lp(n, fc, 2), fc * 0.25) * shape
def riser(d=2.0):
    t = t_(d); f = 200 + 1800 * (t / d) ** 2
    return (0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR) + bp(noise(d), 800, 6000) * 0.6) * (t / d) ** 2
def heartbeat():
    return np.concatenate([thud(52, 0.25, 0.06), np.zeros(int(SR * 0.12)), 0.7 * thud(48, 0.4, 0.07)])
def squelch(d=0.25, f0=500):                         # ho'l "chuv" tovushi
    t = t_(d); f = f0 * (1 + 0.8 * np.sin(2 * np.pi * 9 * t)) * np.exp(-t / 0.2)
    return (bp(noise(d), 300, 2500) * 0.7 + 0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * env(len(t), 0.004, d / 3)
def buzz(d, f0=190, loud=None):                     # pashsha g'ing'illashi
    t = t_(d)
    f = f0 * (1 + 0.04 * np.sin(2 * np.pi * 3.1 * t) + 0.02 * rng.standard_normal(len(t)).cumsum() / np.sqrt(len(t)))
    ph = 2 * np.pi * np.cumsum(f) / SR
    saw = sum(np.sin(k * ph) / k for k in range(1, 14))
    x = bp(saw, 150, 4500) * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * t))
    if loud is not None: x *= np.interp(t, np.linspace(0, d, len(loud)), loud)
    return fade(x, 0.03, 0.06)
def zap(d=0.5):                                     # asab signali "elektr"
    t = t_(d); f = 300 + 2500 * t / d
    sq = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR))
    return bp(sq * 0.5 + noise(d) * 0.3, 400, 6000) * env(len(t), 0.01, d / 2)
def crackle(d):
    x = np.zeros(int(SR * d))
    for k in range(int(d * 30)):
        i = rng.integers(0, len(x) - 200); x[i:i + 200] += rng.standard_normal(200) * np.exp(-np.arange(200) / 40)
    return hp(x, 1500)

# ---------------- voqealar (kadr raqamlari uvishish.py bilan bir xil) ----------------
CUTS = [72, 120, 160, 217, 264, 336, 414, 520, 575, 621, 695, 759, 860, 949, 1031]
for f in CUTS: add(T(f) - 0.25, whoosh(0.45, 1800, 0.6), 0.22)
add(0.0, lp(noise(45.2), 180) * 0.05)                       # xona foni
add(T(1), riser(1.2) * 0.25)
# hissiz: pastga tushuvchi "o'chish"
t = t_(0.9); add(T(87), np.sin(2 * np.pi * np.cumsum(300 * np.exp(-t * 3)) / SR) * env(len(t), 0.005, 0.4) * 0.35)
add(T(87), thud(55, 0.6, 0.2), 0.5)
# turish
add(T(128), whoosh(0.6, 900, 0.5), 0.35)
# minglab ignalar
for k in range(70):
    tt = T(160) + rng.uniform(0.25, 2.2)
    add(tt, bp(noise(0.03), 2500, 9000) * env(int(SR * 0.03), 0.0005, 0.008), rng.uniform(0.15, 0.35))
add(T(160), riser(2.3) * 0.25)
# og'riq
add(T(217), thud(48, 0.9, 0.3), 0.9); add(T(222), heartbeat(), 0.7); add(T(240), heartbeat(), 0.6)
# qon oqimi
x = lp(noise(3.0), 400) * (0.6 + 0.4 * np.sin(2 * np.pi * 1.3 * t_(3.0)))
add(T(264), fade(x, 0.2, 0.4), 0.35)
# qisilish: zarba
add(T(350), thud(42, 1.0, 0.35), 1.0); add(T(350), zap(0.3), 0.25)
# asab yo'li: impulslar
for k in range(10): add(T(420) + k * 0.4, zap(0.25), 0.18)
# shlang: suv purkash, bosish, to'xtash
sp_ = bp(noise(T(536) - T(520) + 0.15), 1500, 8000) * 0.25
add(T(520), fade(sp_, 0.05, 0.12))
add(T(536), thud(70, 0.4, 0.12), 0.6); add(T(536), squelch(0.3, 300), 0.6)
# ezilish: bosim + urilib so'nayotgan impulslar
add(T(575), thud(38, 1.2, 0.5), 0.8)
for f in range(581, 620, 7): add(T(f), zap(0.12), 0.2)
# bosim ko'tariladi
add(T(640), whoosh(1.0, 700, 0.4), 0.4)
# birdaniga uyg'onish
add(T(733) - 0.6, riser(0.6) * 0.5)
add(T(733), thud(60, 0.8, 0.25), 1.0); add(T(733), zap(0.6), 0.6); add(T(733), crackle(1.0), 0.6)
# tartibsiz impulslar
for k in range(28): add(T(759) + rng.uniform(0, 4.0), zap(rng.uniform(0.08, 0.25)), rng.uniform(0.15, 0.35))
add(T(759), crackle(4.1), 0.35)
# chumolilar (o'rmalash) va ignalar
add(T(860), fade(crackle(2.0) * 0.4, 0.2, 0.3), 0.5)
for k in range(35):
    tt = T(908) + rng.uniform(0, 1.5)
    add(tt, bp(noise(0.03), 2500, 9000) * env(int(SR * 0.03), 0.0005, 0.008), rng.uniform(0.15, 0.35))
# qayta ishga tushish: kuchlanish ko'tariladi, yonish
t = t_(2.4); hum = np.sin(2 * np.pi * np.cumsum(60 + 240 * (t / 2.4) ** 2) / SR) * (t / 2.4)
add(T(949), hum, 0.3); add(T(1001), thud(55, 0.8, 0.3), 0.7); add(T(1001), zap(0.4), 0.4)
# qisqa tutashuv
add(T(1043), zap(0.8), 0.9); add(T(1043), crackle(1.6), 0.8); add(T(1043), thud(45, 1.0, 0.4), 0.8)
add(T(1065), zap(0.3), 0.4)

out = out / (np.abs(out).max() + 1e-9) * 0.9
pcm = (out * 32767).astype(np.int16)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("ok", sys.argv[1], len(out) / SR)
