# "Qo'l quritgich — bakteriyalar" videosi uchun tovush effektlari (sintez) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: python3 -I zack_test/quritgich/sfx.py /tmp/claude-0/audio/sfx_q.wav [events.json]
import sys, wave, json
import numpy as np

SR = 48000; DUR = 40.55
rng = np.random.default_rng(26)
out = np.zeros(int(SR * DUR))
EV = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {
    "shots": [[1, "hook"], [34, "wash"], [70, "walk"], [103, "dryer"], [144, "spray"], [223, "intake"], [327, "flush"], [361, "plume"],
              [424, "drift"], [454, "filter"], [499, "button"], [538, "fan"], [587, "speed"], [662, "hit"], [738, "study"], [816, "grow"],
              [863, "towel"], [910, "x27"]],
    "purk": 204, "press": 522, "hit": 725, "flush": 337, "t200": 611, "x27": 911, "dry_on": [[1, 33], [113, 326], [526, 737]], "end": 973}
S = {n: f for f, n in EV["shots"]}
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
    n = len(x); e = np.ones(n); na, nb = max(1, int(a * SR)), max(1, int(b * SR))
    e[:na] = np.linspace(0, 1, na); e[n - nb:] = np.linspace(1, 0, nb); return x * e
def norm(x): return x / (np.abs(x).max() + 1e-9)

def thud(f=60, d=0.8, decay=0.25):
    t = t_(d); sweep = f * (1 + 1.5 * np.exp(-t / 0.03))
    return np.sin(2 * np.pi * np.cumsum(sweep) / SR) * env(len(t), 0.002, decay) + 0.3 * lp(noise(d), 400) * env(len(t), 0.002, 0.05)
def whoosh(d=0.6, fc=1600, peak=0.7):
    t = t_(d); shape = np.exp(-((t / d - peak) ** 2) / 0.03)
    return norm(hp(lp(noise(d), fc, 2), fc * 0.25)) * shape
def riser(d=2.0):
    t = t_(d); f = 200 + 1800 * (t / d) ** 2
    return (0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR) + norm(bp(noise(d), 800, 6000)) * 0.6) * (t / d) ** 2
def click():
    t = t_(0.06); return norm(bp(noise(0.06), 1500, 9000)) * env(len(t), 0.0005, 0.008) + 0.5 * np.sin(2 * np.pi * 2400 * t) * env(len(t), 0.0005, 0.01)
def dryer(d, spin=0.35):                            # issiq havo quritgichi: past g'uvullash + kuchli shovqin
    t = t_(d); ramp = np.minimum(1, t / spin)
    rumble = np.sin(2 * np.pi * np.cumsum(70 + 50 * ramp) / SR) * 0.25
    hiss = norm(bp(noise(d), 300, 5000)) * 0.75
    whine = 0.08 * np.sin(2 * np.pi * np.cumsum(900 + 500 * ramp) / SR)
    return fade((rumble + hiss + whine) * ramp, 0.01, 0.12)
def water(d):
    t = t_(d); x = norm(bp(noise(d), 500, 7000)) * (0.75 + 0.25 * np.sin(2 * np.pi * 11 * t) * rng.uniform(0.5, 1))
    return fade(x, 0.05, 0.1)
def flush(d=2.6):
    t = t_(d); x = norm(lp(noise(d), 1800, 2)) * (np.minimum(1, t / 0.15) * np.exp(-np.maximum(0, t - 1.0) / 0.7))
    gurgle = sum(np.sin(2 * np.pi * np.cumsum(rng.uniform(120, 300) * (1 + 0.3 * np.sin(2 * np.pi * rng.uniform(3, 8) * t))) / SR) for _ in range(4))
    return x + 0.12 * gurgle * np.exp(-t / 1.2)
def step():
    t = t_(0.12); return lp(noise(0.12), 900) * env(len(t), 0.002, 0.03) * 0.8 + 0.3 * np.sin(2 * np.pi * 90 * t) * env(len(t), 0.001, 0.03)
def paper(d):
    x = np.zeros(int(SR * d))
    for k in range(int(d * 30)):
        i = rng.integers(0, len(x) - 2400); c = norm(bp(noise(0.05), 2000, 9000)) * env(2400, 0.001, 0.008) * rng.uniform(0.2, 1)
        x[i:i + 2400] += c
    return x
