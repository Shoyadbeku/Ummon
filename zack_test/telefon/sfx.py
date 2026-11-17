# "Telefon portlashi" videosi uchun tovush effektlari (sintez) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: python3 -I zack_test/telefon/sfx.py <chiqish.wav> [events.json]   (events: EVENTS=... telefon.py)
# Yordamchi funksiyalar ogri/sfx.py dan.
import sys, wave
import numpy as np

SR = 48000; DUR = 43.65
rng = np.random.default_rng(27)
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


# ---------------- voqealar (kadr raqamlari telefon.py dan) ----------------
ev = {"plug": 26, "xr": 177, "short": 793, "crack": 958, "boom": 985, "land": 999, "cpu_zoom": 456, "end": 1047}
SHOTS = [1, 59, 119, 164, 210, 287, 383, 431, 491, 604, 673, 719, 786, 827, 880, 932, 978]
if len(sys.argv) > 2:
    import json; j = json.load(open(sys.argv[2])); ev.update(j); SHOTS = [s[0] for s in j["shots"]]
def shot(i): return T(SHOTS[i])
def hum(d, f=120):                                  # elektr g'uvillashi (zaryad)
    t = t_(d); return fade(0.35 * np.sin(2 * np.pi * f * t) + 0.2 * np.sin(2 * np.pi * 2 * f * t) + 0.15 * bp(noise(d), 2000, 6000), 0.2, 0.3)
def chip(f=660, d=0.07):                             # o'yin "piu"
    t = t_(d); ff = f * (1 + 0.6 * np.exp(-t / 0.02))
    return np.sign(np.sin(2 * np.pi * np.cumsum(ff) / SR)) * 0.3 * env(len(t), 0.002, d / 2)
def game_music(d):
    x = np.zeros(int(SR * d)); notes = [523, 659, 784, 659, 587, 698, 880, 698]; k = 0; t = 0.0
    while t < d - 0.15:
        c = chip(notes[k % 8], 0.12); i = int(t * SR); x[i:i + len(c)] += c[: len(x) - i] * 0.6; k += 1; t += 0.14
    return x
def sizzle(d):                                       # qizish shivirlashi
    t = t_(d); return fade(bp(noise(d), 2500, 9000) * (0.4 + 0.6 * t / d), 0.3, 0.2)
def fire_roar(d):
    t = t_(d); n = lp(noise(d), 600, 2); m = 0.6 + 0.4 * lp(np.abs(noise(d)), 6, 1) * 3
    return fade(n * m * 4 + crackle(d, 40) * 0.5, 0.01, 0.6)

# 1) har kesishda yengil "whoosh"
for i in range(1, len(SHOTS)): add(shot(i) - 0.25, whoosh(0.4, 1800, 0.62), 0.22)
# 2) vilka ulanishi: klik + zaryad signali
add(T(ev["plug"]), click(), 1.0); add(T(ev["plug"]) + 0.08, beep(1046, 0.12), 0.35); add(T(ev["plug"]) + 0.22, beep(1568, 0.16), 0.35)
# 3) o'yin musiqasi (xona kadrlarida, sekin)
add(shot(1), game_music(T(SHOTS[4]) - shot(1)), 0.12)
add(shot(6), game_music(shot(7) - shot(6)), 0.16)
add(shot(14), game_music(shot(15) - shot(14)) * np.linspace(1, 0.3, int(SR * (shot(15) - shot(14))))[: int(SR * (shot(15) - shot(14)))], 0.12)
# 4) rentgen: "reaktor" — past drone + yurak urishi
add(T(ev["xr"]), zap(0.4), 0.5); add(T(ev["xr"]), drone(T(SHOTS[5]) - T(ev["xr"]), 50), 0.35)
for k in range(4): add(T(ev["xr"]) + 0.3 + k * 0.75, heartbeat(), 0.45)
# 5) zaryad oqimi va ionlar: g'uvillash + pufakchalar
add(shot(4), hum(shot(6) - shot(4)), 0.18); add(shot(5), bubbles(shot(6) - shot(5)) * 0.5, 0.25)
# 6) protsessor: crash zoom zarbasi + kuchayuvchi shivirlash
add(T(ev["cpu_zoom"]), thud(70, 0.6, 0.15), 0.9); add(T(ev["cpu_zoom"]), riser(0.5), 0.3)
add(shot(8), hum(shot(9) - shot(8), 180), 0.2)
# 7) qizish -> erish: riser + shivirlash + yurak urishi tezlashadi
add(shot(9), sizzle(T(ev["short"]) - shot(9)), 0.25)
add(T(ev["short"]) - 2.6, riser(2.6), 0.45)
for k, tt in enumerate(np.arange(shot(9), T(ev["short"]) - 0.3, 0.62 - 0.0)):
    add(tt, heartbeat(), 0.25 + 0.03 * k)
add(shot(10), crackle(shot(11) - shot(10), 25), 0.35)
# 8) qisqa tutashuv: elektr "zap" + portlash zarbasi
add(T(ev["short"]), zap(0.5) * 1.5, 0.9); add(T(ev["short"]), thud(55, 1.0, 0.35), 1.0); add(T(ev["short"]), crackle(1.6, 60), 0.6)
# 9) shishish: g'ichirlash + vishillash
add(shot(13), creak_door(1.0) * 0.6, 0.35); add(shot(13) + 0.4, sizzle(shot(15) - shot(13) - 0.4), 0.35)
add(shot(14), hp(noise(shot(15) - shot(14)), 3000) * np.linspace(0, 1, int(SR * (shot(15) - shot(14)))), 0.15)
# 10) ekran yoriladi: shisha sinishi + uchqunlar
add(T(ev["crack"]), snap(0.35), 1.0); add(T(ev["crack"]), crackle(1.2, 70), 0.7); add(T(ev["crack"]) - 0.6, riser(0.6), 0.35)
# 11) portlash: kuchli zarba + olov guvillashi, telefon stolga tushadi
add(T(ev["boom"]), boom(2.5), 1.0); add(T(ev["boom"]), thud(45, 1.4, 0.5), 1.0)
add(T(ev["boom"]) + 0.05, fire_roar(T(ev["end"]) - T(ev["boom"]) + 0.3), 0.55)
add(T(ev["land"]), clank(0.4) * 0.5, 0.6)

out = out / (np.abs(out).max() + 1e-9) * 0.85
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", len(out) / SR)
