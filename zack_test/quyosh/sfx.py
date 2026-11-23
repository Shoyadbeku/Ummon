# "Quyoshga tikilish" videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/quyosh/sfx.py /tmp/claude-0/audio/sfx_quyosh.wav
import sys, wave
import numpy as np

SR = 48000; DUR = 41.75
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

def sizzle(d):                                       # kuyish/cho'g' chirsillashi
    x = bp(noise(d), 2000, 9000) * 0.25
    for k in range(int(d * 60)):
        i = int(rng.uniform(0, d) * SR); c = bp(noise(0.01), 1500, 8000) * env(int(SR * 0.01), 0.0005, 0.002)
        x[i:i + len(c)] += c[: len(x) - i] * rng.uniform(0.5, 2.0)
    return fade(x, 0.15, 0.3)
def zap(d=0.5):                                       # ultrabinafsha nur: yuqori "vjjj"
    t = t_(d); f = 2400 - 1600 * t / d
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4 + bp(noise(d), 3000, 9000) * 0.5) * env(len(t), 0.01, d / 2)
def hum(d, f0=110):                                   # Quyosh "g'uvillashi"
    t = t_(d); x = sum(np.sin(2 * np.pi * f0 * k * t + k) / k for k in (1, 2, 3, 5))
    return fade(lp(x + 0.6 * lp(noise(d), 300), 900), 0.3, 0.4)

tt = np.arange(len(out)) / SR
drone = sum(np.sin(2 * np.pi * f * tt) for f in (55, 65.4, 82.4)) / 3 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.1 * tt))
out += drone * (0.02 + 0.025 * np.clip((tt - 14) / 20, 0, 1))
# vushlar (kesishlarda)
for f in (21, 68, 125, 168, 255, 328, 409, 463, 549, 598, 648, 697, 781, 847, 934):
    add(T(f) - 0.4, whoosh(0.55, 1600, 0.75), 0.2)
# ilgak: crash zoom zarbasi + yorqin "ting"
add(T(1), thud(50, 1.0, 0.35), 0.6); add(T(1), whoosh(0.3, 3000, 0.1), 0.25)
# ko'cha: shamol, uzoqda shahar shovqini
for a, b in ((21, 67), (409, 462), (648, 696), (934, 1001)):
    add(T(a), fade(lp(noise(T(b) - T(a)), 500) * 0.5, 0.1, 0.2), 0.12)
# lupa: nur nuqtasi qiziydi, qog'oz chirsillab kuyadi
add(T(80), riser(T(131) - T(80)), 0.12)
add(T(131), sizzle(T(168) - T(131)), 0.35); add(T(133), thud(70, 0.6, 0.15), 0.35)
# gavhar yonadi: yumshoq akkord
t = t_(2.5); add(T(200), sum(np.sin(2 * np.pi * f * t) for f in (329.6, 415.3, 493.9)) / 3 * env(len(t), 0.3, 1.2), 0.1)
# Quyosh: past g'uvillash, uchib o'tayotgan nurlar
add(T(255), hum(T(328) - T(255)), 0.35)
for k in range(7): add(T(262 + k * 9), zap(0.45), 0.12)
# nurlar yig'iladi -> "uradi"
add(T(340), riser(T(390) - T(340)), 0.2)
add(T(390), thud(44, 1.6, 0.55), 0.85); add(T(390) - 0.1, whoosh(0.25, 3500, 0.8), 0.35); add(T(390), zap(0.6), 0.3)
# asab tolalari: elektr impulslar
for k in range(8): add(T(470 + k * 10), tick(1400 + 100 * k) * 0.8, 0.35)
# hujayralar kuyadi
add(T(598), riser(T(612) - T(598)), 0.15)
add(T(612), thud(48, 1.2, 0.4), 0.7); add(T(612), sizzle(T(648) - T(612)), 0.4)
# soatlar o'tadi: soat tiqillashi
add(T(697), clock_ticks(T(781) - T(697), 10), 0.12)
# qora dog' paydo bo'ladi: past zarba
add(T(806), thud(42, 2.0, 0.7), 0.85); add(T(806) - 0.12, whoosh(0.3, 2500, 0.8), 0.3)
# kitob: varaq shitirlashi
add(T(850), bp(noise(0.35), 1500, 7000) * env(int(SR * 0.35), 0.02, 0.1), 0.15)
# ko'zoynak: nurlar o'tib ketadi, oxirgi zarba
for k in range(4): add(T(938 + k * 5), zap(0.4), 0.12)
add(T(981), thud(45, 1.5, 0.6), 0.7)

out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
