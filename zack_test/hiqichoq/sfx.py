# Hiqichoq videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/hiqichoq/sfx.py /tmp/claude-0/audio/sfx_hiqichoq.wav
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

JOLTS = [10, 66, 601, 796, 934]
tt = np.arange(len(out)) / SR
drone = sum(np.sin(2 * np.pi * f * tt) for f in (49, 73.4, 98)) / 3 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.1 * tt))
out += drone * (0.012 + 0.025 * np.clip((tt - 4) / 10, 0, 1)) * np.clip((39.6 - tt) / 1.5, 0, 1)
for f in (47, 105, 134, 216, 280, 323, 380, 426, 497, 576, 631, 676, 741, 783, 845):
    add(T(f) - 0.35, whoosh(0.45, 1700, 0.8), 0.2)
for i, f in enumerate(JOLTS):                        # har hiqichoqda: havo tortish + "hik" + yengil zarba
    add(T(f) - 0.12, inhale(0.14), 0.25); add(T(f), hic(1.0 + 0.06 * (i % 3)), 0.9); add(T(f), thud(80, 0.3, 0.06), 0.3)
# 3-4 rentgen: o'pka/diafragma — yurak urishi
for f in range(112, 214, 16): add(T(f), heartbeat(), 0.35)
# 5-6 nafas: chuqur havo oqimi
add(T(220), lp(noise(4.4), 900) * np.sin(np.pi * t_(4.4) / 4.4), 0.18)
# 9 asab: elektr uchqunlari
add(T(430), zap(1.4), 0.22); add(T(440), crackle(2.2), 0.25)
# 10 kasilish: chiyillash -> zarba
add(T(510), riser(T(543) - T(510)), 0.15); add(T(543), thud(42, 1.4, 0.45), 0.95); add(T(543), inhale(0.3), 0.35)
# 12 bo'yin: havo yuqoriga yuguradi
add(T(632), riser(T(675) - T(632)) * 0.5, 0.12)
# 13 ovoz yo'li yopiladi
add(T(728), slam(0.6), 0.9)
# 14 havo uriladi: zarba + jaranglash
add(T(744), riser(T(758) - T(744)), 0.15); add(T(758), thud(55, 1.0, 0.3), 0.8); add(T(758), splash(0.4), 0.25)
# 16 yakun: savol ohangidagi qo'ng'iroqcha
t = t_(1.8); add(T(880), (np.sin(2 * np.pi * 880 * t) + 0.6 * np.sin(2 * np.pi * 1320 * t)) * env(len(t), 0.002, 0.6) * 0.3, 0.3)

out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
