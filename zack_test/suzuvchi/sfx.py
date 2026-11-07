# Ko'zdagi suzuvchilar videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/suzuvchi/sfx.py /tmp/claude-0/audio/sfx_suz.wav
import sys, wave
import numpy as np

SR = 48000; DUR = 43.6
rng = np.random.default_rng(9)
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
def chirp(d=0.12, f0=3200, f1=4600):
    t = t_(d); f = f0 + (f1 - f0) * (t / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) ** 2
def birds(d, seed=1):
    r = np.random.default_rng(seed); x = np.zeros(int(SR * d))
    for _ in range(int(d * 2.2)):
        s = r.uniform(0, d - 0.6); f0 = r.uniform(2500, 4200)
        for k in range(r.integers(2, 5)):
            c = chirp(r.uniform(0.06, 0.12), f0, f0 * r.uniform(1.1, 1.5)); i = int((s + k * 0.13) * SR)
            x[i:i + len(c)] += c[: len(x) - i] * r.uniform(0.3, 0.7)
    return x
def bubble(f0=300):
    d = 0.18; t = t_(d); f = f0 * (1 + 2.5 * t / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.003, 0.05)
def shimmer(d):
    t = t_(d); x = sum(np.sin(2 * np.pi * f * t + k) for k, f in enumerate((880, 1318, 1760, 2637))) / 4
    return x * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * t)) * np.minimum(1, t / (d * 0.4)) * np.minimum(1, (d - t) / 0.3)
def rub(d):
    t = t_(d); n = bp(noise(d), 400, 3000)
    return n * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 3.2 * t)))
def water(d):
    n = bp(noise(d), 500, 7000); t = t_(d)
    return n * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 2.5 * t)))

S = [1, 50, 100, 131, 177, 227, 287, 378, 484, 546, 614, 731, 801, 843, 878, 924, 990]
tt = np.arange(len(out)) / SR
# ochiq havo: qushlar, yengil shamol
for a, b in ((1, 130), (131, 176), (801, 877)):
    add(T(a), fade(birds(T(b + 1) - T(a), a), 0.1, 0.15), 0.07)
    add(T(a), fade(lp(noise(T(b + 1) - T(a)), 400) * 3, 0.1, 0.15), 0.03)
# xona: sokin xona shovqini
add(T(177), fade(lp(noise(T(227) - T(177)), 250) * 3, 0.05, 0.1), 0.03)
# ko'z ichi: past "suv osti" drone (kesim, gel, to'r parda, yakun)
for a, b in ((287, 800), (990, 1046)):
    seg = tt[int(T(a) * SR):int(min(T(b + 1), DUR) * SR)] - T(a)
    dr = sum(np.sin(2 * np.pi * f * seg) for f in (49, 73.4, 98)) / 3 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.25 * seg))
    add(T(a), fade(dr + 0.4 * lp(noise(len(seg) / SR), 180) * 3, 0.2, 0.3), 0.07)
# vushlar (har kesishda)
for f in S[1:]:
    add(T(f) - 0.4, whoosh(0.55, 1700, 0.75), 0.2)
# ilgak: kichik "tik"lar suzuvchilar sakraganda
for f in (19, 37, 818):
    add(T(f), thud(160, 0.15, 0.04), 0.12)
# qorachiqqa sho'ng'ish: ko'tariluvchi tovush + zarba
add(T(240), riser(T(287) - T(240)), 0.3); add(T(287), thud(45, 1.6, 0.55), 0.85)
# gel: yumshoq "shalop"
for k in range(4): add(T(390 + k * 22), squelch(0.25, 260 + 30 * k), 0.06)
# suyuqlashish: pufakchalar
r_ = np.random.default_rng(4)
for k in range(16): add(T(488) + k * 0.15 + r_.uniform(0, 0.08), bubble(r_.uniform(250, 700)), 0.12)
# tolalar yopishadi: tortiluvchi tovush, oxirida zarba
add(T(556), riser(T(606) - T(556)), 0.2); add(T(606), thud(55, 1.0, 0.35), 0.55)
# nur kiradi
add(T(614), shimmer(T(700) - T(614)), 0.1)
# to'r pardadagi soya: chuqur zarba
add(T(731), thud(42, 1.5, 0.5), 0.6)
# ishqalash, yuvish
add(T(843), fade(rub(T(878) - T(843)), 0.03, 0.06), 0.18)
add(T(878), fade(water(T(924) - T(878)), 0.05, 0.2), 0.16)
for k in range(5): add(T(882) + k * 0.25, squelch(0.12, 700), 0.1)
# ho'l ko'z: pirpirash
add(T(925), squelch(0.12, 500), 0.12); add(T(964), squelch(0.12, 520), 0.12)
# yakun
add(T(990), thud(48, 1.8, 0.6), 0.5); add(T(1032), thud(40, 2.0, 0.8), 0.7)

out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
