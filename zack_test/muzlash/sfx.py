# Muzqaymoq (miya muzlashi) videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/muzlash/sfx.py /tmp/claude-0/audio/sfx_muzlash.wav
import sys, wave
import numpy as np

SR = 48000; DUR = 40.0
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

def ring(d=1.5, f0=3200):                           # quloq shang'illashi (og'riq)
    t = t_(d); return np.sin(2 * np.pi * f0 * t) * env(len(t), 0.05, d / 2.5) * 0.25
def tinkle(d=1.2, n=26):                           # muz parchalari jaranglashi
    x = np.zeros(int(SR * d))
    for k in range(n):
        i = int(rng.uniform(0, 0.7) * len(x)); f0 = rng.uniform(2500, 7000); tt_ = t_(0.25)
        s = np.sin(2 * np.pi * f0 * tt_) * env(len(tt_), 0.001, 0.05) * rng.uniform(0.2, 0.6)
        x[i:i + len(s)] += s[: len(x) - i]
    return x
def hiss(d=1.2):                                   # sovuq "shhh"
    t = t_(d); return bp(noise(d), 3000, 12000) * env(len(t), 0.02, d / 2)

tt = np.arange(len(out)) / SR
drone = sum(np.sin(2 * np.pi * f * tt) for f in (55, 65.4, 82.4)) / 3 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.12 * tt))
out += drone * (0.015 + 0.03 * np.clip((tt - 5) / 10, 0, 1)) * np.clip((39.6 - tt) / 1.5, 0, 1)
for f in (47, 82, 125, 209, 266, 335, 413, 479, 560, 622, 698, 755, 789, 844, 909):
    add(T(f) - 0.35, whoosh(0.45, 1700, 0.8), 0.2)
# 1 ilgak: katta tishlash (qirsillash)
add(T(28), crackle(0.25), 0.35); add(T(28), thud(90, 0.3, 0.08), 0.25)
# 2 og'riq: crash zoom zarba + shang'illash
add(T(49), thud(50, 1.2, 0.4), 0.8); add(T(50), ring(1.6, 3400), 0.35)
# 3 rentgen: har chaqnashda yurak urishi
for f in range(86, 124, 8): add(T(f), thud(48, 0.35, 0.08), 0.45)
# 4 miya muzlaydi -> sinadi
add(T(135), lp(crackle(T(180) - T(135)), 6000), 0.3); add(T(135), riser(T(181) - T(135)), 0.12)
add(T(181), thud(45, 1.4, 0.5), 0.85); add(T(181), tinkle(1.6, 40), 0.5); add(T(181), crackle(0.5), 0.5)
# 5 muzqaymoq tanglayga tegadi
add(T(229), squelch(0.3, 400), 0.4); add(T(229), hiss(1.4), 0.25); add(T(232), tinkle(0.8, 10), 0.18)
# 6 tomirlar torayadi
t = t_(1.2); add(T(295), np.sin(2 * np.pi * np.cumsum(120 - 70 * t / 1.2) / SR) * env(len(t), 0.05, 0.6), 0.4)
# 7 issiq to'lqin
add(T(343), riser(T(412) - T(343)), 0.12)
for f in range(345, 412, 18): add(T(f), heartbeat(), 0.35)
# 8 kengayish: zarba + kuchli yurak urishi
add(T(437), thud(42, 1.4, 0.5), 0.9)
for f in range(445, 478, 9): add(T(f), thud(50, 0.3, 0.07), 0.55)
# 9-10 asab signali
add(T(489), zap(1.3), 0.2); add(T(562), zap(1.2), 0.22); add(T(590), thud(70, 0.6, 0.2), 0.45)
# 11 adashgan miya: tartibsiz uchqunlar, oxirida zarba
for f in (636, 643, 650, 657, 664, 671): add(T(f), zap(0.3), 0.14)
add(T(676), thud(55, 0.9, 0.3), 0.5); add(T(676), ring(1.0, 3000), 0.2)
# 12 peshona og'rig'i (keng plan)
add(T(698), thud(45, 1.4, 0.5), 0.85); add(T(699), ring(1.8, 3600), 0.3)
# 14 til tanglayga bosiladi
add(T(819), squelch(0.35, 300), 0.4)
# 15 issiqlik tarqaladi
add(T(846), riser(T(908) - T(846)) * 0.6, 0.1)
# 16 yengillik: yumshoq qo'ng'iroqcha
t = t_(1.8); add(T(912), (np.sin(2 * np.pi * 1318 * t) + 0.6 * np.sin(2 * np.pi * 1976 * t)) * env(len(t), 0.002, 0.6) * 0.3, 0.35)

out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
