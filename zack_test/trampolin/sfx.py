# "Batut qanday ixtiro qilingan" videosi uchun tovush effektlari (sintez) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/trampolin/sfx.py /tmp/claude-0/audio/sfx_tr.wav [events.json]
# Yordamchi funksiyalar magnit/sfx.py dan.
import sys, wave
import numpy as np

SR = 48000; DUR = 55.5
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


def wind(d, fc=900):
    n = bp(noise(d), 150, fc); t = t_(d)
    return n / (np.abs(n).max() + 1e-9) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.4 * t))
def jet(d):                                          # reaktiv dvigatel g'uvillashi
    t = t_(d); x = bp(noise(d), 200, 3000) * 0.8 + 0.25 * np.sin(2 * np.pi * 2400 * t) * 0.15
    return x / (np.abs(x).max() + 1e-9)
def creak(d=0.6, f0=140):                            # metall g'ichirlashi
    t = t_(d); f = f0 * (1 + 0.3 * np.sin(2 * np.pi * 3 * t)) + 30 * rng.standard_normal(len(t)).cumsum() / np.sqrt(len(t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return bp(sum(np.sin(k * ph) / k for k in range(1, 20)), 200, 3000) * env(len(t), 0.05, d / 2)
def metal_crack():
    return crackle(0.5) * 1.4 + 0.6 * thud(80, 0.5, 0.12)

def mixs(*xs):
    n = max(len(x) for x in xs); o = np.zeros(n)
    for x in xs: o[:len(x)] += x
    return o
def glass_break():
    return mixs(tinkle(1.0, 60) * 1.2, crackle(0.4) * 0.8, 0.5 * thud(90, 0.4, 0.08))
def glass_crack():
    return mixs(crackle(0.35) * 1.2, tinkle(0.5, 8) * 0.5)
def roar(d):                                         # dekompressiya: kuchli havo oqimi
    t = t_(d); x = bp(noise(d), 120, 5000)
    return x / (np.abs(x).max() + 1e-9) * np.minimum(1, t / 0.05) * (0.55 + 0.45 * np.exp(-t / 1.5))
def alarm(d, f0=880):                                # "ding-dong" ogohlantirish
    t = t_(d); x = np.zeros(len(t))
    for k, f in enumerate((f0, f0 * 0.75)):
        tt_ = t_(0.6); s = (np.sin(2 * np.pi * f * tt_) + 0.3 * np.sin(4 * np.pi * f * tt_)) * env(len(tt_), 0.005, 0.25)
        i = int(k * 0.45 * SR); x[i:i + len(s)] += s[: len(x) - i]
    return x
def heartbeat_slow(d, bpm=55):
    x = np.zeros(int(SR * d)); hb = heartbeat()
    for k in range(int(d * bpm / 60)):
        i = int(k * 60 / bpm * SR); x[i:i + len(hb)] += hb[: len(x) - i]
    return x

def click(f0=3500):                                   # magnitlar "chiq" etib yopishadi
    t = t_(0.08); return (np.sin(2 * np.pi * f0 * t) + 0.5 * np.sin(2 * np.pi * f0 * 1.7 * t)) * env(len(t), 0.0005, 0.012) + hp(noise(0.08), 3000) * env(len(t), 0.0005, 0.004)
def gulp():
    t = t_(0.35); f = 260 - 140 * t / 0.35
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.02, 0.12) + 0.4 * squelch(0.35, 300)
def rumble(d):
    t = t_(d); x = lp(noise(d), 90, 2); return x / (np.abs(x).max() + 1e-9) * np.minimum(1, t / 0.4)
def beep(d, f0=1000, per=0.9):
    x = np.zeros(int(SR * d)); tt_ = t_(0.12); s = np.sin(2 * np.pi * f0 * tt_) * env(len(tt_), 0.003, 0.08)
    for k in range(int(d / per)):
        i = int(k * per * SR); x[i:i + len(s)] += s[: len(x) - i]
    return x
def roll(d, fc=500):
    t = t_(d); x = bp(noise(d), 80, fc) * (0.8 + 0.2 * np.sin(2 * np.pi * 11 * t)); return x / (np.abs(x).max() + 1e-9)
def clock(d):
    x = np.zeros(int(SR * d))
    for k in range(int(d * 8)): s = tick(1500 if k % 2 else 1100); i = int(k / 8 * SR); x[i:i + len(s)] += s[: len(x) - i]
    return x

def sneeze_snd(d=0.5):                               # "apchi" — havo portlashi
    t = t_(d); return bp(noise(d), 500, 7000) * env(len(t), 0.004, 0.12) + 0.4 * thud(110, d, 0.05)
def muffled(d=0.35):                                 # yopilgan aksirish: bo'g'iq "mpf"
    return lp(sneeze_snd(d), 450, 2) * 2.5
def inhale(d=1.0):
    t = t_(d); return bp(noise(d), 600, 4000) * (t / d) ** 1.5 * 0.5
def pop(f0=2500):                                    # quloq "chiq"
    t = t_(0.1); return np.sin(2 * np.pi * f0 * t) * env(len(t), 0.0005, 0.02) + 0.3 * thud(200, 0.1, 0.02)
def qirs():                                          # "qirs" — to'qima yirtilishi
    return mixs(crackle(0.25) * 1.6, 0.6 * thud(140, 0.25, 0.04), squelch(0.2, 600) * 0.5)
def city(d):
    t = t_(d); x = bp(noise(d), 100, 1500); return x / (np.abs(x).max() + 1e-9) * 0.7
def steps(d, per=0.52):
    x = np.zeros(int(SR * d))
    for k in range(int(d / per)):
        s = thud(160, 0.12, 0.02) * 0.6 + hp(noise(0.12), 2000) * env(int(SR * 0.12), 0.001, 0.01) * 0.3
        i = int(k * per * SR); x[i:i + len(s)] += s[: len(x) - i]
    return x

tt = np.arange(len(out)) / SR
room = lp(noise(DUR), 300, 2); room /= np.abs(room).max()
out += room * 0.03

import json, os
EV = json.load(open(sys.argv[2])) if len(sys.argv) > 2 and os.path.exists(sys.argv[2]) else []

def boing(d=0.7, f0=170, depth=0.5):                  # prujina "boing"
    t = t_(d); f = f0 * (1 + 0.7 * np.exp(-t / 0.06)) * (1 + 0.12 * np.sin(2 * np.pi * 9 * t) * np.exp(-t / 0.3))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = (np.sin(ph) + 0.35 * np.sin(2.01 * ph) + 0.15 * np.sin(3.7 * ph)) * env(len(t), 0.003, d / 3)
    return x * (0.6 + depth) + 0.4 * thud(55, d, 0.08)
def fwump(d=0.5):                                     # choyshabga yumshoq tushish
    return lp(noise(d), 300) * env(int(SR * d), 0.004, 0.08) * 2.5 + 0.6 * thud(45, d, 0.1)
def wood_crack():
    d = 0.9; n = noise(d); t = t_(d)
    snaps = np.zeros(len(t))
    for k in range(9):
        i = int(SR * (0.012 * k + rng.uniform(0, 0.01))); snaps[i:i + 400] += rng.uniform(0.5, 1) * np.exp(-np.arange(400) / 60)
    return bp(n, 600, 6000) * env(len(t), 0.001, 0.12) * 1.2 + bp(snaps * n, 300, 8000) * 3 + thud(70, d, 0.2)
def clank(f0=520):
    d = 1.4; t = t_(d)
    return sum(np.sin(2 * np.pi * f0 * r * t) * np.exp(-t / (0.5 / r)) for r in (1, 2.76, 5.4, 8.9)) * 0.4 + 0.5 * bp(noise(d), 2000, 9000) * env(len(t), 0.001, 0.01)
def ting(f0=2600):
    d = 0.35; t = t_(d); return np.sin(2 * np.pi * f0 * t) * np.exp(-t / 0.06) + 0.3 * np.sin(2 * np.pi * f0 * 2.7 * t) * np.exp(-t / 0.03)
def flap(d=1.5):                                     # mato silkinishi
    t = t_(d); a = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 7 * t + 3 * np.sin(2 * np.pi * 1.3 * t)))
    return bp(noise(d), 300, 3000) * lp(a, 40) * fade(np.ones(len(t)), 0.1, 0.3)
