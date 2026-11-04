# "Illyuminatorni sindirsangiz" videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/illyuminator/sfx.py /tmp/claude-0/audio/sfx_ill.wav
import sys, wave
import numpy as np

SR = 48000; DUR = 54.5
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

tt = np.arange(len(out)) / SR
cabin = lp(noise(DUR), 350, 2); cabin /= np.abs(cabin).max()
out += cabin * 0.06 * np.clip((54.2 - tt) / 1.0, 0, 1)                   # salon g'uvillashi (fon)
CUTS = (54, 112, 148, 192, 240, 305, 373, 445, 515, 571, 625, 697, 776, 826, 875, 919, 985, 1034, 1124, 1202, 1257)
for f in CUTS: add(T(f) - 0.3, whoosh(0.4, 1800, 0.8), 0.18)
# 1 osmon: shamol + dvigatel, kamera uchib boradi
add(0, fade(wind(2.3) * 0.6 + jet(2.3) * 0.4, 0.05, 0.3), 0.22); add(T(20), whoosh(1.2, 1300, 0.7), 0.4)
# 2 bolg'acha: tayyorlanish -> zarba
add(T(70), riser(T(98) - T(70)), 0.12); add(T(98), glass_crack(), 0.8); add(T(98), thud(70, 0.5, 0.1), 0.7)
# 3 yoriqlar tarqaladi
for f in range(114, 146, 7): add(T(f), crackle(0.15), 0.25)
add(T(112), creak(1.4, 260), 0.18); add(T(130), riser(T(152) - T(130)), 0.2)
# 4-5 portlash va dekompressiya
add(T(152), thud(34, 2.2, 0.7), 1.0); add(T(152), glass_break(), 0.8); add(T(152), roar(T(305) - T(152)), 0.55)
add(T(155), alarm(1.2), 0.2)
# 6-7 narsalar uchadi, odam tortiladi
add(T(258), squeak(0.3), 0.2); add(T(270), whoosh(0.5, 2500, 0.6), 0.35); add(T(280), whoosh(0.5, 2000, 0.5), 0.3)
add(T(305), fade(wind(T(445) - T(305), 2200), 0.05, 1.0), 0.35); add(T(318), thud(60, 0.4, 0.1), 0.4)
# 8 sovuq: qirov chirsillashi
add(T(373), hiss(2.5), 0.25); add(T(380), crackle(2.4), 0.12); add(T(395), tinkle(1.5, 18), 0.18)
# 9 tuman
add(T(445), fade(wind(2.9, 700), 0.4, 0.5), 0.3)
# 10 niqoblar tushadi
for f in (519, 522, 525, 528, 531): add(T(f), tick(700 + 37 * (f % 7)), 0.3); add(T(f), thud(110, 0.15, 0.03), 0.2)
add(T(518), alarm(1.2, 988), 0.25)
# 11-12 hushdan ketish: yurak urishi, quloq shang'illashi
add(T(571), heartbeat_slow(T(697) - T(571), 70), 0.35); add(T(640), ring(2.4, 2800), 0.25)
# 13-14 niqob: rezina, nafas
add(T(720), squeak(0.25), 0.2); add(T(735), hiss(0.6), 0.15); add(T(805), squeak(0.25), 0.15); add(T(812), hiss(0.6), 0.12)
# 15-16 sho'ng'ish: dvigatel, shamol kuchayadi
add(T(826), fade(jet(T(919) - T(826)) * 0.6 + wind(T(919) - T(826), 1800) * 0.6, 0.1, 0.4), 0.4)
add(T(875), whoosh(1.6, 1500, 0.5), 0.5)
# 17 yengillik: chuqur nafas, iliq tovush
add(T(925), hiss(1.2), 0.18)
t = t_(2.0); add(T(930), (np.sin(2 * np.pi * 523 * t) + 0.5 * np.sin(2 * np.pi * 784 * t)) * env(len(t), 0.05, 0.8) * 0.25, 0.25)
# 18 yaxshi xabar: "ding"
t = t_(1.6); add(T(1005), (np.sin(2 * np.pi * 1318 * t) + 0.6 * np.sin(2 * np.pi * 1976 * t)) * env(len(t), 0.002, 0.6) * 0.3, 0.3)
# 19 qatlamlar ajraladi
add(T(1040), riser(1.4), 0.12); add(T(1074), thud(55, 0.6, 0.15), 0.4); add(T(1074), tinkle(0.6, 6), 0.2)
# 20 musht: oyna sinmaydi
add(T(1148), thud(65, 0.5, 0.08), 0.8); add(T(1148), tick(900), 0.4); add(T(1152), ring(0.8, 2500), 0.1)
# 22 yakun
add(T(1257), fade(wind(T(1308) - T(1257)) * 0.6 + jet(T(1308) - T(1257)) * 0.4, 0.2, 0.8), 0.2)
add(T(1257), whoosh(1.5, 1200, 0.4), 0.3)

out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
