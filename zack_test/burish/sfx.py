# Barmoqlar burishishi videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/burish/sfx.py /tmp/claude-0/audio/sfx_burish.wav
import sys, wave
import numpy as np

SR = 48000; DUR = 35.42
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
# vushlar (kesishlarda)
for f in (20, 46, 87, 115, 199, 247, 314, 361, 407, 456, 506, 563, 631, 685, 739, 780, 818):
    add(T(f) - 0.4, whoosh(0.5, 1600, 0.8), 0.2)
# 1 ilgak: barmoq suvdan chiqadi
add(T(1), splash(0.7), 0.25); add(T(6), drip(1500), 0.25); add(T(13), drip(1900), 0.18)
# 2 hammom: suv shildirashi, tomchilar
add(T(20), fade(bp(noise(T(46) - T(20)), 300, 3000) * 0.4, 0.05, 0.1), 0.12)
for f in (26, 38): add(T(f), drip(1300), 0.2)
# 3 time-lapse: har burma o'sishida "tik"
for k in range(8): add(T(49 + k * 4), tick(900 + 60 * k), 0.12)
add(T(46), riser(T(86) - T(46)), 0.12)
# 5 afsona: tomchilar singadi
for i in range(12): add(T(121 + i * 3), drip(900 + 50 * i), 0.18)
# 6 "noto'g'ri": zarba + buzzer
add(T(163), thud(48, 1.2, 0.45), 0.8)
t = t_(0.45); add(T(164), bp(np.sign(np.sin(2 * np.pi * 110 * t)), 100, 3000) * env(len(t), 0.005, 0.2), 0.12)
for i in range(9): add(T(173 + i * 2), drip(1700), 0.12)
# 7 miya: crash zoom zarba, elektr
add(T(199), thud(55, 1.0, 0.35), 0.55); add(T(205), zap(0.6), 0.18)
for k in range(3): add(T(212 + k * 7), crackle(0.15), 0.25)
# 8 suv osti: bo'g'iq pufakchalar
add(T(247), lp(bubbles(T(314) - T(247)), 1800), 0.5)
add(T(247), fade(lp(noise(T(314) - T(247)), 300) * 2, 0.05, 0.1), 0.08)
# 9-10 signal yuguradi
add(T(318), zap(1.6), 0.2); add(T(361), zap(1.0), 0.18); add(T(383), thud(70, 0.6, 0.2), 0.4)
# 11 torayish: past "siqilish"
t = t_(1.6); add(T(412), np.sin(2 * np.pi * np.cumsum(90 - 40 * t / 1.6) / SR) * env(len(t), 0.2, 0.8), 0.3)
# 12-13 burmalar
add(T(460), riser(1.7), 0.12); add(T(506), thud(60, 0.8, 0.3), 0.4)
# 14 uzilgan asab: uchqun
add(T(570), zap(0.8), 0.18); add(T(581), thud(50, 0.8, 0.3), 0.5); add(T(581), crackle(T(630) - T(581)), 0.25)
# 15 ikki barmoq
add(T(631), thud(65, 0.6, 0.2), 0.3)
# 16 laboratoriya "ding"
t = t_(1.2); add(T(690), np.sin(2 * np.pi * 1760 * t) * env(len(t), 0.002, 0.4) * 0.3, 0.3)
# 17 shina: ho'l yo'l shovqini, sachrash
add(T(739), fade(bp(noise(T(780) - T(739)), 200, 5000), 0.2, 0.1) * np.linspace(0.4, 1, int(SR * (T(780) - T(739)))), 0.3)
add(T(755), splash(1.0), 0.4)
# 18 shisha: bosilish, g'ichirlash
add(T(796), thud(80, 0.4, 0.12), 0.4); add(T(797), squeak(0.3), 0.15); add(T(797), splash(0.3), 0.15)
# 19 o'rdak: suv, ushlash, oxirgi zarba
add(T(829), splash(0.8), 0.45); add(T(830), squeak(0.2), 0.2)
add(T(830), thud(45, 1.6, 0.55), 0.8)

out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
