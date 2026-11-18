# "Yostiq jildi va bakteriyalar" videosi uchun tovush effektlari (sintez) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: python3 -I zack_test/yostiq/sfx.py /tmp/claude-0/audio/sfx_yostiq.wav
# Yordamchi funksiyalar quloq/sfx.py (aksirish/sfx.py) dan.
import sys, wave
import numpy as np

SR = 48000; DUR = 42.88
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

def tick(d=0.03, f=2600):
    t = t_(d); return np.sin(2 * np.pi * f * t) * env(len(t), 0.0005, 0.006)
def steps(d, per=0.5, soft=1.0):
    x = np.zeros(int(SR * d)); t = 0.05
    while t < d - 0.15:
        s_ = lp(noise(0.12), 1500 * soft) * env(int(SR * 0.12), 0.002, 0.03) + 0.4 * thud(80, 0.12, 0.03)
        i = int(t * SR); x[i:i + len(s_)] += s_[: len(x) - i]; t += per
    return x
def creak_door(d=0.9):                               # eshik g'ichirlashi
    t = t_(d); f = 380 + 140 * np.sin(2 * np.pi * 1.3 * t) + 60 * np.sin(2 * np.pi * 7 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return bp(sum(np.sin(k * ph) / k for k in range(1, 16)), 300, 4000) * (0.5 + 0.5 * np.sin(2 * np.pi * 23 * t) ** 2) * fade(np.ones(len(t)), 0.08, 0.2)
def ding(f=1320, d=1.2):                             # "fikr" qo'ng'irog'i
    t = t_(d); return sum(np.sin(2 * np.pi * f * k * t) * np.exp(-t / (0.5 / k)) / k for k in (1, 2.76, 5.4)) * 0.5
def screw(d):                                         # otvyortka burash: tez chiqirlash
    x = np.zeros(int(SR * d)); t = 0.0
    while t < d - 0.05:
        c = bp(noise(0.03), 2000, 9000) * env(int(SR * 0.03), 0.001, 0.008)
        i = int(t * SR); x[i:i + len(c)] += c[: len(x) - i] * rng.uniform(0.4, 1.0); t += rng.uniform(0.03, 0.07)
    return x
def snap(d=0.3):                                     # plastmassa sinishi
    return bp(noise(d), 800, 9000) * env(int(SR * d), 0.0005, 0.02) + 0.4 * thud(200, d, 0.03)
def metal(d=0.5):
    return clank(d) * 0.6
def zipper(d=0.8):
    t = t_(d); x = np.zeros(len(t)); k = 0.0
    while k < d - 0.01:
        c = hp(noise(0.006), 3000) * env(int(SR * 0.006), 0.0003, 0.0015); i = int(k * SR); x[i:i + len(c)] += c[: len(x) - i]; k += 0.006
    return x * fade(np.ones(len(t)), 0.05, 0.1)
def click(d=0.08):
    return hp(noise(d), 2000) * env(int(SR * d), 0.0003, 0.004) + 0.5 * thud(400, d, 0.01)
def sting(d=1.4):                                    # hayrat "ta-da" (pastlab ketuvchi trombon kabi)
    t = t_(d); out_ = np.zeros(len(t))
    for i, (f0, a) in enumerate(((392, 0.0), (370, 0.35), (349, 0.7))):
        tt = np.clip(t - a, 0, None); m = (t >= a)
        f = f0 * (1 - 0.06 * (tt / 0.6) * (i == 2))
        ph = 2 * np.pi * np.cumsum(f * m) / SR
        out_ += bp(sum(np.sin(k * ph) / k for k in range(1, 10)), 150, 2500) * m * np.exp(-tt / (0.25 if i < 2 else 0.6)) * np.minimum(1, tt / 0.02)
    return out_ * 0.6


SH = [1, 47, 81, 105, 136, 182, 251, 299, 342, 378, 406, 462, 513, 575, 601, 690, 747, 789, 858, 925, 968]
N_ = ["hook", "tlapse", "face", "toilet", "petri", "press", "night8", "sweat", "flakes", "dust", "saliva", "soak", "thermal", "fungi",
      "breed", "rub", "smear", "pores", "inflame", "cream", "apply"]
S = dict(zip(N_, SH)); NXT = dict(zip(N_, SH[1:] + [1030]))
def dur(n): return T(NXT[n]) - T(S[n])
def squish(d=0.5):                                   # shilimshiq "chav-chuv"
    x = np.zeros(int(SR * d)); t = 0.0
    while t < d - 0.12:
        s_ = squelch(0.12, rng.uniform(250, 700)); i = int(t * SR); x[i:i + len(s_)] += s_[: len(x) - i] * rng.uniform(0.4, 1.0); t += rng.uniform(0.05, 0.12)
    return x
def heat(d):                                         # issiqlik "shovqini"
    t = t_(d); return fade(lp(noise(d), 300, 2) * 2 + 0.25 * np.sin(2 * np.pi * 60 * t) * np.sin(2 * np.pi * 0.7 * t), 0.2, 0.3)
def rub(d, rate=2.5):                                # mato ishqalanishi
    t = t_(d); return bp(noise(d), 300, 3500) * (0.35 + 0.65 * np.abs(np.sin(np.pi * rate * t)))

for f in SH[1:]: add(T(f) - 0.22, whoosh(0.45, 1800, 0.5), 0.22)
add(0.0, drone(DUR, 50), 0.07)
# 1 ilgak: crash zoom zarbasi
add(T(21) - 0.5, riser(0.5), 0.22); add(T(27), thud(70, 0.7, 0.15), 0.9)
# 2 timelapse: soat tiqillashi tezlashadi
for k in range(int(dur("tlapse") / 0.07)): add(T(S["tlapse"]) + k * 0.07, tick(0.03, 2600 if k % 2 else 2100), 0.2)
# 3 yuz: yostiq "shuv"
add(T(S["face"]), rub(0.6, 1.5), 0.3)
# 4 unitaz: sovuq aks-sado, suv tomchisi
add(T(S["toilet"]) + 0.1, drip(1100), 0.4); add(T(S["toilet"]) + 0.5, drip(900), 0.25)
# 5 17 000: zarba + "ding"
add(T(140) - 0.4, riser(0.4), 0.25); add(T(140), thud(55, 1.0, 0.22), 1.0); add(T(140) + 0.05, ding(1760, 1.0), 0.3)
for k in range(14): add(T(S["petri"]) + 0.1 + k * 0.12, drip(rng.uniform(1600, 2600)), 0.08)
# 6 bakteriyalar g'imirlashi, teri bosadi
add(T(S["press"]), squish(dur("press")), 0.22); add(T(222) - 0.6, whoosh(0.7, 500, 0.85), 0.5); add(T(222), thud(45, 1.2, 0.3), 1.0)
# 7 sakkiz soat: tez tiqillash
for k in range(int(dur("night8") / 0.05)): add(T(S["night8"]) + k * 0.05, tick(0.025, 3000 if k % 2 else 2400), 0.18)
# 8 ter: tomchilar
for k in range(6): add(T(S["sweat"]) + 0.15 + k * 0.25, drip(rng.uniform(1300, 2200)), 0.25)
# 9 qipiqlar: shitirlash
add(T(S["flakes"]), crackle(dur("flakes"), 25), 0.18)
# 10 chang
add(T(S["dust"]), scratch(dur("dust")), 0.12)
# 11 so'lak: nafas + mayda tomchilar
add(T(S["saliva"]), bp(noise(dur("saliva")), 200, 2500) * np.abs(np.sin(np.pi * 0.7 * t_(dur("saliva")))), 0.25)
for k in range(8): add(T(S["saliva"]) + 0.2 + k * 0.25, drip(rng.uniform(2200, 3200)), 0.12)
# 12 singish
add(T(S["soak"]) + 0.3, squelch(0.6, 300), 0.4); add(T(S["soak"]) + 0.8, bubbles(1.2), 0.25)
# 13 issiqlik
add(T(S["thermal"]), heat(dur("thermal")), 0.35)
# 14 zamburug': crash zoom
add(T(S["fungi"]) + 0.15, thud(80, 0.5, 0.1), 0.6); add(T(S["fungi"]), crackle(dur("fungi"), 50), 0.2)
# 15 ko'payish: tobora tezlashadigan "pop"lar
d = dur("breed"); t = 0.0
while t < d - 0.1:
    add(T(S["breed"]) + t, drip(rng.uniform(500, 900)), 0.11); add(T(S["breed"]) + t, squelch(0.08, 600), 0.07); t += 0.35 * np.exp(-3 * t / d) + 0.02
add(T(S["breed"]), squish(d), 0.12)
# 16 ishqalash
add(T(S["rub"]), rub(dur("rub"), 2.5), 0.45)
# 17 surtilish: shilimshiq
add(T(S["smear"]), squish(dur("smear")), 0.35); add(T(S["smear"]), rub(dur("smear"), 1.0), 0.25)
# 18 teshikka kirish
add(T(S["pores"]) + 1.0, whoosh(1.0, 700, 0.8), 0.3); add(T(S["pores"]) + 0.5, squish(dur("pores") - 0.5), 0.25)
# 19 yallig'lanish: yurak urishi, "yiringli" da zarba
for k in range(4): add(T(S["inflame"]) + 0.1 + k * 0.7, heartbeat(), 0.45)
add(T(882), thud(50, 1.0, 0.25), 0.9); add(T(882), squelch(0.5, 280), 0.5)
# 20 krem: qopqoq buraladi
add(T(S["cream"]) + 0.1, screw(0.6), 0.25); add(T(S["cream"]) + 0.75, click(), 0.4); add(T(S["cream"]) + 0.3, ding(2640, 0.8), 0.15)
# 21 surtish, oxirida "ta-da" (pastlab)
add(T(S["apply"]), rub(dur("apply"), 3.0) * 0.6, 0.2); add(T(S["apply"]) + 0.6, sting(1.6), 0.5)
out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
