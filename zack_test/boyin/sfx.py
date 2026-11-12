# "Bo'yinni qirsillatish" videosi uchun tovush effektlari (sintez) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/boyin/sfx.py /tmp/claude-0/audio/sfx_boyin.wav
# Yordamchi funksiyalar trampolin/sfx.py dan. Vaqtlar boyin.py dagi kadrlarga bog'langan (24 fps).
import sys, wave
import numpy as np

SR = 48000; DUR = 41.36
rng = np.random.default_rng(5)
out = np.zeros(int(SR * DUR))
def T(frame): return (frame - 1) / 24.0

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
def crack(n=5, spread=0.05):
    """suyak "qirs": bir nechta o'tkir chertish + past zarba"""
    d = spread + 0.08; x = np.zeros(int(SR * d))
    for k in range(n):
        i = int(rng.uniform(0, spread) * SR); m = int(0.006 * SR)
        c = bp(noise(0.006), 1500, 9000) * env(m, 0.0002, 0.0015) * rng.uniform(0.5, 1.0)
        x[i:i + m] += c
    return x * 2.5 + 0.5 * thud(140, d, 0.03)[: len(x)]
def click(gain=1.0, f=3000):
    d = 0.03; t = t_(d)
    return gain * (bp(noise(d), f * 0.5, f * 2) * env(len(t), 0.0003, 0.004) + 0.4 * np.sin(2 * np.pi * f * 0.6 * t) * env(len(t), 0.0003, 0.006))
def squelch(d=0.35, f0=380):
    t = t_(d); f = f0 * (1 + 0.8 * np.sin(2 * np.pi * 9 * t)) * np.exp(-t / 0.2)
    return (bp(noise(d), 200, 2200) * 0.7 + 0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * env(len(t), 0.004, d / 3)
def rip(d=0.5):
    """to'qima yirtilishi: donador shitirlash"""
    t = t_(d); x = bp(noise(d), 600, 7000)
    gr = (rng.random(len(t)) < 0.004).astype(float); gr = lp(gr, 3000) * 30
    return (x * 0.4 + gr) * np.minimum(1, t / 0.01) * np.exp(-t / (d * 0.5))
def drone(d, f0=46):
    t = t_(d)
    return fade((np.sin(2 * np.pi * f0 * t) + 0.5 * np.sin(2 * np.pi * f0 * 1.5 * t) + 0.3 * lp(noise(d), 200)) * 0.35, 0.4, 0.8)
def ambience(d):
    return fade(lp(noise(d), 900) * 0.12 + bp(noise(d), 2000, 5000) * 0.015, 0.1, 0.1)
def bird(d=0.35):
    t = t_(d); f = 3200 + 900 * np.sin(2 * np.pi * 7 * t)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.02, d / 3) * 0.12

# --- kesishlarda whoosh ---
for fr in (46, 99, 152, 242, 319, 398, 450, 519, 584, 610, 696, 750, 829, 880, 919):
    add(T(fr) - 0.35, whoosh(0.5, 1800, 0.7), 0.35)
# --- xona: past fon ---
add(0.0, ambience(6.3) * 0.6, 1.0)
for k in range(10): add(0.1 + k * 0.17 + rng.uniform(0, 0.05), click(0.18, 2500))      # klaviatura
for k in range(6): add(24.4 + k * 0.16, click(0.18, 2500))
# --- "qirs" ---
add(T(66), crack(4, 0.04), 0.9)
add(T(85), crack(7, 0.07), 1.3); add(T(85), thud(70, 0.6, 0.15), 0.6)
add(T(99), fade(lp(noise(1.2), 500) * 0.25, 0.2, 0.6), 0.6)                             # yengillik (nafas)
# --- revolver: aylanish shiqirlashi sekinlashadi, oxirida "chiq" ---
CL = T(217); t0 = T(152); TOT = 17.0
ang_prev = 0.0
for fr in np.arange(152, 217, 0.05):
    u = (fr - 152) / (217 - 152); ang = TOT * (1 - (1 - u) ** 3)
    if int(ang / (np.pi / 3)) != int(ang_prev / (np.pi / 3)):
        add(T(fr), click(0.35, 2200))
    ang_prev = ang
add(CL, click(1.6, 1600)); add(CL, thud(55, 1.2, 0.35), 0.9); add(CL - 1.8, riser(1.8), 0.35)
# --- rentgen: yurak urishi ---
for k in range(13): add(T(242) + k * 0.75, heartbeat(), 0.5)
add(T(242), drone(8.5, 42), 0.6)
add(T(424), crack(8, 0.1), 1.2); add(T(424), thud(60, 0.8, 0.2), 0.7)
# --- tomir studiyasi ---
add(T(450), drone(5.8, 38), 0.7)
add(T(481), squelch(0.5, 300), 1.0); add(T(481), thud(48, 0.9, 0.25), 0.9)
add(T(550) - 0.05, rip(0.6), 1.3); add(T(550), thud(70, 0.6, 0.15), 0.6)
add(T(610), drone(3.6, 36), 0.7)
for k in range(5): add(T(610) + 0.4 + k * 0.6, squelch(0.25, 500), 0.25)
# --- ko'cha ---
add(T(696), ambience(2.3), 1.2)
for k in range(3): add(T(696) + 0.3 + k * 0.6, bird(), 1.0)
add(T(758), squelch(0.3, 700), 0.9); add(T(758), click(0.8, 1200))
add(T(758), riser(3.0), 0.5); add(T(762), whoosh(1.2, 2500, 0.5), 0.6)
add(T(852), thud(40, 1.6, 0.5), 1.4); add(T(852), crack(3, 0.03), 0.5)
add(T(852), drone(2.1, 33), 0.8)
add(T(880), ambience(5.5) * 0.7, 1.0)
add(T(880), fade(np.sin(2 * np.pi * 3800 * t_(5.0)) * 0.03, 0.8, 1.5), 1.0)           # quloqdagi shang'illash
add(T(962), thud(70, 0.7, 0.18), 1.1); add(T(964), thud(90, 0.4, 0.08), 0.5)
add(T(930), drone(3.0, 30), 0.6)

out = np.tanh(out * 0.9) * 0.8
w = wave.open(sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/audio/sfx_boyin.wav", "wb")
w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
