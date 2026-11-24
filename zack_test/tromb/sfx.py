# "Uzoq o'tirish -> tromb -> o'pka tromboemboliyasi" videosi uchun tovush effektlari (sintez) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: python3 -I zack_test/tromb/sfx.py <chiqish.wav> [events.json]
# events.json: EVENTS=... bilan tromb.py yozadi (kesishlar, nasos sikllari, tromb, uzilish, tiqilish, yiqilish kadrlari).
# Yordamchilar chotka/sfx.py dan.
import sys, wave
import numpy as np

SR = 48000; DUR = 40.25
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

import json, os
EV = {"shots": [[1, "hook"], [45, "desk"], [120, "xlegs"], [171, "puddle"], [231, "calf"], [284, "pump"], [399, "slow"], [472, "clot"],
                [570, "face"], [607, "stand"], [662, "detach"], [714, "travel"], [784, "lung"], [839, "choke"], [898, "lungdark"], [944, "end"]],
      "stop": 381, "tromb": 527, "rip": 700, "lodge": 818, "stand": 609, "walk": 646, "die": 841, "knees": 885, "cycles": [290, 314, 338, 362], "end": 966}
if len(sys.argv) > 2 and os.path.exists(sys.argv[2]): EV.update(json.load(open(sys.argv[2])))
SH = {n: f for f, n in EV["shots"]}
names = [n for f, n in EV["shots"]]
def rng_(n):
    i = names.index(n); a = SH[n]; b = SH[names[i + 1]] - 1 if i + 1 < len(names) else EV["end"]
    return T(a), T(b + 1)
def bed(x, a, b, fi=0.04, fo=0.04):
    n = int((b - a) * SR); y = x[:n] if len(x) >= n else np.resize(x, n)
    add(a, fade(y, fi, fo))
# 1) samolyot g'uvillashi (salon kadrlari): past chastotali shovqin + 110 Hz tonal
eng = lp(noise(DUR), 220, 2) * 0.5 + 0.05 * np.sin(2 * np.pi * 112 * np.arange(int(SR * DUR)) / SR) + bp(noise(DUR), 400, 1200) * 0.05
for n in ("hook", "xlegs", "calf", "face", "stand", "travel", "choke", "end"):
    a, b = rng_(n); bed(eng[int(a * SR):], a, b)
# 2) xona: klaviatura chiqillashi + soat tez chiqillaydi (timelapse)
a, b = rng_("desk")
t = a + 0.05
while t < b - 0.1:
    add(t, bp(noise(0.03), 1500, 6000) * env(int(0.03 * SR), 0.001, 0.008), 0.35); t += rng.uniform(0.07, 0.16)
t = a + 0.1
while t < b - 0.05:
    add(t, bp(noise(0.02), 2500, 7000) * env(int(0.02 * SR), 0.0005, 0.004), 0.5); t += 0.09
add(a, riser(b - a) * 0.12)
# 3) tomir ichi: ho'l oqim shovqini; ko'lmakda sekinlashadi
for n, g0, g1 in (("puddle", 0.7, 0.15), ("slow", 0.18, 0.12), ("clot", 0.12, 0.1), ("detach", 0.12, 0.8), ("pump", 0.3, 0.3)):
    a, b = rng_(n); d = b - a; x = lp(noise(d), 500, 2) * np.linspace(g0, g1, int(d * SR)) + bp(noise(d), 80, 300) * 0.3
    bed(x, a, b, 0.03, 0.05)
# 4) har kesishda whoosh (Zack D. montaji)
for f, n in EV["shots"][1:]:
    add(T(f) - 0.18, whoosh(0.45, 1800, 0.55), 0.45)
# 5) ilgak: crash zoom
add(T(SH["desk"] - 14) - 0.3, whoosh(0.5, 2500, 0.8), 0.6)
# 6) nasos: har siqilishda "chuv" + past zarba; to'xtaganda pasayuvchi "power down"
for c0 in EV["cycles"]:
    add(T(c0), squelch(0.3, 420), 0.6); add(T(c0), thud(70, 0.4, 0.1), 0.6)
st = T(EV["stop"]); d = 1.0; tt = t_(d); f = 160 * np.exp(-tt / 0.35) + 30
add(st, np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.005, 0.5) * 0.7); add(st, thud(45, 1.0, 0.35), 0.8)
# 7) tromb: riser -> zarba
add(T(EV["tromb"]) - 1.4, riser(1.4), 0.35); add(T(EV["tromb"]), thud(55, 1.0, 0.3), 1.0); add(T(EV["tromb"]), squelch(0.35, 300), 0.5)
# 8) yuz: sekin tushadigan drone ("Eng dahshatlisi")
a, b = rng_("face"); d = b - a + 0.6; tt = t_(d)
add(a, np.sin(2 * np.pi * np.cumsum(70 - 15 * tt / d) / SR) * np.minimum(1, tt / 0.3) * np.exp(-tt / 1.5) * 0.35)
# 9) o'rnidan turish: o'rindiq g'ichirlashi, qadam tovushlari
add(T(EV["stand"]) + 0.2, bp(noise(0.5), 300, 1500) * env(int(0.5 * SR), 0.05, 0.15), 0.25)
for k in range(5): add(T(EV["walk"]) + 0.1 + k * 0.5, thud(90, 0.2, 0.04), 0.35)
# 10) uzilish: yirtilish + whoosh
add(T(EV["rip"]) - 0.15, squelch(0.4, 650), 0.8); add(T(EV["rip"]), whoosh(0.9, 1200, 0.3), 0.8); add(T(EV["rip"]), thud(60, 0.6, 0.15), 0.6)
# 11) tromb o'pkaga uchadi: riser; tiqilishda kuchli zarba + qo'ng'iroq
a, b = rng_("travel"); add(a, riser(b - a), 0.25)
lo = T(EV["lodge"]); add(lo, thud(40, 1.4, 0.45), 1.1); add(lo, squelch(0.3, 250), 0.6)
tt = t_(2.2); add(lo, np.sin(2 * np.pi * 1850 * tt) * env(len(tt), 0.005, 0.7) * 0.06)
# 12) yurak urishi: tromb yo'lga chiqqanda tezlashadi, oxirida notekis
t = T(SH["travel"]); per = 0.85
while t < T(EV["end"]) - 0.2:
    add(t, heartbeat(), 0.55 if t < T(SH["choke"]) else 0.75)
    per = max(0.42, per * 0.97); t += per + (rng.uniform(-0.12, 0.2) if t > T(SH["lungdark"]) else 0)
# 13) yiqilish: tizzalar polga
add(T(EV["knees"]), thud(75, 0.5, 0.12), 0.8)
add(T(EV["die"]) + 0.1, bp(noise(0.6), 200, 900) * env(int(0.6 * SR), 0.02, 0.2), 0.3)          # xirillash
# 14) yakun: past drone, sekin so'nadi
a, b = rng_("end"); d = b - a + 0.3; tt = t_(d)
add(a - 0.3, lp(noise(d), 120, 2) * np.minimum(1, tt / 0.2) * np.exp(-tt / 0.9) * 0.6)

out = out / (np.abs(out).max() + 1e-9) * 0.7
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", sys.argv[1], round(len(out) / SR, 2), "s")
