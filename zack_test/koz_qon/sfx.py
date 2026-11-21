# "Ko'zdagi qizil dog'" videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/koz_qon/sfx.py /tmp/claude-0/audio/sfx_koz.wav
import sys, wave
import numpy as np

SR = 48000; DUR = 37.3
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
def gull(d=0.8):
    t = t_(d); f = 1500 + 700 * np.sin(np.pi * t / d) - 600 * (t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)) * env(len(t), 0.05, d / 2.5) * 0.4
def moo(d=1.6):
    t = t_(d); f = 135 - 30 * t / d
    ph = 2 * np.pi * np.cumsum(f) / SR
    saw = sum(np.sin(k * ph) / k for k in range(1, 30))
    return bp(saw, 180, 1100) * np.minimum(1, t / 0.15) * np.exp(-np.maximum(0, t - d * 0.6) / 0.2)
def sneeze():                                         # "a-a-apchxi!": nafas olish + keskin shovqin
    a = bp(noise(0.45), 500, 3000) * np.linspace(0, 1, int(SR * 0.45)) ** 2 * 0.25
    b = bp(noise(0.35), 900, 7000) * env(int(SR * 0.35), 0.003, 0.08)
    return np.concatenate([a, b])
def creak(d=0.6):                                     # shtanga temiri g'ichirlashi
    t = t_(d); f = 90 + 30 * np.sin(2 * np.pi * 1.5 * t)
    return bp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5 + 0.5 * noise(d), 200, 2500) * env(len(t), 0.05, d / 2)
def pop():                                            # tomir yorilishi: ho'l "pat"
    return thud(140, 0.3, 0.04) * 0.6 + bp(noise(0.3), 400, 4000) * env(int(SR * 0.3), 0.001, 0.03)
def tick(f0=2200):
    t = t_(0.05); return np.sin(2 * np.pi * f0 * t) * env(len(t), 0.0005, 0.01)
def clock_ticks(d, rate=8):
    x = np.zeros(int(SR * d))
    for k in range(int(d * rate)):
        y = tick(1800 if k % 2 else 2400); i = int(k / rate * SR); x[i:i + len(y)] += y[: len(x) - i]
    return x

tt = np.arange(len(out)) / SR
drone = sum(np.sin(2 * np.pi * f * tt) for f in (55, 65.4, 82.4)) / 3 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.1 * tt))
out += drone * (0.02 + 0.025 * np.clip((tt - 10) / 20, 0, 1))
# vushlar (kesishlarda)
for f in (19, 47, 82, 113, 142, 216, 248, 294, 365, 411, 473, 535, 621, 689, 769, 827):
    add(T(f) - 0.4, whoosh(0.55, 1600, 0.75), 0.2)
# ilgak: crash zoom zarbasi
add(T(1), thud(50, 1.0, 0.35), 0.6); add(T(1), whoosh(0.3, 3000, 0.1), 0.25)
# aksirish
add(T(19) + 0.05, sneeze(), 0.55); add(T(28), thud(70, 0.5, 0.12), 0.25)
# shtanga: temir g'ichirlashi, og'ir nafas
add(T(50), creak(0.7), 0.15); add(T(85), creak(0.9), 0.15)
add(T(84), bp(noise(0.9), 250, 1200) * env(int(SR * 0.9), 0.2, 0.4), 0.15)
# "to'satdan": dog' paydo bo'ladi — zarba
add(T(178), thud(46, 1.6, 0.55), 0.8); add(T(178) - 0.15, whoosh(0.3, 3000, 0.8), 0.3)
# qo'rqib ketdi
add(T(248), thud(55, 1.0, 0.35), 0.5)
# sho'ng'ish: ko'tariluvchi tovush
add(T(300), riser(T(365) - T(300)), 0.18)
# tomir yorilishi (1 va 2): yurak urishi tezlashadi, keyin "pat"
for k in range(3): add(T(365) + k * 0.33, heartbeat(), 0.35)
add(T(395), pop(), 0.8); add(T(395), thud(48, 1.2, 0.4), 0.6)
for k in range(3): add(T(621) + k * 0.45, heartbeat(), 0.35)
add(T(667), pop(), 0.8); add(T(667), thud(48, 1.2, 0.4), 0.6)
# rentgen: yurak urishi
for k in range(4): add(T(413) + k * 0.65, heartbeat(), 0.5)
# manometr: tiqillash, strelka sakraydi
add(T(473), clock_ticks(T(515) - T(473), 10), 0.12)
add(T(515), thud(44, 1.4, 0.5), 0.75); add(T(515) - 0.1, whoosh(0.25, 3500, 0.8), 0.35)
add(T(515), bp(noise(0.6), 1500, 6000) * env(int(SR * 0.6), 0.002, 0.15), 0.15)
# qon sizib chiqishi: ho'l tovushlar
for k in range(6): add(T(695 + k * 11), squelch(0.25, 300 + 20 * k), 0.12)
# yengil tin olish: yumshoq akkord
t = t_(2.4); add(T(769), sum(np.sin(2 * np.pi * f * t) for f in (261.6, 329.6, 392.0)) / 3 * env(len(t), 0.3, 1.0), 0.12)
# time-lapse: soat tiqillashi, oxirida pirpirash zarbasi
add(T(827), clock_ticks(T(880) - T(827), 12), 0.1)
add(T(883), thud(45, 1.8, 0.6), 0.8); add(T(883) - 0.1, whoosh(0.25, 3500, 0.8), 0.3)

out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
