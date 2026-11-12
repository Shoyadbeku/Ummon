# "Pichoqni sug'urma" videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/pichoq/sfx.py /tmp/claude-0/audio/sfx_pichoq.wav
# (yordamchi sintez funksiyalari zack_test/goz/sfx.py dan)
import sys, wave
import numpy as np

SR = 48000; DUR = 39.6
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

def growl(d=1.2, f0=70):                            # ajdod bo'kirishi / yirtqich irillashi
    t = t_(d); f = f0 * (1 + 0.25 * np.sin(2 * np.pi * 5.5 * t) + 0.15 * rng.standard_normal(len(t)).cumsum() / np.sqrt(len(t)))
    ph = 2 * np.pi * np.cumsum(f) / SR
    saw = sum(np.sin(k * ph) / k for k in range(1, 40))
    rough = 0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 31 * t))
    return (bp(saw * rough, 80, 2400) + 0.5 * bp(noise(d), 200, 3000)) * np.minimum(1, t / 0.12) * np.exp(-np.maximum(0, t - d * 0.7) / 0.2)
def thunder(d=3.0):
    t = t_(d); c = hp(noise(0.25), 1500) * env(int(SR * 0.25), 0.001, 0.05)
    rum = lp(noise(d), 160, 2) * (np.minimum(1, t / 0.05) * np.exp(-t / 1.1)) * (0.7 + 0.3 * np.sin(2 * np.pi * 3 * t))
    x = rum / (np.abs(rum).max() + 1e-9); x[: len(c)] += c * 0.8; return x
def tingle(d=1.2):                                  # "jimirlash": mayda chirsillashlar ko'tariladi
    x = crackle(d) * np.linspace(0.2, 1, int(SR * d)); t = t_(d)
    return x + 0.3 * bp(noise(d), 4000, 12000) * (t / d)


def pluck(d=0.18):                                  # sochni yulish: "chirt"
    t = t_(d); x = bp(noise(d), 2500, 11000) * env(len(t), 0.0005, 0.012)
    tk = np.zeros(len(t)); k = tick(2600); tk[: len(k)] = k
    return x * 1.4 + 0.4 * tk
def tear(d=0.35):                                   # to'qima uzilishi (ho'l "yirt")
    return crackle(d) * 0.8 + squelch(d, 300) * 0.8
def pop(f0=900):
    t = t_(0.12); f = f0 * (1 + 2.5 * np.exp(-t / 0.01))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.001, 0.03)
def stinger(d=1.6, f0=58):                           # qorong'i "BRAAM"
    t = t_(d); ph = 2 * np.pi * f0 * t
    saw = sum(np.sin(k * ph) / k for k in range(1, 25))
    return lp(saw, 900) * env(len(t), 0.01, d / 2.2) + 0.5 * thud(40, d, 0.5)

def shing(d=0.9):                                    # po'lat tig' "shiing"
    t = t_(d); x = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((3150, 0.5), (4720, 0.35), (6890, 0.25), (2210, 0.3)))
    return (x * env(len(t), 0.003, 0.25) + 0.6 * bp(noise(d), 3000, 12000) * env(len(t), 0.002, 0.08))
def scratch(d=0.55):                                 # plastinka to'xtashi ("Lekin...")
    t = t_(d); f = 900 * np.exp(-t / 0.15) + 60
    return (bp(noise(d), 400, 5000) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * np.cumsum(f / 6) / SR))) +
            0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * env(len(t), 0.002, d / 2)
def zap(d=0.35):                                     # asab tolasi uzilishi: elektr chirsillashi
    t = t_(d); buzz_ = np.sign(np.sin(2 * np.pi * 120 * t)) * bp(noise(d), 1500, 9000)
    return (buzz_ * 0.6 + crackle(d) * 0.8) * env(len(t), 0.001, d / 3)
def snap(d=0.12):
    t = t_(d); return bp(noise(d), 1200, 8000) * env(len(t), 0.0005, 0.02) + 0.5 * thud(140, d, 0.03)
def gush(d=2.4):                                     # bosim ostidagi qon oqimi
    t = t_(d); x = lp(noise(d), 1400, 2) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * t) ** 2)
    x = x / (np.abs(x).max() + 1e-9)
    return x * np.minimum(1, t / 0.03) * np.exp(-np.maximum(0, t - d * 0.6) / 0.4)
