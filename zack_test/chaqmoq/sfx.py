# "Chaqmoq" videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/bvenv/bin/python -I zack_test/chaqmoq/sfx.py /tmp/claude-0/audio/sfx_chaqmoq.wav
import sys, wave
import numpy as np

SR = 48000; DUR = 54.67
rng = np.random.default_rng(21)
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
def hic(pitch=1.0):                                 # "hik!": glottis chertishi + qisqa ovoz (formantlar)
    d = 0.16; t = t_(d)
    click = bp(noise(0.012), 800, 9000) * env(int(SR * 0.012), 0.0005, 0.003)
    f0 = 260 * pitch * (1 + 0.25 * np.exp(-t / 0.02))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    src = sum(np.sin(k * ph) / k for k in range(1, 25))
    voc = bp(src, 300, 3200) * np.minimum(1, t / 0.006) * np.exp(-t / 0.035)
    breath = bp(noise(d), 1200, 6000) * env(len(t), 0.002, 0.03) * 0.5
    x = voc * 0.9 + breath; x[: len(click)] += click * 1.2
    return x
def inhale(d=0.5):                                  # keskin havo tortish
    t = t_(d); return bp(noise(d), 900, 5000) * (t / d) ** 2 * np.exp(-np.maximum(0, t - d * 0.85) / 0.02)
def slam(d=0.5):                                    # yopilish: ho'l "tap" + zarba
    x = thud(70, d, 0.12) * 0.8; q = squelch(0.15, 700); x[:len(q)] += q * 0.6
    return x


def thunder(d=3.5, crack=1.0):                      # chaqmoq: keskin "chars" + uzoq gumburlash
    t = t_(d); n = noise(d)
    cr = hp(n, 1200) * env(len(t), 0.001, 0.05) * crack
    rum = lp(noise(d), 160, 2) * (np.minimum(1, t / 0.08) * np.exp(-t / (d / 3))) * (1 + 0.6 * np.sin(2 * np.pi * 3.3 * t))
    mid = bp(noise(d), 150, 900) * env(len(t), 0.005, 0.35)
    x = cr * 0.9 + rum * 6.0 + mid * 1.2
    return x / np.abs(x).max()
def far_thunder(d=4.0):
    t = t_(d); x = lp(noise(d), 120, 2) * np.sin(np.pi * np.minimum(1, t / d)) ** 0.7 * (1 + 0.5 * np.sin(2 * np.pi * 2.1 * t))
    return x / np.abs(x).max()
def buzz_e(d, f0=100):                              # elektr g'uvillashi (50/100 Hz, tishli)
    t = t_(d); ph = 2 * np.pi * f0 * t * (1 + 0.01 * np.sin(2 * np.pi * 7 * t))
    saw = sum(np.sin(k * ph) / k for k in range(1, 30))
    x = bp(saw, 80, 6000) * (0.7 + 0.3 * np.sign(np.sin(2 * np.pi * 13 * t)))
    return fade(x / np.abs(x).max(), 0.01, 0.1)
def hiss(d):                                        # bug' vishillashi
    t = t_(d); return fade(bp(noise(d), 2500, 11000) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.8 * t)), 0.3, 0.3)
def rain(d):
    x = bp(noise(d), 400, 9000) * 0.6 + lp(noise(d), 300) * 0.4
    return fade(x, 0.15, 0.15)
def pop(d=0.25):
    t = t_(d); return (bp(noise(d), 200, 5000) * env(len(t), 0.0005, 0.03) + np.sin(2 * np.pi * 90 * t) * env(len(t), 0.001, 0.06))
def beep(d, f0=1000):
    t = t_(d); return np.sin(2 * np.pi * f0 * t) * np.minimum(1, t / 0.005) * np.minimum(1, (d - t) / 0.01)
def roar(d):                                        # quyosh/plazma shovqini
    t = t_(d); return fade(lp(noise(d), 500, 2) + 0.4 * bp(noise(d), 500, 3000), 0.2, 0.3)

