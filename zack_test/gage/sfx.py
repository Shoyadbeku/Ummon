# Phineas Gage videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/gage/sfx.py /tmp/claude-0/audio/sfx.wav
import sys, wave
import numpy as np

SR = 48000; DUR = 55.2
rng = np.random.default_rng(5)
out = np.zeros(int(SR * DUR))

def t_(d): return np.arange(int(SR * d)) / SR
def env(n, a=0.005, decay=0.3):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / decay)
def lp(x, fc, n=2):                      # FFT past o'tkazuvchi filtr (n = keskinlik darajasi)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / fc) ** 2) ** (n / 2), len(x))
def hp(x, fc): return x - lp(x, fc, 1)
def add(at, x, gain=1.0):
    i = int(at * SR); j = min(len(out), i + len(x)); out[i:j] += gain * x[: j - i]
def noise(d): return rng.standard_normal(int(SR * d))

def clink(f=2600):                       # temir tayoq toshga urilishi
    t = t_(0.35); x = sum(np.sin(2 * np.pi * f * k * t) / k for k in (1, 1.47, 2.09))
    return x * env(len(t), 0.001, 0.07) + 0.4 * hp(noise(0.35), 3000) * env(len(t), 0.001, 0.02)
def thud(f=70, d=0.6, decay=0.15):       # past zarba
    t = t_(d); sweep = f * (1 + 1.5 * np.exp(-t / 0.03))
    return np.sin(2 * np.pi * np.cumsum(sweep) / SR) * env(len(t), 0.002, decay) + 0.3 * lp(noise(d), 400) * env(len(t), 0.002, 0.05)
def whoosh(d=1.2, fc=900, peak=0.6):     # havo kesilishi
    n = noise(d); t = t_(d); shape = np.exp(-((t / d - peak) ** 2) / 0.04)
    return hp(lp(n, fc, 2), fc * 0.25) * shape
def boom(d=3.0):                         # portlash
    t = t_(d)
    return (1.2 * np.sin(2 * np.pi * np.cumsum(45 * (1 + 2 * np.exp(-t / 0.08))) / SR) * env(len(t), 0.003, 0.6)
            + 2.0 * lp(noise(d), 300, 3) * env(len(t), 0.002, 0.8) + 0.5 * hp(noise(d), 2000) * env(len(t), 0.001, 0.08))
def crackle(d=0.5):                      # uchqun chirsillashi
    x = np.zeros(int(SR * d))
    for _ in range(40):
        i = rng.integers(0, len(x) - 400); x[i:i + 300] += hp(noise(300 / SR), 4000) * env(300, 0.0005, 0.002) * rng.uniform(.3, 1)
    return x * np.linspace(1, 0.2, len(x))
def heartbeat():                         # yurak urishi (lub-dub)
    return np.concatenate([thud(52, 0.25, 0.06), np.zeros(int(SR * 0.12)), 0.7 * thud(48, 0.4, 0.07)])

# fon: shamol va past tovush (keskinlik)
amb = lp(noise(DUR), 350, 3); amb /= np.abs(amb).max()
tt = np.arange(len(out)) / SR
gain = np.where((tt > 24.1) & (tt < 35.2), 0.25, 1.0) * 0.05      # rentgenda shamol pasayadi
drone = sum(np.sin(2 * np.pi * f * tt) for f in (55, 82.41, 110.0)) / 3 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.15 * tt))
dgain = 0.025 + 0.04 * np.clip((tt - 43.6) / 8, 0, 1)                # oxirida kuchayadi
out += amb * gain + drone * dgain

for at in (2.5, 4.4, 7.0): add(at, clink(2400), 0.25)              # S1: zichlash zarblari
add(12.97, clink(2700), 0.5); add(13.0, crackle(), 0.6)              # uchqun
add(14.3, boom(), 0.9)                                               # portlash
add(15.2, whoosh(1.0, 1200, 0.3), 0.5)                               # sekinlashgan kadrga o'tish
add(16.5, lp(noise(3.5), 120, 3) * np.hanning(int(SR * 3.5)) * 3, 0.4)   # tayoq ko'tarilayotgandagi past g'uvillash
add(19.8, thud(60, 1.0, 0.3), 0.8)                                   # yonoqdan kiradi
add(23.2, thud(80, 0.8, 0.2), 0.6); add(23.2, whoosh(0.8, 2000, 0.2), 0.4)   # tepadan chiqadi
add(23.9, whoosh(0.6, 1500, 0.6), 0.4)                               # rentgenga o'tish
for k in range(6): add(30.6 + k * 0.85, heartbeat(), 0.7)            # miya ustuni: nafas va yurak
for at in (35.1, 43.5, 49.0): add(at, whoosh(0.5, 1800, 0.7), 0.3)   # kesishlar
add(46.4, thud(55, 1.2, 0.4), 0.5)                                   # "xarakteri o'zgarib ketdi"
add(51.6, boom(2.5), 0.45); add(51.6, thud(42, 2.0, 0.6), 0.5)                 # "jahldor" — keskin zarba

out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