def tok():                                            # g'isht qo'yilishi
    return bp(noise(0.2), 400, 2500) * env(int(SR * 0.2), 0.001, 0.03) * 1.5 + 0.5 * thud(120, 0.2, 0.04)
def zipper(d=0.6):
    t = t_(d); clicks = (np.sin(2 * np.pi * (40 + 60 * t / d) * t) > 0.95).astype(float)
    return bp(clicks * noise(d), 1500, 8000) * 2.0 * fade(np.ones(len(t)), 0.05, 0.1)
def rustle(d=0.8): return bp(noise(d), 1500, 7000) * env(int(SR * d), 0.01, 0.2) * 1.2
def chirp(f0=3200):
    d = 0.18; t = t_(d); f = f0 * (1 + 0.4 * np.sin(np.pi * t / d)); return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.01, 0.05)
def stinger():
    d = 1.2; t = t_(d); x = sum(np.sin(2 * np.pi * f * t) for f in (261.6, 329.6, 392.0, 523.3)) * env(len(t), 0.005, 0.4)
    return x * 0.4 + thud(60, d, 0.25)

SHOTS = (65, 118, 197, 249, 314, 406, 483, 509, 583, 660, 763, 852, 936, 978, 1073, 1125, 1173, 1237)
for f in SHOTS: add(T(f) - 0.28, whoosh(0.4, 1800, 0.8), 0.14)
# fon: qushlar va basseyn suvi
for k in range(40): add(rng.uniform(0, DUR - 1), chirp(rng.uniform(2600, 4200)), 0.05)
add(0, waves(DUR) * 0.6, 0.05)
add(T(65), splash(0.8), 0.25); add(T(85), splash(0.6), 0.15)
# 1-2: yerda sakrashlar
for f in (24, 77): add(T(f), thud(80, 0.3, 0.05), 0.5); add(T(f), rustle(0.3), 0.15)
# 3: choyshab tortiladi
add(T(128), flap(2.0), 0.35); add(T(165), whoosh(0.5, 1200, 0.7), 0.3)
# 6: devor qator-qator o'sadi
for i in range(1, 11): add(T(328 + int((375 - 328) * i / 10)), tok(), 0.5)
add(T(318), riser(T(390) - T(318)), 0.15)
# 7: prujinalar ilinadi
for f in range(416, 480, 3): add(T(f), ting(rng.uniform(2200, 3000)), 0.12); add(T(f), tick(1800), 0.2)
# 8: Dahaa!
add(T(483), stinger(), 0.7)
# choyshab/batutga tushishlar (sahnadan)
last = -99
for f, obj, dep in EV:
    if f - last < 8: last = f; continue
    last = f
    if obj == "sheetA": add(T(f), fwump(), 0.55 + 0.3 * dep)
    else: add(T(f), boing(0.8, 150 + 60 * (0.6 - dep), dep), 0.35 + 0.4 * dep); add(T(f), creak(0.4, 160), 0.08)
