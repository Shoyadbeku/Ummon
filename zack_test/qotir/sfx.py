# "Qo'tir nega qichishadi" videosi uchun tovush effektlari (sintez) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: python3 -I zack_test/qotir/sfx.py /tmp/claude-0/audio/sfx_qotir.wav
# Yordamchi funksiyalar tirnoq_osishi/sfx.py dan; voqealar kadrlari qotir.py bilan bir xil.
import sys, wave
import numpy as np

SR = 48000; DUR = 39.8
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
    return x / (np.abs(x).max() + 1e-9) * np.minimum(1, t / 0.05) * (0.55 + 0.45 * np.exp(-t / 1.5))
def alarm(d, f0=880):                                # "ding-dong" ogohlantirish
    t = t_(d); x = np.zeros(len(t))
    for k, f in enumerate((f0, f0 * 0.75)):
        tt_ = t_(0.6); s = (np.sin(2 * np.pi * f * tt_) + 0.3 * np.sin(4 * np.pi * f * tt_)) * env(len(tt_), 0.005, 0.25)
        i = int(k * 0.45 * SR); x[i:i + len(s)] += s[: len(x) - i]
    return x
def heartbeat_slow(d, bpm=55):
    x = np.zeros(int(SR * d)); hb = heartbeat()
    for k in range(int(d * bpm / 60)):
        i = int(k * 60 / bpm * SR); x[i:i + len(hb)] += hb[: len(x) - i]
    return x

def click(f0=3500):                                   # magnitlar "chiq" etib yopishadi
    t = t_(0.08); return (np.sin(2 * np.pi * f0 * t) + 0.5 * np.sin(2 * np.pi * f0 * 1.7 * t)) * env(len(t), 0.0005, 0.012) + hp(noise(0.08), 3000) * env(len(t), 0.0005, 0.004)
def gulp():
    t = t_(0.35); f = 260 - 140 * t / 0.35
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.02, 0.12) + 0.4 * squelch(0.35, 300)
def rumble(d):
    t = t_(d); x = lp(noise(d), 90, 2); return x / (np.abs(x).max() + 1e-9) * np.minimum(1, t / 0.4)
def pad(d, freqs=(220, 277, 330, 415), trem=0.3):     # tush: yumshoq akkord
    t = t_(d); x = sum(np.sin(2 * np.pi * f * t + k) for k, f in enumerate(freqs)) / len(freqs)
    return fade(x * (1 - trem + trem * np.sin(2 * np.pi * 0.7 * t)), 0.4, 0.6)
def glitch_snd(d=1.0):
    x = np.zeros(int(SR * d)); n = int(SR * 0.03)
    for k in range(int(d / 0.03)):
        if rng.random() < 0.55: x[k * n:(k + 1) * n] = np.sign(np.sin(2 * np.pi * rng.uniform(200, 3000) * t_(0.03))) * rng.uniform(0.2, 0.8)
    return bp(x, 300, 8000)

def power_down(d=2.6):
    t = t_(d); f = 520 * np.exp(-t / (d / 2.5)) + 40
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * fade(np.ones(len(t)), 0.02, 0.4) * 0.6
def twitch_snd():                                    # qovoq "tit" etib uchishi
    return mixs(click(rng.uniform(2200, 3200)) * 0.6, squelch(0.08, 900) * 0.5)

def scrape(d=1.2):                                   # skalpel "shirr"
    t = t_(d); return bp(noise(d), 2500, 9000) * (0.6 + 0.4 * np.sin(2 * np.pi * 11 * t)) * fade(np.ones(len(t)), 0.05, 0.2)
def shing(d=1.0):                                    # pichoq tig'i yaltirashi
    t = t_(d); x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t / (d / k)) for k, f in ((2, 3100), (3, 4650), (4, 6200)))
    return mixs(x * env(len(t), 0.003, d) * 0.4, whoosh(0.4, 5000, 0.2) * 0.3)
def step(f0=70):
    return mixs(thud(f0, 0.25, 0.05) * 0.7, bp(noise(0.12), 600, 4000) * env(int(SR * 0.12), 0.002, 0.03) * 0.5)

def scratch_snd(d=0.14):                             # tirnoq "shirq"
    t = t_(d); return bp(noise(d), 1800, 7000) * env(len(t), 0.01, d / 2.5)

