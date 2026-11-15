# "Paxtali cho'p / oltingugurt tiqini" videosi uchun tovush effektlari (sintez) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: python3 -I zack_test/paxta/sfx.py /tmp/claude-0/audio/sfx_paxta.wav
# Yordamchi funksiyalar quloq/sfx.py (aksirish/sfx.py) dan.
import sys, wave
import numpy as np

SR = 48000; DUR = 40.92
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
def scuttle(d, rate=22, f0=4200):                  # hasharot oyoqlari tiqillashi
    x = np.zeros(int(SR * d)); t = 0.0
    while t < d - 0.02:
        c = hp(noise(0.012), 2500) * env(int(SR * 0.012), 0.0005, 0.003)
        i = int(t * SR); x[i:i + len(c)] += c[: len(x) - i] * rng.uniform(0.4, 1.0); t += rng.exponential(1 / rate)
    return x
def drone(d, f=55):
    t = t_(d); return fade(lp(noise(d), 120, 2) * 3 + 0.4 * np.sin(2 * np.pi * f * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * t)), 0.5, 0.8)
def boom(d=2.2):                                    # momaqaldiroq
    t = t_(d); return lp(noise(d), 180, 2) * 6 * env(len(t), 0.01, 0.6) + thud(40, d, 0.5) * 0.8
def rip(d=0.5):
    t = t_(d); return bp(noise(d), 500, 5000) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 37 * t))) * env(len(t), 0.003, 0.15)
def scratch(d):                                     # tayoqcha ishqalanishi
    t = t_(d); return bp(noise(d), 1500, 7000) * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * t)) * 0.6
def F(sec): return sec
SH = [1, 41, 93, 152, 203, 292, 364, 469, 561, 639, 690, 759, 852, 925, 1000, 1068]
for f in SH[1:]: add(T(f) - 0.25, whoosh(0.5, 1800, 0.5), 0.35)
add(0.0, drone(47.4, 50), 0.12)
def beep(f=880, d=0.14):
    t = t_(d); return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * env(len(t), 0.004, d / 2)
def clank(d=0.5):                                    # metall zarbasi (shompol)
    t = t_(d); return (sum(np.sin(2 * np.pi * f * t) * np.exp(-t / dc) for f, dc in ((1870, 0.09), (2930, 0.06), (4410, 0.04), (640, 0.12))) * 0.3
                       + thud(110, d, 0.07))
def shower(d):
    return fade(hp(lp(noise(d), 9000, 1), 1800) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.7 * t_(d))), 0.25, 0.3)
def crackle(d, rate=30):                             # qotish/yorilish
    x = np.zeros(int(SR * d)); t = 0.0
    while t < d - 0.03:
        c = bp(noise(0.02), 900, 6000) * env(int(SR * 0.02), 0.0005, 0.005)
        i = int(t * SR); x[i:i + len(c)] += c[: len(x) - i] * rng.uniform(0.3, 1.0); t += rng.exponential(1 / (rate * (0.3 + t / d)))
    return x

SHOTS = [1, 39, 86, 172, 253, 309, 381, 441, 498, 534, 582, 678, 753, 803, 843, 900]
HITS = [592, 613, 636, 656]; GUN = [548, 564, 575]; CHEWS = [202, 215, 228, 241, 254, 267, 280, 293, 306]
STEPS = [309, 323, 337, 351, 365, 379]; BOUNCES = [762, 771, 780, 789, 798]
for f in SHOTS[1:]: add(T(f) - 0.25, whoosh(0.5, 1800, 0.5), 0.35)
add(0.0, drone(DUR, 50), 0.10)
# 1 ilgak: cho'p quloqqa kiradi
add(0.0, riser(0.9), 0.25); add(T(8), scratch(1.0), 0.35); add(T(24), thud(90, 0.4, 0.08), 0.7)
# 2–3 quti aylanadi, ogohlantirish yonadi
add(T(43), whoosh(0.9, 1200, 0.6), 0.5); add(T(69), thud(140, 0.25, 0.05), 0.4)
for k in (113, 138): add(T(k), beep(880), 0.35); add(T(k) + 0.16, beep(660), 0.35)
# 4–5 rentgen: past shovqin, chaynash
add(T(172), lp(noise(5.6), 300) * 0.5, 0.3)
for c in CHEWS: add(T(c), thud(210, 0.14, 0.03), 0.35); add(T(c + 5), squelch(0.12, 700), 0.18)
# 6 konveyer: oltingugurt siljiydi
for s_ in STEPS: add(T(s_), squelch(0.3, 380), 0.35)
# 7 tiqish
add(T(385), scratch(2.0), 0.3)
# 8 ozgina oladi
add(T(441), whoosh(0.6, 900, 0.7), 0.3); add(T(456), squelch(0.3, 500), 0.5); add(T(461), scratch(0.5), 0.3); add(T(476), squelch(0.2, 800), 0.3)
# 9 itaradi (80%)
add(T(505), squelch(0.65, 260), 0.7); add(T(505), lp(noise(0.7), 500) * 0.5, 0.4); add(T(512), thud(150, 0.3, 0.06), 0.5)
# 10 to'pponcha shompoli
for i, g in enumerate(GUN): add(T(g), clank(0.5), 0.6 + 0.15 * i)
# 11 zichlash: 4 zarba, oxirida quloq shang'illashi
for i, h in enumerate(HITS):
    add(T(h) - 0.3, whoosh(0.35, 1500, 0.8), 0.3); add(T(h), thud(70 - 5 * i, 0.6, 0.14), 0.75 + 0.1 * i); add(T(h), squelch(0.25, 300), 0.4)
add(T(HITS[-1]), np.sin(2 * np.pi * 3200 * t_(1.6)) * env(int(SR * 1.6), 0.01, 0.6), 0.06)
# 12 qotish
add(T(678), crackle(3.0), 0.45); add(T(678), riser(3.0), 0.12); add(T(745), thud(60, 0.5, 0.1), 0.5)
# 13 tovush halqalari tiqinga uriladi
for b in BOUNCES:
    t = t_(0.5); add(T(b) - 0.5, np.sin(2 * np.pi * np.cumsum(900 - 500 * t / 0.5) / SR) * (t / 0.5) ** 2, 0.14)
    add(T(b), thud(190, 0.2, 0.04), 0.5)
# 14–16 dush: suv shovqini; kesimda bo'g'iq + pufakchalar; shishish; oxirida quloq bitadi (bo'g'iq) + shang'illash
t_sw, t_df, t_blk = T(843), T(900), T(916)
add(T(803), shower(t_sw - T(803) + 0.1), 0.3)
add(t_sw, lp(shower(t_df - t_sw + 0.1), 900, 2), 0.5); add(T(851), bubbles(1.9), 0.45); add(T(851), splash(0.6), 0.35)
add(T(879) - 0.4, riser(0.5), 0.2); add(T(879), squelch(0.5, 220), 0.7); add(T(879) + 0.2, thud(55, 0.7, 0.15), 0.8)
add(t_df, shower(t_blk - t_df + 0.15), 0.3)
add(t_blk, thud(50, 0.8, 0.2), 0.9); add(t_blk, lp(shower(DUR - t_blk), 350, 2), 0.9)
add(t_blk, np.sin(2 * np.pi * 3400 * t_(DUR - t_blk - 0.05)) * fade(np.ones(int(SR * (DUR - t_blk - 0.05))), 0.05, 1.0), 0.05)
for k in range(3): add(t_blk + 0.5 + k * 0.85, heartbeat(), 0.45)
out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
