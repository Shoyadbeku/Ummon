# Tish va jag' suyagi videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/tish/sfx.py /tmp/claude-0/audio/sfx_tish.wav
import sys, wave
import numpy as np

SR = 48000; DUR = 43.76
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
def gull(d=0.8):
    t = t_(d); f = 1500 + 700 * np.sin(np.pi * t / d) - 600 * (t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)) * env(len(t), 0.05, d / 2.5) * 0.4
def moo(d=1.6):
    t = t_(d); f = 135 - 30 * t / d
    ph = 2 * np.pi * np.cumsum(f) / SR
    saw = sum(np.sin(k * ph) / k for k in range(1, 30))
    return bp(saw, 180, 1100) * np.minimum(1, t / 0.15) * np.exp(-np.maximum(0, t - d * 0.6) / 0.2)
def waves(d):
    n = lp(noise(d), 700, 2); t = t_(d)
    sw = 0.55 + 0.45 * np.sin(2 * np.pi * t / 4.5) ** 2
    return n / (np.abs(n).max() + 1e-9) * sw

def drip(f0=1400):                                  # suv tomchisi "plop"
    t = t_(0.18); f = f0 * (1 + 1.2 * np.exp(-t / 0.02))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.001, 0.04)
def splash(d=0.6):
    t = t_(d); return bp(noise(d), 600, 7000) * env(len(t), 0.004, d / 4)
def bubbles(d):
    x = np.zeros(int(SR * d))
    for k in range(int(d * 14)):
        i = rng.integers(0, len(x) - int(SR * 0.1)); b = drip(rng.uniform(700, 2200)) * rng.uniform(0.2, 0.6)
        x[i:i + len(b)] += b[: len(x) - i]
    return x
def zap(d=0.5):                                     # asab signali "elektr"
    t = t_(d); f = 300 + 2500 * t / d
    sq = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR))
    return bp(sq * 0.5 + noise(d) * 0.3, 400, 6000) * env(len(t), 0.01, d / 2)
def crackle(d):
    x = np.zeros(int(SR * d))
    for k in range(int(d * 30)):
        i = rng.integers(0, len(x) - 200); x[i:i + 200] += rng.standard_normal(200) * np.exp(-np.arange(200) / 40)
    return hp(x, 1500)
def squeak(d=0.25):                                 # rezina/shisha g'ichirlashi
    t = t_(d); f = 900 + 500 * np.sin(2 * np.pi * 6 * t)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.01, d / 2) * 0.6
def tick(f0=1200):
    t = t_(0.06); return np.sin(2 * np.pi * f0 * t) * env(len(t), 0.001, 0.015)

tt = np.arange(len(out)) / SR
# fon: past drone, rentgen/kesim qismida kuchayadi
drone = sum(np.sin(2 * np.pi * f * tt) for f in (55, 65.4, 82.4)) / 3 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.12 * tt))
out += drone * (0.02 + 0.03 * np.clip((tt - 8) / 15, 0, 1))
def ting(f0=2400, d=0.9):                           # metall laganga tegish
    t = t_(d)
    return sum(a * np.sin(2 * np.pi * f0 * k * t) * np.exp(-t / (d / (1 + 2 * i)))
               for i, (k, a) in enumerate(((1, 1.0), (2.76, 0.5), (5.4, 0.25)))) * env(len(t), 0.001, d)
def crunch(d=0.35):                                 # ovqat ezilishi
    return crackle(d) * 2 + bp(noise(d), 300, 3000) * env(int(SR * d), 0.002, d / 3)

tt = np.arange(len(out)) / SR
drone = sum(np.sin(2 * np.pi * f * tt) for f in (55, 65.4, 82.4)) / 3 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.12 * tt))
out += drone * (0.02 + 0.03 * np.clip((tt - 6) / 20, 0, 1))
for f in (51, 111, 144, 231, 295, 364, 466, 552, 629, 713, 829, 913, 977):     # kesishlarda vush
    add(T(f) - 0.35, whoosh(0.45, 1600, 0.8), 0.22)
# 1 ilgak: og'riq zarbalari (yurak urishi)
for f in (1, 19, 37): add(T(f), heartbeat(), 0.55)
# 2 qisqich: ushlash, g'ichirlash, sug'urish
add(T(69), tick(2600), 0.35); add(T(69), ting(3200, 0.3), 0.1)
add(T(72), crackle(0.9), 0.35); add(T(74), squeak(0.5), 0.12)
add(T(95), thud(70, 0.6, 0.15), 0.6); add(T(95), crackle(0.3), 0.6); add(T(96), squelch(0.3, 420), 0.45)
# 3 lagan: tish tushib sakraydi
add(T(120), ting(2400, 1.0), 0.45); add(T(131), ting(2500, 0.6), 0.25); add(T(138), ting(2600, 0.4), 0.15)
# 4 rentgen
add(T(144), thud(50, 1.0, 0.35), 0.55); add(T(150), zap(0.6), 0.15)
for f in range(158, 230, 12): add(T(f), heartbeat(), 0.25)
# 5 ildiz: past drone siljishi
add(T(231), riser(2.5), 0.08)
# 6 tishlash
add(T(330), riser(0.5), 0.1); add(T(341), crunch(0.45), 0.8); add(T(341), thud(60, 0.7, 0.2), 0.6)
# 7 chaynash + signal
for c in (372, 404, 436):
    add(T(c), thud(65, 0.5, 0.12), 0.5); add(T(c), crunch(0.15), 0.25); add(T(c + 1), zap(0.5), 0.15)
# 8 tish chiqadi, bo'shliqqa tishlash
add(T(470), squelch(0.35, 380), 0.45); add(T(478), crackle(0.3), 0.4); add(T(486), whoosh(0.4, 2000, 0.5), 0.25)
add(T(528), tick(700), 0.6); add(T(528), thud(45, 1.0, 0.4), 0.6)
t = t_(0.5); add(T(530), bp(np.sign(np.sin(2 * np.pi * 110 * t)), 100, 3000) * env(len(t), 0.005, 0.25), 0.1)
# 9 miya o'ylaydi
for k in range(5): add(T(556 + k * 7), crackle(0.12), 0.25)
add(T(588), zap(1.0), 0.2); add(T(612), thud(55, 0.8, 0.3), 0.45)
# 10 kalsiy oqib ketadi
for k in range(26): add(T(633 + k * 3), drip(1600 + 40 * k), 0.08)
add(T(629), fade(lp(noise(T(712) - T(629)), 400) * 1.5, 0.2, 0.2), 0.08)
# 11 cho'kish (time-lapse)
t = t_(4.0); add(T(722), np.sin(2 * np.pi * np.cumsum(110 - 60 * t / 4.0) / SR) * env(len(t), 0.4, 2.0), 0.3)
for k in range(10): add(T(722 + k * 10), tick(900 - 40 * k), 0.1)
# 12 tishlar qiyshayadi
add(T(840), squeak(0.8), 0.08); add(T(840), crackle(1.5), 0.12)
# 13 yuz cho'kadi
add(T(913), riser(2.6), 0.12)
# 14 qarigan yuz: zarba
add(T(977), thud(42, 1.8, 0.6), 0.9); add(T(977), crackle(0.4), 0.2)

out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