def bubbles(d, rate=14):
    x = np.zeros(int(SR * d))
    for k in range(int(d * rate)):
        f0 = rng.uniform(500, 1600); t = t_(0.12); f = f0 * (1 + 1.2 * np.exp(-t / 0.02))
        b = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.001, 0.03) * rng.uniform(0.2, 0.6)
        i = rng.integers(0, len(x) - len(b)); x[i:i + len(b)] += b
    return x
def ding(f=1320, d=0.9):
    t = t_(d); return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2.01 * f * t)) * env(len(t), 0.002, 0.25)
def boom(d=1.6):
    t = t_(d); return thud(45, d, 0.5) + 0.4 * norm(lp(noise(d), 250)) * env(len(t), 0.003, 0.4)

# --- fon: hojatxona xonasi tovushi (ventilyatsiya), laboratoriyada past g'uvullash ---
room_end = T(S["study"]); amb = norm(lp(noise(room_end), 400, 2)) * 0.05
add(0, fade(amb, 0.3, 0.3))
lab = T(EV["end"]) - room_end
add(room_end, fade(0.05 * np.sin(2 * np.pi * 55 * t_(lab)) + 0.02 * norm(lp(noise(lab), 300)), 0.2, 0.6))
add(T(S["towel"]), fade(norm(lp(noise(T(S["x27"]) - T(S["towel"])), 400, 2)) * 0.05, 0.05, 0.05))
# kesishlarda whoosh
for f, n in EV["shots"][1:]:
    add(T(f) - 0.32, whoosh(0.45, rng.uniform(1200, 2400)), 0.25)
# quritgich ishlashi
for a, b in EV["dry_on"]:
    d = T(b) - T(a) + 0.1; add(T(a), dryer(d), 0.32)
add(T(1), thud(70, 0.6, 0.2), 0.5)
# kran suvi (yuvish)
add(T(S["wash"]) - 0.1, water(T(S["walk"]) - T(S["wash"]) + 0.2), 0.22)
# qadamlar
for k in range(4):
    add(T(S["walk"]) + 0.12 + k * 0.36, step(), 0.35)
# "purkash" zarbasi
add(T(EV["purk"]), thud(55, 0.9, 0.3), 0.7); add(T(EV["purk"]) - 0.25, whoosh(0.4), 0.4)
# havo so'rilishi: teskari whoosh
add(T(S["intake"]), riser(3.5) * 0.25, 1.0)
# unitaz yuvilishi va "fontan"
add(T(EV["flush"]) - 0.05, click(), 0.6)
add(T(EV["flush"]), flush(2.6), 0.5)
add(T(S["plume"]), riser(1.6), 0.35); add(T(S["plume"]) + 1.6, thud(60, 0.6, 0.2), 0.4)
# filtrga yopishish (ho'l chirsillash)
add(T(S["filter"]), bubbles(T(S["button"]) - T(S["filter"]), 18), 0.35)
# tugma
add(T(EV["press"]) - 0.02, click(), 0.9); add(T(EV["press"]), thud(80, 0.4, 0.12), 0.5)
# tezlik: kuchli whoosh, "200" ding
add(T(S["speed"]), riser(1.0), 0.3)
for k in range(5):
    add(T(S["speed"]) + 0.5 + k * 0.55, whoosh(0.5, 2500), 0.35)
add(T(EV["t200"]), ding(1320, 0.9), 0.3)
# qo'lga urilish
add(T(EV["hit"]) - 0.3, whoosh(0.35, 3000), 0.5); add(T(EV["hit"]), thud(50, 1.0, 0.35), 0.9)
add(T(EV["hit"]), bubbles(0.8, 30), 0.4)
# laboratoriya: koloniyalar o'sishi (pufakchalar)
add(T(S["study"]) + 0.2, ding(880, 1.2), 0.15)
add(T(S["grow"]), fade(bubbles(T(S["towel"]) - T(S["grow"]), 22), 0.1, 0.2), 0.35)
# qog'oz sochiq
add(T(S["towel"]) + 0.1, paper(T(S["x27"]) - T(S["towel"]) - 0.2), 0.25)
# 27x
add(T(EV["x27"]) - 0.6, riser(0.6), 0.35); add(T(EV["x27"]), boom(1.8), 0.9); add(T(EV["x27"]) + 0.15, ding(660, 1.5), 0.2)
add(T(EV["x27"]) + 0.2, fade(bubbles(2.0, 40), 0.05, 0.6), 0.3)

out = np.tanh(out * 1.2) * 0.85
w = wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
print("sfx", round(len(out) / SR, 2), "s")
