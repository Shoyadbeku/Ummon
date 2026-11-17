# "O'g'ri va televizor" videosi uchun tovush effektlari (sintez) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: python3 -I zack_test/ogri/sfx.py /tmp/claude-0/audio/sfx_ogri.wav
# Yordamchi funksiyalar quloq/sfx.py (aksirish/sfx.py) dan.
import sys, wave
import numpy as np

SR = 48000; DUR = 46.33
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

ev = {"hit1": 234, "hit2": 302, "idea": 355, "light": 715, "drop": 774, "door_open": 704, "clock": [471, 526], "unscrew": [527, 566],
      "pile": [567, 600], "bag": [601, 655], "end": 1112}
SHOTS = [1, 49, 95, 121, 179, 231, 260, 299, 327, 399, 438, 471, 527, 567, 601, 656, 702, 750, 781, 812, 858, 908, 954, 1007, 1067]
if len(sys.argv) > 2:
    import json; j = json.load(open(sys.argv[2])); ev.update(j); SHOTS = [s[0] for s in j["shots"]]
S = {n: SHOTS[i] for i, n in enumerate(["hook", "tv", "greed", "big", "window", "nofit1", "door", "nofit2", "idea", "tool", "dark", "clock",
                                       "unscrew", "pile", "bag", "exit", "owner", "drop", "flee", "open", "nottv", "parts", "empty", "flashback", "street"])}

for f in SHOTS[1:]: add(T(f) - 0.25, whoosh(0.5, 1800, 0.5), 0.25)
# tungi fon: past g'uvullash (uy egasi chiroqni yoqguncha), ko'chada shamol
add(0.0, drone(T(ev["light"]), 45), 0.08)
# 1 ilgak: eshik g'ichirlab ochiladi, crash zoom zarbasi, sekin qadamlar
add(0.05, creak_door(0.9), 0.35); add(T(19), thud(90, 0.4, 0.08), 0.55); add(T(19) - 0.6, riser(0.6), 0.2)
add(0.3, steps(T(48) - 0.3, 0.42, 0.6), 0.25); add(T(19), click(), 0.4)          # peshona chirog'i yoqiladi
# 2 TV: nur sirpanadi, yaltiroq
add(T(S["tv"]) + 0.2, whoosh(1.0, 900, 0.6), 0.25); add(T(S["tv"] + 26), ding(2640, 0.6), 0.18)
# 4 juda katta: zo'riqish (past g'uvillash), ko'tarish
add(T(S["big"]), lp(noise(T(S["window"]) - T(S["big"])), 300) * np.linspace(0.3, 1, int(SR * (T(S["window"]) - T(S["big"])))), 0.35)
add(T(S["big"]) + 0.3, thud(70, 0.5, 0.1), 0.4)
# 5-6 deraza: surilish, zarb + oyna titrashi
add(T(S["window"]), lp(noise(T(ev["hit1"]) - T(S["window"])), 900) * 0.6, 0.25)
add(T(ev["hit1"]), thud(55, 0.9, 0.2), 1.0); add(T(ev["hit1"]), clank(0.6), 0.35); add(T(ev["hit1"]) + 0.02, crackle(0.5, 40), 0.25)
# 7-8 eshik: shoshilib qadamlar, zarb
add(T(S["door"]), steps(T(ev["hit2"]) - T(S["door"]), 0.32), 0.4)
add(T(ev["hit2"]), thud(50, 1.0, 0.22), 1.0); add(T(ev["hit2"]), snap(0.3), 0.35); add(T(ev["hit2"]) + 0.03, thud(120, 0.3, 0.05), 0.4)
# 9 g'oya: "ding"
add(T(ev["idea"]) - 0.4, riser(0.4), 0.2); add(T(ev["idea"]), ding(1320, 1.4), 0.55)
# 10 otvyortka: metall "shing"
add(T(S["tool"]) + 0.6, ding(3960, 0.5), 0.2); add(T(S["tool"]) + 0.5, whoosh(0.4, 3000, 0.6), 0.2)
# 11 qorong'i: sekin qadamlar
add(T(S["dark"]), steps(T(S["clock"]) - T(S["dark"]), 0.45, 0.6), 0.25)
# 12 soat: timelapse — tez tiqillash
c0, c1 = ev["clock"]
for k in range(int((T(c1) - T(c0)) / 0.06)): add(T(c0) + k * 0.06, tick(0.03, 2600 if k % 2 else 2100), 0.22)
add(T(c0), screw(T(c1) - T(c0)), 0.15)
# 13 burab, sindirib
u0, u1 = ev["unscrew"]; add(T(u0), screw(T(u1) - T(u0)), 0.45)
for k in range(5): add(T(u0) + 0.2 + k * 0.32, snap(0.25) if k % 2 else metal(0.4), 0.35)
# 14 uyum: qismlar taraqlab tushadi
p0, p1 = ev["pile"]
for k in range(12): add(T(p0) + k * (T(p1) - T(p0)) / 12, metal(0.35) if k % 3 else snap(0.25), 0.3)
# 15 sumka: qismlar tushadi, zamok
b0, b1 = ev["bag"]
for k in range(10): add(T(b0) + 0.1 + k * (T(b1) - T(b0) - 0.6) / 10, clank(0.35) if k % 2 else thud(140, 0.3, 0.05), 0.3)
add(T(b1) - 0.8, zipper(0.75), 0.45)
# 16 chiqish: qadamlar, sumka shitirlashi
add(T(S["exit"]), steps(T(S["owner"]) - T(S["exit"]), 0.5), 0.35)
# 17 eshik ochiladi, chiroq yoqiladi (click + elektr g'uvullashi), zarb
add(T(ev["door_open"]), creak_door(0.6), 0.3); add(T(ev["light"]) - 0.05, click(), 0.7); add(T(ev["light"]), thud(70, 0.6, 0.12), 0.7)
add(T(ev["light"]), riser(0.3)[::-1], 0.3)
# 18 sumka yerga tushadi (qism taraqlashi)
add(T(ev["drop"]), thud(60, 0.7, 0.14), 1.0); add(T(ev["drop"]), clank(0.5), 0.45); add(T(ev["drop"]) + 0.05, crackle(0.4, 50), 0.25)
# 19 qochish: tez qadamlar
add(T(S["flee"]), steps(T(S["open"]) - T(S["flee"]), 0.22), 0.4); add(T(S["flee"]), whoosh(0.7, 1200, 0.5), 0.3)
# 20 sumka ochiladi
add(T(S["open"]) + 0.6, zipper(0.9), 0.45)
# 21 TV joyida: hayrat zarbasi
add(T(S["nottv"]), thud(80, 0.6, 0.12), 0.7); add(T(S["nottv"]) + 0.1, ding(1760, 0.8), 0.25)
# 22 qismlar: kulgili "ta-da" (pastlab)
add(T(S["parts"]) + 0.3, sting(1.6), 0.55)
# 24 eslash: sekin, filtrlangan otvyortka + tiqillash
add(T(S["flashback"]), riser(0.5)[::-1], 0.3); add(T(S["flashback"]), lp(screw(T(S["street"]) - T(S["flashback"])), 2500), 0.3)
# 25 ko'cha: yugurish, shamol
add(T(S["street"]), steps(DUR - T(S["street"]), 0.2), 0.4); add(T(S["street"]), fade(lp(noise(DUR - T(S["street"])), 500), 0.3, 0.6), 0.25)
out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
