# Qulf videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/qulf/sfx.py /tmp/claude-0/audio/sfx_qulf.wav
import sys, wave
import numpy as np

SR = 48000; DUR = 40.2
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
def hic(pitch=1.0):                                 # "hik!": glottis chertishi + qisqa ovoz (formantlar)
    d = 0.16; t = t_(d)
    click = bp(noise(0.012), 800, 9000) * env(int(SR * 0.012), 0.0005, 0.003)
    f0 = 260 * pitch * (1 + 0.25 * np.exp(-t / 0.02))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    src = sum(np.sin(k * ph) / k for k in range(1, 25))
    voc = bp(src, 300, 3200) * np.minimum(1, t / 0.006) * np.exp(-t / 0.035)
    breath = bp(noise(d), 1200, 6000) * env(len(t), 0.002, 0.03) * 0.5
    x = voc * 0.9 + breath; x[: len(click)] += click * 1.2
    return x
def inhale(d=0.5):                                  # keskin havo tortish
    t = t_(d); return bp(noise(d), 900, 5000) * (t / d) ** 2 * np.exp(-np.maximum(0, t - d * 0.85) / 0.02)
def slam(d=0.5):                                    # yopilish: ho'l "tap" + zarba
    x = thud(70, d, 0.12) * 0.8; q = squelch(0.15, 700); x[:len(q)] += q * 0.6
    return x


def clink(f0=2400, d=0.4):                          # metall "chiq"
    t = t_(d); x = sum(np.sin(2 * np.pi * f0 * k * t) * np.exp(-t / (0.08 / k)) / k for k in (1, 2.76, 5.4))
    x[:600] += bp(noise(600 / SR), 2000, 9000) * np.exp(-np.arange(600) / 80)
    return x * env(len(t), 0.0005, d)
def rattle(d=1.0, rate=14):                         # qulf silkinishi
    x = np.zeros(int(SR * d))
    for k in range(int(d * rate)):
        i = int(k / rate * SR + rng.integers(0, 400)); c = clink(rng.uniform(1400, 2600), 0.15) * rng.uniform(0.3, 0.8)
        x[i:i + len(c)] += c[: len(x) - i]
    return x
def creak(d=1.5):                                   # zang g'ichirlashi
    t = t_(d); f = 160 + 60 * np.sin(2 * np.pi * 0.7 * t)
    pulses = (np.sin(2 * np.pi * np.cumsum(f) / SR) > 0.97).astype(float)
    return bp(pulses + 0.2 * noise(d), 300, 3000) * np.sin(np.pi * t / d)
def rain_amb(d):
    t = t_(d); x = bp(noise(d), 500, 9000) * 0.6 + lp(noise(d), 300) * 0.4
    for k in range(int(d * 60)):
        i = rng.integers(0, len(x) - 3000); b = drip(rng.uniform(1500, 4000)) * rng.uniform(0.1, 0.4); x[i:i + len(b)] += b[: len(x) - i]
    return fade(x, 0.15, 0.2)
def wind(d):
    t = t_(d); return fade(bp(noise(d), 200, 1200) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.4 * t)), 0.2, 0.25)

tt = np.arange(len(out)) / SR
drone = sum(np.sin(2 * np.pi * f * tt) for f in (55, 82.4, 110)) / 3 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * tt))
out += drone * 0.02 * np.clip((39.7 - tt) / 1.5, 0, 1)
for f in (46, 91, 146, 207, 273, 323, 382, 444, 484, 579, 630, 693, 749, 799, 857, 910, 937):
    add(T(f) - 0.3, whoosh(0.4, 1800, 0.8), 0.22)
add(T(1), riser(T(40)), 0.12); add(T(40), thud(60, 0.5, 0.12), 0.5)          # ilgak push-in
add(T(8), rattle(0.6, 10), 0.35)                                              # qiz qulfni ushlaydi
add(T(178), clink(2600, 0.5), 0.8); add(T(181), clink(2300, 0.3), 0.4); add(T(184), clink(2500, 0.3), 0.4)   # kalit sig'maydi
add(T(207), rain_amb(T(273) - T(207) + 0.2), 0.35)
add(T(273), wind(T(323) - T(273) + 0.2), 0.3)
for f in (330, 342, 356, 366): add(T(f), drip(1600), 0.5)                     # tomchi kalit teshigiga
for f in range(386, 470, 9): add(T(f), drip(rng.uniform(900, 1500)), 0.35)    # ichkarida to'planadi
add(T(390), bubbles(2.0), 0.2)
add(T(488), creak(3.6), 0.4); add(T(488), crackle(3.8), 0.15)                 # zang (timelapse)
for f in range(490, 576, 6): add(T(f), tick(900), 0.15)
add(T(584), crackle(1.6), 0.4); add(T(590), tinkle(1.4), 0.45)               # muzlash
add(T(630), wind(T(693) - T(630) + 0.2), 0.3)
add(T(634), rattle(1.2, 12), 0.7); add(T(662), thud(48, 0.9, 0.3), 0.9); add(T(664), rattle(1.0, 8), 0.5)   # tortadi, ochilmaydi
add(T(695), lp(noise(2.2), 1500) * np.sin(np.pi * t_(2.2) / 2.2), 0.25)      # suv oqib chiqadi
for f in range(700, 748, 5): add(T(f), drip(rng.uniform(1100, 1700)), 0.3)
for f in (752, 763, 774, 785, 796): add(T(f + 12), drip(1300), 0.6)          # tomchilar tushadi
add(T(806), rattle(0.4, 8), 0.3)
for f in (869, 880, 891, 902): add(T(f), drip(700), 0.55)                    # moy tomchilari
add(T(912), squeak(0.3), 0.3)
for f in (914, 916, 918, 920): add(T(f), tick(1800), 0.5)                    # pinlar tekislanadi
add(T(927), clink(1900, 0.5), 0.7)
add(T(938), squeak(0.25), 0.3); add(T(944), clink(2100, 0.7), 1.0); add(T(944), thud(70, 0.6, 0.12), 0.7)   # "chiq" ochiladi
t = t_(1.2); add(T(948), (np.sin(2 * np.pi * 988 * t) + 0.6 * np.sin(2 * np.pi * 1318 * t)) * env(len(t), 0.002, 0.4), 0.25)

out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
