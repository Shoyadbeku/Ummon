# Ebbi videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/ebbi/sfx.py /tmp/claude-0/audio/sfx_ebbi.wav
import sys, wave
import numpy as np

SR = 48000; DUR = 55.0
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
def waves(d):
    n = lp(noise(d), 700, 2); t = t_(d)
    sw = 0.55 + 0.45 * np.sin(2 * np.pi * t / 4.5) ** 2
    return n / (np.abs(n).max() + 1e-9) * sw

tt = np.arange(len(out)) / SR
# fon: past drone (keskinlik), oxirida kuchayadi
drone = sum(np.sin(2 * np.pi * f * tt) for f in (55, 65.4, 82.4)) / 3 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.1 * tt))
out += drone * (0.02 + 0.03 * np.clip((tt - 17) / 20, 0, 1))
# dengiz va chaykalar (kema kadrlari)
for a, b in ((41, 88), (89, 122), (123, 154), (155, 183), (231, 277), (841, 870), (1096, 1189)):
    add(T(a), fade(waves(T(b + 1) - T(a)), 0.05, 0.1), 0.18)
for f in (50, 130, 160, 1110, 1160): add(T(f), gull(0.7), 0.12)
# yaylov: shamol, sigir mo'raydi
add(T(717), fade(lp(noise(T(775) - T(717)), 500) * 3, 0.05, 0.1), 0.05); add(T(720), moo(1.3), 0.25)
# vushlar (kesishlarda)
for f in (41, 123, 184, 278, 341, 507, 623, 659, 717, 747, 841, 916, 981, 1033, 1096, 1190, 1244):
    add(T(f) - 0.45, whoosh(0.6, 1600, 0.75), 0.22)
# ilgak: qovoq ostida qimirlash
for k in range(4): add(T(8 + k * 8), squelch(0.18, 380 + 40 * k), 0.12)
# qizarish: past "bum"
add(T(184), thud(70, 0.8, 0.3), 0.3)
# tortib chiqarish: ho'l tovushlar, ko'tariluvchi tovush
for k in range(9): add(T(370 + k * 6), squelch(0.22, 420 + 30 * k), 0.18)
add(T(380), riser(T(428) - T(380)), 0.18)
# "Bu chuvalchang edi" — zarba
add(T(428), thud(48, 1.4, 0.5), 0.75); add(T(428), whoosh(0.3, 3000, 0.1), 0.25)
for k in range(5): add(T(435 + k * 7), squelch(0.15, 600), 0.08)
# "qo'rqib ketdi": crash zoom
add(T(469), thud(55, 1.0, 0.35), 0.6); add(T(469) - 0.2, whoosh(0.35, 2500, 0.8), 0.35)
# qovoq ostida, yana bittasi
for k in range(5): add(T(552 + k * 7), squelch(0.18, 450), 0.12)
add(T(589), thud(60, 0.8, 0.3), 0.55); add(T(589) - 0.15, whoosh(0.3, 3000, 0.8), 0.3)
# Petri idishi: laboratoriya "ding"
t = t_(1.2); add(T(661), np.sin(2 * np.pi * 1760 * t) * env(len(t), 0.002, 0.4) * 0.3, 0.3)
# pashsha
add(T(818), buzz(T(841) - T(818), 200, [0.3, 1, 0.6]), 0.22)
add(T(841), buzz(T(871) - T(841), 120, [0.7, 1, 0.7]), 0.3)                      # sekinlashgan: pastroq
add(T(871), buzz(T(888) - T(871), 210, [0.3, 1, 0.8]), 0.25); add(T(888), thud(110, 0.2, 0.05), 0.15)
add(T(907), buzz(T(916) - T(907), 220, [1, 0.3]), 0.2)
add(T(1244), buzz(T(1290) - T(1244), 200, [0.1, 0.4, 1.0]), 0.3)
add(T(1290), buzz(0.6, 230, [1, 0.2]), 0.2)
# rentgen: yurak urishi
for k in range(3): add(T(918) + k * 0.85, heartbeat(), 0.5)
# 14 ta: har biri qisqa "tik"
for k in range(14):
    t = t_(0.08); add(T(1036) + k * 0.12, np.sin(2 * np.pi * (900 + 40 * k) * t) * env(len(t), 0.001, 0.02), 0.12)
# "dunyodagi birinchi odam": chuqur zarba
add(T(1152), thud(42, 2.0, 0.7), 0.6)
# ko'z keskin yumiladi: oxirgi zarba
add(T(1289), thud(45, 1.8, 0.6), 0.9); add(T(1289) - 0.1, whoosh(0.25, 3500, 0.8), 0.35)

out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
