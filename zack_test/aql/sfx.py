# Aql tishlari videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/aql/sfx.py /tmp/claude-0/audio/sfx_aql.wav
import sys, wave
import numpy as np

SR = 48000; DUR = 39.5
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

def grind(d):                                       # suyak/tish g'ijirlashi (buldozer)
    t = t_(d); f = 70 + 15 * np.sin(2 * np.pi * 5 * t)
    sq = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR))
    return (lp(sq, 900) * 0.5 + bp(noise(d), 200, 2500) * 0.6) * fade(np.ones(len(t)), 0.05, 0.15)
def snap():                                         # suyak sinishi: keskin chirsillash + zarba
    x = crackle(0.35) * 2.5
    n = int(SR * 0.12); x[:n] += hp(noise(0.12), 2000) * env(n, 0.0005, 0.02) * 1.5
    return x
def squish(d=0.4):                                  # ho'l, yumshoq (kista, milk)
    t = t_(d); f = 220 * (1 + 0.5 * np.sin(2 * np.pi * 4 * t))
    return lp(noise(d), 900) * 0.6 * env(len(t), 0.02, d / 2) + 0.3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.02, d / 3)
def brush_scrub(d):
    t = t_(d); return bp(noise(d), 2500, 9000) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 3.3 * t)))

tt = np.arange(len(out)) / SR
drone = sum(np.sin(2 * np.pi * f * tt) for f in (49, 58.3, 73.4)) / 3 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * tt))
out += drone * (0.02 + 0.035 * np.clip((tt - 12) / 20, 0, 1))
for f in (51, 82, 113, 171, 232, 283, 338, 366, 421, 484, 531, 592, 641, 695, 761, 832, 863, 894):
    add(T(f) - 0.4, whoosh(0.5, 1600, 0.8), 0.2)
# 1 ilgak: rentgen crash zoom
add(T(1), riser(0.7), 0.12); add(T(17), thud(55, 1.0, 0.35), 0.6); add(T(18), zap(0.5), 0.12)
# 2-3 bosh suyagi: yurak urishi kabi pulsatsiya
for f in (55, 65, 75, 86, 96, 106): add(T(f), heartbeat(), 0.35)
# 4-5 kesim: tishlar qatori, titrash
add(T(113), thud(70, 0.6, 0.2), 0.3); add(T(195), riser(1.5), 0.1)
for k in range(10): add(T(192 + k * 4), tick(300 + 20 * k), 0.1)
# 6 oshxona: tinch
# 7 rentgenga o'tish
add(T(300), thud(50, 1.0, 0.35), 0.55); add(T(301), zap(0.5), 0.15)
# 8 buldozer
add(T(340), grind(1.1), 0.45); add(T(342), thud(45, 1.0, 0.4), 0.7); add(T(344), crackle(0.8), 0.3)
# 9 bosim to'lqinlari
for k in range(6): add(T(370 + k * 8), thud(40, 0.5, 0.15), 0.3)
add(T(366), grind(2.2) * 0.4, 0.25)
# 10 erish
add(T(421), crackle(2.5), 0.15); add(T(421), riser(2.4), 0.08)
# 11-12 og'iz ichi: ho'l
add(T(484), squish(0.6), 0.3); add(T(552), squish(0.8), 0.45)
# 13 ushoqlar tushadi
for k in range(14): add(T(596 + k * 2.5), tick(rng.uniform(500, 1400)), 0.15)
add(T(612), squish(0.5), 0.3)
# 14 cho'tka
add(T(641), brush_scrub(T(694) - T(641)), 0.18); add(T(675), thud(90, 0.3, 0.08), 0.35)
# 15-16 kista, yemirilish
add(T(700), squish(1.2), 0.4); add(T(730), squish(1.0), 0.35)
for k in range(6): add(T(769 + k * 6), crackle(0.25), 0.3)
add(T(761), riser(2.8), 0.12)
# 17 ovqat: chaynash
add(T(873), squish(0.25), 0.4); add(T(874), crackle(0.15), 0.3)
# 18 sinish
add(T(906), snap(), 0.9); add(T(906), thud(42, 1.4, 0.5), 0.9)
add(T(925), snap(), 1.0); add(T(925), thud(38, 1.5, 0.6), 1.0)

out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
