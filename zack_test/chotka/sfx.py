# "Unitaz aerozoli va tish cho'tkasi" videosi uchun tovush effektlari (sintez) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: python3 -I zack_test/chotka/sfx.py /tmp/claude-0/audio/sfx_chotka.wav
# Yordamchilar yostiq/sfx.py dan.
# Yordamchi funksiyalar quloq/sfx.py (aksirish/sfx.py) dan.
import sys, wave
import numpy as np

SR = 48000; DUR = 40.08
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



SH = [1, 28, 62, 122, 152, 175, 237, 285, 326, 371, 450, 509, 566, 627, 683, 739, 817, 851, 911]
N_ = ["hook", "room", "cup", "morning", "face", "reveal", "lid", "vortex", "burst", "drops", "height", "spread", "hours",
      "drift", "land", "micro", "breed", "cap", "trap"]
S = dict(zip(N_, SH)); NXT = dict(zip(N_, SH[1:] + [963]))
def dur(n): return T(NXT[n]) - T(S[n])
def squish(d=0.5):
    x = np.zeros(int(SR * d)); t = 0.0
    while t < d - 0.12:
        s_ = squelch(0.12, rng.uniform(250, 700)); i = int(t * SR); x[i:i + len(s_)] += s_[: len(x) - i] * rng.uniform(0.4, 1.0); t += rng.uniform(0.05, 0.12)
    return x
def brushing(d, rate=5.0):                           # tish yuvish "shirq-shirq"
    t = t_(d); return bp(noise(d), 1200, 8000) * (0.25 + 0.75 * np.abs(np.sin(np.pi * rate * t)) ** 2)
def flush(d=3.2):                                    # unitaz suvi: shovqin + girdob gurillashi
    t = t_(d); e = np.minimum(1, t / 0.15) * np.exp(-np.maximum(0, t - 1.6) / 0.9)
    gurgle = sum(np.sin(2 * np.pi * (f0 + 40 * np.sin(2 * np.pi * r * t)) * t) for f0, r in ((140, 3.1), (220, 4.7), (95, 2.3))) * 0.15
    return (lp(noise(d), 2500, 2) * 1.6 + bp(noise(d), 300, 1200) * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * t)) + gurgle) * e
def hiss(d):                                         # aerozol pufaklari "pssh"
    t = t_(d); return hp(lp(noise(d), 9000, 1), 2500) * np.minimum(1, t / 0.02) * np.exp(-t / (d / 2.5))
def airy(d):                                         # havoda suzish: past shamol
    return fade(bp(noise(d), 150, 900) * 0.8 + 0.2 * hp(lp(noise(d), 5000), 2000), 0.3, 0.4)

for f in SH[1:]: add(T(f) - 0.2, whoosh(0.42, 1800, 0.5), 0.2)
add(0.0, drone(DUR, 48), 0.07)
# 1 ilgak: tomchi + zarba
add(0.05, drip(1100), 0.35); add(T(20) - 0.4, riser(0.4), 0.2); add(T(24), thud(70, 0.6, 0.14), 0.7)
# 2 masofa chizig'i: "tik-tik" + ding
for k in range(8): add(T(S["room"]) + 0.12 + k * 0.05, click(0.04), 0.12)
add(T(S["room"]) + 0.6, ding(1760, 0.8), 0.22)
# 3 stakan: shisha "dzing"
add(T(S["cup"]) + 0.2, ding(2900, 1.0), 0.12)
# 4-5 tish yuvish
add(T(S["morning"]), brushing(dur("morning") + dur("face") + 0.4), 0.3)
add(T(S["morning"]) + 0.1, drip(900), 0.2)
# 6 reveal: crash zoom zarbasi + "UV" g'uvillash
add(T(176) - 0.35, riser(0.35), 0.3); add(T(176), thud(55, 1.0, 0.22), 1.0); add(T(176) + 0.05, zap(0.6), 0.25)
add(T(S["reveal"]), brushing(dur("reveal"), 4.0) * 0.5, 0.2)
# 7 tugma bosish
add(T(258), click(), 0.6); add(T(258) + 0.02, clank(0.3), 0.15)
# 8 girdob
add(T(280), flush(4.0), 0.55)
# 9 portlash: pssh + zarba
add(T(338) - 0.3, riser(0.3), 0.25); add(T(338), thud(48, 1.2, 0.25), 1.0); add(T(338), hiss(1.4), 0.5); add(T(338) + 0.1, bubbles(1.2), 0.25)
# 10 mikro tomchilar: pufakchalar
add(T(S["drops"]), bubbles(dur("drops")), 0.22); add(T(S["drops"]), airy(dur("drops")), 0.25)
# 11 balandlik: chizg'ich o'sadi, "2 M" da zarba
add(T(S["height"]) + 0.2, riser(T(492) - T(S["height"]) - 0.2), 0.25); add(T(492), thud(60, 0.9, 0.18), 0.85); add(T(492) + 0.05, ding(1320, 0.9), 0.25)
# 12-14 suzish
add(T(S["spread"]), airy(dur("spread") + dur("hours") + dur("drift")), 0.35)
for k in range(int(dur("hours") / 0.06)): add(T(S["hours"]) + k * 0.06, tick(0.025, 2800 if k % 2 else 2200), 0.16)
# 15 qo'nish: mayda tomchilar
for k in range(10): add(T(S["land"]) + 0.15 + k * 0.2, drip(rng.uniform(2000, 3200)), 0.12)
# 16 mikro tuklar: shilimshiq g'imirlash
add(T(S["micro"]), squish(dur("micro")), 0.16); add(T(S["micro"]), drone(dur("micro"), 70), 0.12)
# 17 ko'payish: crash zoom + tezlashuvchi "pop"lar
add(T(S["breed"]) + 0.15, thud(80, 0.5, 0.1), 0.6)
d = dur("breed"); t = 0.0
while t < d - 0.08:
    add(T(S["breed"]) + t, drip(rng.uniform(500, 900)), 0.12); add(T(S["breed"]) + t, squelch(0.08, 600), 0.08); t += 0.25 * np.exp(-3 * t / d) + 0.02
# 18 qopqoq kiydiriladi: "chiq"
add(T(884) - 0.15, whoosh(0.3, 3000, 0.7), 0.2); add(T(884), snap(0.2), 0.5); add(T(884) + 0.01, click(), 0.4)
# 19 rentgen: yurak urishi + oxirida pastlab ketuvchi "ta-da"
add(T(912), thud(50, 0.9, 0.2), 0.8); add(T(912), zap(0.5), 0.2)
for k in range(2): add(T(S["trap"]) + 0.3 + k * 0.7, heartbeat(), 0.4)
add(T(S["trap"]) + 0.2, squish(dur("trap") - 0.3), 0.15); add(T(938), sting(1.0), 0.45)
out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