# 10: baland otilish
add(T(598), whoosh(1.2, 900, 0.3), 0.5); add(T(598), riser(1.0), 0.15)
# 11: yog'och sinadi
add(T(736), wood_crack(), 1.0); add(T(737), thud(45, 1.0, 0.3), 0.9)
# 12: temir rama
add(T(763), clank(480), 0.35); add(T(770), ting(3600), 0.2); add(T(785), clank(620), 0.2)
# 14: tiqilish
add(T(940), thud(60, 0.6, 0.12), 0.9); add(T(940), creak(0.8, 120), 0.35); add(T(941), clank(900), 0.15)
# 15: qoplama tushadi
add(T(1000), whoosh(0.8, 700, 0.8), 0.3); add(T(1022), fwump(0.6), 0.8)
# 17: jiyan uchib ketadi, butaga tushadi
add(T(1126), whoosh(1.0, 1500, 0.4), 0.45); add(T(1158), rustle(1.0), 0.7); add(T(1158), thud(90, 0.4, 0.08), 0.5)
# 18: to'r ustunlari va to'r
for j in range(8): add(T(1179 + j * 2 + 10), whoosh(0.25, 2400, 0.7), 0.12)
add(T(1192), zipper(0.9), 0.45)
# 19: final — juda baland
add(T(1279), whoosh(1.5, 800, 0.35), 0.5); add(T(1300), stinger() * 0.6, 0.4); add(T(1295), splash(0.8), 0.25)
out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