# ---------------- voqealar (kadrlar) ----------------
SHOTS = [1, 37, 63, 116, 176, 230, 287, 345, 404, 457, 512, 559, 627, 675, 744, 784, 862, 916]
F_IMPACT, F_ITCH, F_TOUCH, F_NO, F_LINK, F_ARRIVE = 24, 147, 204, 262, 549, 896
for f in SHOTS[1:]: add(T(f) - 0.25, whoosh(0.45, 1800, 0.6), 0.35)
# 1) ko'cha: yugurish, yiqilish
add(0.0, wind(1.5, 700) * 0.08)
for k in range(4): add(0.05 + k * 0.22, step(70 + 6 * (k % 2)), 0.6)
add(T(F_IMPACT) - 0.35, whoosh(0.4, 2500, 0.8), 0.5)
add(T(F_IMPACT), mixs(thud(60, 0.9, 0.25), bp(noise(0.5), 500, 5000) * env(int(SR * 0.5), 0.003, 0.12) * 0.9), 1.0)
add(T(F_IMPACT) + 0.08, scrape(0.5), 0.5)
# 2) shilinish, qon
add(T(37), scrape(0.45), 0.6); add(T(44), squelch(0.5, 400), 0.5)
for k in range(5): add(T(45) + k * 0.13, drip(900 + 150 * k), 0.3)
# 3) qo'tir qotishi
add(T(63), riser(1.6), 0.18); add(T(70), crackle(1.6) * 0.5, 0.6); add(T(100), mixs(click(1800), crackle(0.2)), 0.5)
# 4) xona, qichish
add(T(116), lp(noise(2.4), 500) * 0.05)
add(T(F_ITCH) - 0.3, riser(0.35), 0.35); add(T(F_ITCH), mixs(thud(70, 0.6, 0.15), ring(1.1, 2600)), 0.8)
for f in range(F_ITCH, 176, 8): add(T(f), tick(900), 0.25)
# 5) qashish
for f in range(180, F_TOUCH - 4, 3): add(T(f), tick(2200), 0.08)
add(T(F_TOUCH), thud(90, 0.3, 0.06), 0.5)
for f in range(F_TOUCH, 228, 4): add(T(f), scratch_snd(0.15), 0.55)
# 6) infeksiya emas
add(T(230), bubbles(1.3), 0.3)
add(T(F_NO), mixs(thud(55, 0.8, 0.25), click(1500) * 0.8, alarm(0.5, 330) * 0.35), 0.95)
add(T(F_NO) + 0.5, whoosh(0.6, 3000, 0.3), 0.3)
# 7) tiklanish -> kesimga sho'ng'ish
add(T(287), pad(2.3, (262, 330, 392, 523), 0.2), 0.22); add(T(330), riser(0.6), 0.4)
add(T(345), thud(50, 1.0, 0.35), 0.8)
add(T(345), rumble(T(627) - T(345)) * 0.22)
# 9-11) hujayralar
add(T(404), squelch(1.6, 180), 0.3)
for f in range(457, F_LINK, 5): add(T(f), squelch(0.12, rng.uniform(500, 900)), 0.22)
add(T(F_LINK) - 0.3, riser(0.3), 0.3); add(T(F_LINK), mixs(click(3000), thud(80, 0.5, 0.12), tinkle(0.5, 10) * 0.5), 0.9)
# 12-13) tortilish
add(T(563), creak(2.4, 80), 0.45); add(T(563), squelch(2.0, 150), 0.3)
add(T(627), rumble(T(744) - T(627)) * 0.25)
for f in range(629, 672, 5): add(T(f), creak(0.25, 180 + (f % 3) * 30), 0.4)
add(T(637), ring(1.4, 1900), 0.4)
# 14) gistamin
add(T(675), bubbles(2.8), 0.4); add(T(678), tinkle(2.6, 30), 0.25)
# 15-16) asab
add(T(744), rumble(T(862) - T(744)) * 0.2)
for i in range(3):
    f = 744 + 4 + i * 5
    while f < 857:
        big = f >= 784
        add(T(f), zap(0.4 if big else 0.15), 0.4 if big else 0.2)
        f += (17 if big else 11) + (i * 3) % 5
# 17) miya
add(T(862), zap(1.3), 0.5); add(T(866), riser(1.2), 0.3)
add(T(F_ARRIVE), mixs(thud(50, 1.0, 0.3), zap(0.5), ring(1.2, 3000)), 0.95)
# 18) oxiri
for f in range(916, 950, 4): add(T(f), scratch_snd(0.14), 0.5)
add(T(940), thud(48, 1.2, 0.4), 0.6)
x = out / (np.abs(out).max() + 1e-9) * 0.9
x[-int(SR * 0.3):] *= np.linspace(1, 0, int(SR * 0.3))
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())
print("ok", len(x) / SR)