FIELD_RANGES = [(1, 98), (404, 447), (507, 768), (898, 1177)]
for a, b in FIELD_RANGES:
    add(T(a), rain(T(b + 1) - T(a) + 0.05), 0.07)
# kesimlarda havo "vish"i
for f in (32, 62, 99, 191, 266, 337, 404, 448, 507, 578, 625, 674, 769, 818, 898, 947, 1056, 1120, 1178, 1263):
    add(T(f) - 0.3, whoosh(0.4, 1800, 0.8), 0.18)
# 1 uzoq momaqaldiroq, 2 zarba
add(T(12), far_thunder(3.0), 0.35)
add(T(32), riser(T(36) - T(32)), 0.12)
add(T(36), thunder(4.0), 1.0)
# 2-4 elektr toki (yuz, rentgen)
add(T(36), buzz_e(T(191) - T(36), 100), 0.22); add(T(36), crackle(T(191) - T(36)), 0.3)
add(T(99), zap(1.0), 0.25)
# 5-6 plazma va quyosh
add(T(191), roar(T(337) - T(191)), 0.2); add(T(191), crackle(T(266) - T(191)), 0.35)
# 7 tok teri ustida
add(T(337), zap(0.8), 0.3); add(T(337), crackle(T(404) - T(337)), 0.35)
# 8 daraxt fonida chaqnashlar
add(T(412), thunder(2.5, 0.4), 0.45); add(T(431), far_thunder(2.5), 0.3)
# 9 naqsh: past dron
t = t_(T(507) - T(448)); add(T(448), np.sin(2 * np.pi * 55 * t) * np.sin(np.pi * t / t[-1]), 0.1)
add(T(540), far_thunder(3.0), 0.3); add(T(600), far_thunder(3.0), 0.3)
# 11-13 bug'
add(T(578), hiss(T(769) - T(578)), 0.12); add(T(625), riser(T(640) - T(625)) * 0.6, 0.12); add(T(640), hiss(1.2), 0.25)
# 13 krossovkalar uchadi
add(T(735), thunder(2.0, 0.8), 0.6); add(T(735), pop(), 0.6); add(T(735), whoosh(0.9, 2200, 0.3), 0.35)
# 14 quloq pardasi yoriladi + shang'illash
add(T(771), whoosh(0.8, 900, 0.9), 0.3); add(T(795), pop(0.3), 0.9); add(T(795), thud(60, 0.6, 0.15), 0.6); add(T(796), ring(2.0, 3600), 0.5)
# 15 yurak uradi -> to'xtaydi (monitor)
for f in range(812, 858, 12): add(T(f), heartbeat(), 0.5); add(T(f), beep(0.08), 0.06)
add(T(858), beep(T(898) - T(858) - 0.1), 0.06)
# 16 nafas oladi
add(T(906), inhale(0.5), 0.5)
# 17 10 kishi: chiroqlar "chiq" + yiqilish
for k in (0, 3, 6, 9, 12, 15, 18, 21, 24): add(T(947 + 50 + k), tick(900), 0.25); add(T(947 + 50 + k), thud(90, 0.2, 0.03), 0.15)
add(T(975), far_thunder(3.0), 0.3); add(T(1025), thud(55, 0.6, 0.15), 0.5)
# 18-19 daraxt
add(T(1075), far_thunder(2.5), 0.3); add(T(1100), far_thunder(2.5), 0.25)
add(T(1127), riser(T(1131) - T(1127)), 0.12); add(T(1131), thunder(4.0), 1.0); add(T(1131), crackle(1.5), 0.4); add(T(1150), thud(60, 0.5, 0.12), 0.4)
# 20-21 minora: uch zarba
for f in (1215, 1240, 1250, 1290): add(T(f), thunder(3.0, 0.9), 0.8)
t = t_(1.6); add(T(1300), (np.sin(2 * np.pi * 880 * t) + 0.6 * np.sin(2 * np.pi * 1320 * t)) * env(len(t), 0.002, 0.5) * 0.3, 0.25)

out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