def clink(f0=2600):
    t = t_(0.6); return sum(np.sin(2 * np.pi * f0 * k * t) / k for k in (1, 2.7, 5.1)) * env(len(t), 0.001, 0.12)
def siren(d=2.0):
    t = t_(d); f = np.where((t * 1.6) % 1 < 0.5, 960, 770)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, t / 0.3) * np.minimum(1, (d - t) / 0.3)
def beep(d=0.12, f=1000):
    t = t_(d); return np.sin(2 * np.pi * f * t) * np.minimum(1, t / 0.005) * np.minimum(1, (d - t) / 0.005)

tt = np.arange(len(out)) / SR
drone = sum(np.sin(2 * np.pi * f * tt) for f in (41, 49.2, 61.7)) / 3 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * tt))
out += drone * (0.012 + 0.03 * np.clip((tt - 9.8) / 20, 0, 1)) * np.clip((39.4 - tt) / 1.0, 0, 1)
CUTS = (32, 72, 96, 136, 184, 237, 286, 335, 361, 398, 462, 514, 556, 625, 693, 721, 772, 849, 890)
for f in CUTS: add(T(f) - 0.3, whoosh(0.4, 1800, 0.8), 0.2)
# 1–4: kino — epik braam, pichoq sug'urilishi
add(T(1), stinger(2.2, 55), 0.55); add(T(1), riser(1.3), 0.12)
add(T(40), squeak(0.2), 0.12); add(T(72), thud(70, 0.4, 0.1), 0.3)
add(T(96), riser(0.85), 0.25)
add(T(115), squelch(0.3, 420), 0.7); add(T(117), shing(1.0), 0.75); add(T(117), stinger(1.5, 62), 0.55)
# 5–6: haqiqat — plastinka to'xtaydi, tizzaga, yerga
add(T(136), scratch(0.6), 0.8)
add(T(175), thud(60, 0.6, 0.15), 0.8); add(T(198), thud(45, 1.0, 0.25), 0.95); add(T(200), stinger(1.8, 44), 0.45)
# 7–8: mehmonxona, rentgen yurak urishi
add(T(237), riser(1.8), 0.1)
for f in range(286, 336, 17): add(T(f), heartbeat(), 0.45)
add(T(296), tingle(0.8), 0.15)
# 9–11: makro oqim, shisha
add(T(335), whoosh(1.0, 700, 0.3), 0.5)
add(T(335), fade(bubbles(T(461) - T(335)), 0.2, 0.3), 0.18)
add(T(366), clink(2600), 0.4); add(T(380), clink(3100), 0.2)
for f in range(398, 462, 17): add(T(f), heartbeat(), 0.25)
# 12–13: torta boshlaydi — taranglik
add(T(462), riser(2.3), 0.22); add(T(520), creak(1.2, 120), 0.3); add(T(553), thud(55, 0.6, 0.15), 0.6)
# 14–15: tig' qaytadi, tolalar uziladi
add(T(560), fade(squelch(T(692) - T(560), 260), 0.3, 0.3), 0.25)
for f in (612, 640, 668): add(T(f), zap(0.4), 0.85); add(T(f), snap(), 0.8)
for f in (604, 626, 652, 676, 686): add(T(f), tear(0.3), 0.5)
# 16–17: tiqin otiladi, qon favvorasi
add(T(699), squeak(0.15), 0.3); add(T(701), pop(420), 1.0); add(T(701), thud(110, 0.3, 0.05), 0.6)
add(T(702), fade(hiss(0.9), 0.02, 0.4), 0.45)
add(T(PULL := 722), squelch(0.4, 300), 0.9); add(T(725), fade(gush(2.4), 0.02, 0.6), 0.85); add(T(722), stinger(1.6, 50), 0.5)
# 18: ichki bo'shliqqa favvora
add(T(772), fade(gush(3.2), 0.1, 0.8), 0.5)
for f in range(772, 849, 15): add(T(f), heartbeat(), 0.5)
# 19: tez yordam sireni (uzoqdan)
add(T(849), lp(siren(1.9), 2500), 0.22)
# 20: yurak sekinlashadi, monitor "pip" -> to'xtaydi
f = 890; per = 18
while f < 935:
    add(T(f), heartbeat(), 0.55); add(T(f), beep(0.1, 1000), 0.12); f += per; per += 6
add(T(937), beep(1.4, 1000), 0.14)
out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
