# "Hojatxonada telefon — gemorroy" videosi uchun tovush effektlari (sintez) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: python3 -I zack_test/gemorroy/sfx.py /tmp/claude-0/audio/sfx_gemorroy.wav
# Yordamchi funksiyalar quloq/sfx.py (aksirish/sfx.py) dan.
import sys, wave
import numpy as np

SR = 48000; DUR = 42.64
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

# voqea kadrlari: EVENTS=... python3 -I gemorroy.py (pastdagi qiymatlar o'sha json'dan)
SHOTS = [1, 39, 86, 174, 236, 315, 427, 474, 519, 589, 618, 637, 704, 746, 795, 824, 897, 971]
SAG, POP, BURST, BAL, PUFFS = 408, 726, 788, 631, [591, 600, 609]
DROPS = [800, 802, 805, 808, 812, 814, 817, 821, 824, 826, 829, 832, 836, 839, 842, 844]
GAUGE, GAUGE_MAX, LAMP, TIMER_END, SEAT_ARROW, INFECT = 128, 162, 987, 77, 214, 937
def tick(d=0.03):
    t = t_(d); return np.sin(2 * np.pi * 2600 * t) * env(len(t), 0.0005, 0.006)
def creak(d=0.6):                                    # rezina/shar cho'zilishi
    t = t_(d); f = 160 + 90 * np.sin(2 * np.pi * 2.5 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return bp(sum(np.sin(k * ph) / k for k in range(1, 12)), 200, 2500) * fade(np.ones(len(t)), 0.05, 0.15)
def pop_(d=0.4):
    return bp(noise(d), 600, 8000) * env(int(SR * d), 0.0005, 0.03) + 0.6 * thud(90, d, 0.06)
def steps(d, per=0.5):                               # ko'chada qadamlar
    x = np.zeros(int(SR * d)); t = 0.1
    while t < d - 0.2:
        s_ = lp(noise(0.12), 1500) * env(int(SR * 0.12), 0.002, 0.03) + 0.4 * thud(80, 0.12, 0.03)
        i = int(t * SR); x[i:i + len(s_)] += s_[: len(x) - i]; t += per
    return x
def beep(f=880, d=0.14):
    t = t_(d); return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * env(len(t), 0.004, d / 2)

for f in SHOTS[1:]: add(T(f) - 0.25, whoosh(0.5, 1800, 0.5), 0.3)
add(0.0, drone(DUR, 50), 0.10)
# 1 ilgak: crash zoom; telefon "tap"lari
add(0.0, riser(0.85), 0.25); add(T(20), thud(90, 0.4, 0.08), 0.6)
for k in range(5): add(T(6) + k * 0.33, tick(0.02), 0.25)
# 2 taymer: tez soat tiqillashi, oxirida signal
for k in range(int((T(TIMER_END) - T(39)) / 0.07)): add(T(39) + k * 0.07, tick(), 0.18)
add(T(TIMER_END), beep(1200, 0.25), 0.35); add(T(TIMER_END) + 0.3, beep(1200, 0.25), 0.35)
# 3 rentgen: yurak urishi + bosim o'lchagich ko'tariladi
for k in range(4): add(T(86) + 0.2 + k * 0.85, heartbeat(), 0.35)
add(T(GAUGE) - 0.2, riser(T(GAUGE_MAX) - T(GAUGE) + 0.2), 0.25); add(T(GAUGE_MAX), thud(140, 0.3, 0.05), 0.5)
add(T(GAUGE_MAX), beep(500, 0.5), 0.2)
# 4 o'rindiq teshigi: halqa va strelka
add(T(174), whoosh(0.6, 1500, 0.5), 0.3); add(T(SEAT_ARROW), thud(120, 0.3, 0.06), 0.6)
# 5 og'irlik strelkalari
for k in range(4): add(T(236) + 0.15 + k * 0.6, whoosh(0.4, 900, 0.8), 0.25)
# 6 to'qima teshikka osilib tushadi
add(T(315) + 0.3, lp(noise(T(SAG) - T(315)), 250) * np.linspace(0.2, 1, int(SR * (T(SAG) - T(315)))), 0.35)
add(T(SAG) - 0.5, creak(0.6), 0.3); add(T(SAG), thud(55, 0.8, 0.18), 0.9); add(T(SAG), squelch(0.4, 260), 0.5)
# 7–8 oyoq venalari: qon tepaga chiqolmaydi, orqaga qaytadi
add(T(427), riser(1.6), 0.15); add(T(474) + 0.6, whoosh(0.8, 700, 0.4), 0.35); add(T(474) + 1.4, squelch(0.4, 220), 0.45)
# 9 qon tanachalari uyuladi
for k in range(18): add(T(519) + 0.15 + k * 0.15, squelch(0.12, rng.uniform(500, 900)), 0.12)
# 10–11 shar puflanadi, vena shishadi
for p in PUFFS: add(T(p), lp(noise(0.35), 1200) * env(int(SR * 0.35), 0.03, 0.12), 0.45); add(T(p) + 0.1, creak(0.3), 0.15)
add(T(BAL) - 0.3, creak(0.5), 0.3); add(T(BAL), thud(70, 0.6, 0.12), 0.7)
# 12 devor yupqalashadi (timelapse)
add(T(637), crackle(2.7, 25), 0.3); add(T(637), riser(2.7), 0.1)
# 13 tugunlar bo'rtadi
add(T(704) + 0.2, creak(T(POP) - T(704) - 0.2), 0.25); add(T(POP), squelch(0.5, 200), 0.7); add(T(POP), thud(60, 0.6, 0.14), 0.7)
# 14 yorilish
add(T(BURST) - 0.5, riser(0.5), 0.3); add(T(BURST), pop_(0.5), 0.9); add(T(BURST) + 0.05, squelch(0.4, 350), 0.6)
# 15 qon tomchilari suvga
for d_ in DROPS: add(T(d_), drip(rng.uniform(900, 1500)), 0.35)
# 16 ko'cha: qadamlar, shahar shovqini
add(T(824), lp(noise(T(897) - T(824)), 700) * 0.6, 0.25); add(T(824), steps(T(897) - T(824), 0.52), 0.45)
# 17 infeksiya: bakteriyalar yopiriladi
add(T(897), scuttle(T(971) - T(897), 28, 3600), 0.25); add(T(INFECT), squelch(0.5, 300), 0.4); add(T(897), riser(T(971) - T(897)), 0.15)
# 18 operatsiya: chiroq yonadi, monitor
add(T(LAMP), thud(150, 0.4, 0.05), 0.6); add(T(LAMP) + 0.25, thud(150, 0.4, 0.05), 0.7)
for k in range(int((DUR - T(971)) / 0.8) + 1): add(T(971) + 0.1 + k * 0.8, beep(1000, 0.12), 0.28)
out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
