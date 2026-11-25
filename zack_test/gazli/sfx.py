# "Gazli ichimlik" videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/gazli/sfx.py /tmp/claude-0/audio/sfx.wav
import sys, wave
import numpy as np

SR = 48000; DUR = 43.67
rng = np.random.default_rng(11)
out = np.zeros(int(SR * DUR))
def T(frame): return (frame - 1) / 24.0                       # kadr -> soniya
CUTS = [25, 53, 87, 119, 169, 221, 269, 319, 375, 417, 471, 519, 585, 621, 651, 683, 741, 781, 819, 863, 919, 967, 1011]

def t_(d): return np.arange(int(SR * d)) / SR
def env(n, a=0.005, decay=0.3):
    t = np.arange(n) / SR; return np.minimum(1, t / a) * np.exp(-t / decay)
def lp(x, fc, n=2):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / fc) ** 2) ** (n / 2), len(x))
def hp(x, fc): return x - lp(x, fc, 1)
def add(at, x, gain=1.0):
    i = int(at * SR); j = min(len(out), i + len(x))
    if i < len(out): out[i:j] += gain * x[: j - i]
def noise(d): return rng.standard_normal(int(SR * d))
def whoosh(d=0.6, fc=1200, peak=0.55):
    t = t_(d); shape = np.exp(-((t / d - peak) ** 2) / 0.03)
    return hp(lp(noise(d), fc, 2), fc * 0.2) * shape
def thud(f=60, d=0.5, decay=0.12):
    t = t_(d); sweep = f * (1 + 1.5 * np.exp(-t / 0.03))
    return np.sin(2 * np.pi * np.cumsum(sweep) / SR) * env(len(t), 0.002, decay) + 0.25 * lp(noise(d), 400) * env(len(t), 0.002, 0.04)
def heartbeat():
    return np.concatenate([thud(55, 0.25, 0.07), np.zeros(int(SR * 0.11)), 0.75 * thud(50, 0.4, 0.08)])
def fizz(d, density=900, gain=1.0):                            # gaz pufakchalari chirsillashi
    x = np.zeros(int(SR * d)); n = int(d * density)
    for _ in range(n):
        i = rng.integers(0, len(x) - 200); L = rng.integers(40, 160)
        f = rng.uniform(2500, 9000); tt = np.arange(L) / SR
        x[i:i + L] += np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.0015) * rng.uniform(0.1, 1)
    return x * gain
def plop(f=700):                                              # qand suvga tushishi
    t = t_(0.18); sweep = f * (1 + 2.0 * np.exp(-t / 0.02))
    return np.sin(2 * np.pi * np.cumsum(sweep) / SR) * env(len(t), 0.001, 0.05) + 0.3 * hp(noise(0.18), 2000) * env(len(t), 0.001, 0.02)
def gulp():                                                   # ho'plash
    t = t_(0.28); f = 180 * (1 + 0.8 * np.exp(-t / 0.05))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.01, 0.07) + 0.4 * lp(noise(0.28), 600) * env(len(t), 0.005, 0.05))
def beep(f=880, d=0.16):
    t = t_(d); return np.sin(2 * np.pi * f * t) * np.minimum(1, t / 0.005) * np.minimum(1, (d - t) / 0.02)
def riser(d, f0, f1):
    t = t_(d); f = f0 * (f1 / f0) ** (t / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / d) ** 2

# fon: xona shovqini + past drone
tt = np.arange(len(out)) / SR
amb = lp(noise(DUR), 300, 3); amb /= np.abs(amb).max()
out += amb * 0.03
drone = sum(np.sin(2 * np.pi * f * tt) for f in (55, 82.4, 110)) / 3 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.2 * tt))
out += drone * (0.015 + 0.02 * ((tt > T(683)) & (tt < T(863))))

# 1: banka ochilishi (chiq + pssh) va muz
add(0.05, np.concatenate([thud(1800, 0.03, 0.004) * 0.6, hp(noise(0.7), 3000) * env(int(SR * 0.7), 0.003, 0.25)]), 0.5)
add(0.1, fizz(1.1, 500, 0.25))
# 2-3: ho'plashlar
for t0 in np.arange(T(40), T(104), 0.42): add(t0, gulp(), 0.45)
# 4: qizilo'ngachdan tushish
add(T(87), whoosh(1.3, 500, 0.6), 0.5)
# 6: qandlar tushadi (10 ta)
for i in range(10): add(T(169 + 6 + i * 4.4), plop(rng.uniform(550, 900)), 0.5)
# 7: oshqozon xavfi: puls
for f in range(221, 269, 12): add(T(f), thud(48, 0.5, 0.15), 0.6)
# 8: ko'ngil aynishi: qorin g'uldirashi
gr = lp(noise(2.0), 160, 3) * (0.5 + 0.5 * np.sin(2 * np.pi * 3.0 * t_(2.0))); add(T(275), gr / np.abs(gr).max(), 0.35)
# 9-10: ichimlik ichida pufakchalar, kislota
add(T(319), lp(fizz(T(417) - T(319), 700, 1.0), 4000), 0.35)
add(T(375), riser(1.7, 300, 900), 0.08)
# 13: qon oqimi
fl = lp(noise(T(585) - T(519)), 250, 2); fl *= (0.6 + 0.4 * np.sin(2 * np.pi * 1.6 * t_(len(fl) / SR))); add(T(519), fl / np.abs(fl).max(), 0.25)
# 15: qorachiq kengayadi
add(T(617), riser(0.35, 200, 1600), 0.12); add(T(623), thud(70, 0.5, 0.12), 0.5)
# 16: qon bosimi — kuchli yurak urishi
for f in range(651, 683, 11): add(T(f), heartbeat(), 0.85)
# 17-19: signal (bez vahimasi), insulin otilishi
for f in range(683, 819, 12): add(T(f), beep(880 if (f // 12) % 2 else 660), 0.07)
add(T(781), hp(fizz(1.6, 1400, 1.0), 1500), 0.3)
add(T(781), whoosh(1.0, 2000, 0.3), 0.4)
# 20: insulin to'dasi
fl = lp(noise(T(863) - T(819)), 400, 2); add(T(819), fl / np.abs(fl).max(), 0.25)
add(T(819), riser(1.6, 400, 120), 0.05)
# 21: qand tushib ketadi — "o'chish" tovushi
t = t_(1.4); f = 220 * (0.25 ** (t / 1.4)); add(T(863), np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.9), 0.18)
# 23-24: yangi banka, yakuniy zarba
add(T(1011) - 0.05, whoosh(0.5, 2500, 0.8), 0.6)
add(T(1011), thud(45, 1.5, 0.45), 0.9)
add(T(1011) + 0.15, np.concatenate([thud(1800, 0.03, 0.004) * 0.6, hp(noise(0.5), 3000) * env(int(SR * 0.5), 0.003, 0.2)]), 0.4)
# kesishlarda "vush"
for f in CUTS:
    add(max(0, T(f) - 0.25), whoosh(0.45, rng.uniform(900, 1600)), 0.22)

out = out / max(1e-6, np.abs(out).max()) * 0.9
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", DUR)
