# "Oq ko'ylakdagi qora nuqta" videosi uchun tovush effektlari (sintez) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/nuqta/sfx.py /tmp/claude-0/audio/sfx_nuqta.wav
# Yordamchi funksiyalar tirnoq/sfx.py dan; voqealar kadrlari tirnoq_osishi.py bilan bir xil.
import sys, wave
import numpy as np

SR = 48000; DUR = 41.6
rng = np.random.default_rng(17)
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
def pad(d, freqs=(220, 277, 330, 415), trem=0.3):     # tush: yumshoq akkord
    t = t_(d); x = sum(np.sin(2 * np.pi * f * t + k) for k, f in enumerate(freqs)) / len(freqs)
    return fade(x * (1 - trem + trem * np.sin(2 * np.pi * 0.7 * t)), 0.4, 0.6)
def shing(d=1.0):                                    # pichoq tig'i yaltirashi
    t = t_(d); x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t / (d / k)) for k, f in ((2, 3100), (3, 4650), (4, 6200)))
    return mixs(x * env(len(t), 0.003, d) * 0.4, whoosh(0.4, 5000, 0.2) * 0.3)
def pop(f0=900):                                     # pufak "pop"
    t = t_(0.12); f = f0 * (1 + 2.0 * np.exp(-t / 0.01))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.001, 0.03)
def marker_squeak(d=0.5):                            # marker "g'irch" (mato ustida)
    t = t_(d); f = 1800 + 500 * np.sin(2 * np.pi * 6 * t)
    return (0.3 * np.sin(2 * np.pi * np.cumsum(f) / SR) + bp(noise(d), 2500, 7000)) * fade(np.ones(len(t)), 0.02, 0.1) * 0.6
def chime(d=1.4, f0=880):                            # yaxshi narsa "dzing"
    t = t_(d); return sum(np.sin(2 * np.pi * f0 * k * t) * np.exp(-t / (d / (k + 1))) / k for k in (1, 2, 3)) * env(len(t), 0.002, d)
def sting(d=1.2):                                    # salbiy "dum"
    t = t_(d); x = sum(np.sin(2 * np.pi * f * t) for f in (55, 58.3, 82.4)) / 3
    return mixs(x * env(len(t), 0.005, 0.5), thud(45, d, 0.35) * 0.8)

# ---------------- voqealar (kadrlar) — nuqta.py bilan bir xil ----------------
SHOTS = [1, 32, 62, 111, 147, 184, 208, 230, 290, 344, 410, 469, 506, 568, 630, 727, 790, 863, 936]
F_DOT, F_HEART0, F_SAD = 83, 516, 607
for f in SHOTS[1:]: add(T(f) - 0.22, whoosh(0.4, 1900, 0.6), 0.3)
add(0.0, whoosh(1.0, 900, 0.85), 0.45)
add(T(1), lp(noise(T(506)), 450) * 0.035)                     # sinf shovqini
add(T(F_DOT) - 0.05, marker_squeak(0.55), 0.7)
add(T(F_DOT), thud(90, 0.4, 0.06), 0.6)
add(T(208), mixs(thud(60, 0.6, 0.15), whoosh(0.3, 4000, 0.2) * 0.5), 0.8)    # crash zoom
add(T(184), riser(0.35), 0.15)
add(T(350), shing(1.4), 0.4); add(T(352), chime(1.6, 1046), 0.25)              # oq to'lqin
add(T(410), pad(2.2, (196, 233, 294)) * 0.25)                                # hech kim
for k in range(10): add(T(F_HEART0 + k * 3), pop(700 + k * 70), 0.45)
add(T(F_HEART0 + 29), chime(1.2, 1318), 0.35)
add(T(580), whoosh(0.35, 2500, 0.4), 0.45)                                   # qo'l siltash
add(T(F_SAD), sting(1.4), 0.75)
for k in range(3): add(T(630 + 12 + k * 7), pop(1100 + k * 150), 0.4)
add(T(630 + 38), mixs(pop(600), whoosh(0.3, 3000, 0.3) * 0.4), 0.6)
add(T(727), hiss(1.0), 0.25); add(T(727), zap(0.4), 0.25)
for k in range(5): add(T(790 + 4 + k * 3), pop(900 + k * 80), 0.3)
add(T(820), sting(1.5), 0.8); add(T(820) - 0.5, riser(0.5), 0.25)
add(T(863), thud(70, 0.6, 0.2), 0.5)
add(T(936) - 0.3, whoosh(0.6, 1200, 0.5), 0.4)
add(T(936), pad(T(998) - T(936), (220, 277, 330)) * 0.2)
x = out / (np.abs(out).max() + 1e-9) * 0.9
x[-int(SR * 0.3):] *= np.linspace(1, 0, int(SR * 0.3))
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())
print("ok", len(x) / SR)
