# "Qaynoq choy" videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/choy/sfx.py /tmp/claude-0/audio/sfx_choy.wav
import sys, wave
import numpy as np

SR = 48000; DUR = 42.32
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


def pour(d):                                        # choy quyilishi: suv oqimi shovqini + pufakchalar
    t = t_(d); x = bp(noise(d), 500, 4500) * (0.6 + 0.4 * np.sin(2 * np.pi * 5.3 * t) ** 2)
    return fade(x * 0.6 + bubbles(d) * 0.8, 0.08, 0.3)
def boil(d):                                        # qaynash: past "bulg'-bulg'"
    x = np.zeros(int(SR * d))
    for k in range(int(d * 22)):
        i = rng.integers(0, len(x) - int(SR * 0.2)); b = drip(rng.uniform(250, 700)) * rng.uniform(0.3, 0.8)
        x[i:i + len(b)] += b[: len(x) - i]
    return fade(lp(x, 2500) + 0.15 * lp(noise(d), 300), 0.1, 0.3)
def sip(d=0.6):                                     # ho'plash: havo bilan so'rish "shhlup"
    t = t_(d); x = bp(noise(d), 1500, 7000) * np.exp(-((t - d * 0.35) / (d * 0.18)) ** 2)
    q = squelch(0.12, 600); x[int(SR * d * 0.55):int(SR * d * 0.55) + len(q)] += q * 0.5
    return x
def gulp():                                         # yutish
    x = thud(110, 0.35, 0.07) * 0.6; q = squelch(0.2, 380); x[:len(q)] += q * 0.8
    return x
def sizzle(d):                                      # kuyish: jazillash
    t = t_(d); return fade(hp(crackle(d) * 1.5 + bp(noise(d), 3000, 11000) * 0.6, 1200) * (0.6 + 0.4 * np.sin(2 * np.pi * 13 * t)), 0.02, d * 0.5)
def snap():                                         # DNK sinishi: quruq "chirt" + jaranglash
    x = bp(noise(0.05), 1500, 9000) * env(int(SR * 0.05), 0.0005, 0.008)
    t = t_(0.8); r = (np.sin(2 * np.pi * 2100 * t) + 0.5 * np.sin(2 * np.pi * 3170 * t)) * env(len(t), 0.001, 0.15) * 0.4
    r[:len(x)] += x * 1.5; return r
def pop(f0=900):                                    # hujayra "pufak" bo'lib o'sishi
    t = t_(0.12); f = f0 * (1 + 0.6 * np.exp(-t / 0.02))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.002, 0.03)

tt = np.arange(len(out)) / SR
drone = sum(np.sin(2 * np.pi * f * tt) for f in (46, 69, 92)) / 3 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * tt))
out += drone * (0.012 + 0.03 * np.clip((tt - 12) / 20, 0, 1)) * np.clip((42.2 - tt) / 1.0, 0, 1)
CUTS = [41, 96, 126, 206, 261, 301, 384, 435, 472, 541, 589, 637, 685, 735, 813, 914, 967]
for f in CUTS: add(T(f) - 0.3, whoosh(0.4, 1800, 0.8), 0.18)
# 1 ilgak: yengil zarba
add(0.0, thud(60, 0.8, 0.2), 0.5)
# 2 choy quyish + qaynash
add(T(44), pour(T(91) - T(44)), 0.45); add(T(41), boil(T(96) - T(41)), 0.35)
# 3 ho'plash (sip) va keyingilari
for f in (100, 112, 268, 604, 980): add(T(f), sip(0.55), 0.55)
for f in (122, 286, 620): add(T(f), gulp(), 0.5)
# 4 rentgen: qaynoq oqim + "kuydirish" (jazillash, zarba)
add(T(128), riser(T(175) - T(128)) * 0.6, 0.14); add(T(175), thud(45, 1.2, 0.35), 0.85); add(T(175), sizzle(1.6), 0.5)
for f in range(140, 205, 18): add(T(f), heartbeat(), 0.25)
# 5 og'iz "qalqoni": past g'uvillash
t = t_(2.2); add(T(208), np.sin(2 * np.pi * 180 * t) * env(len(t), 0.2, 1.2) * 0.3, 0.3)
# 7 qizilo'ngach kesimi: nam "shilliq" tovushi
add(T(330), squelch(0.3, 420), 0.35); add(T(356), squelch(0.25, 520), 0.3)
# 8 termometr: ko'tarilish + "65" zarbasi
add(T(386), riser(T(400) - T(386)), 0.2); add(T(400), thud(70, 0.6, 0.15), 0.6); add(T(400), tick(2400), 0.3)
# 9 tunnel: to'lqin gumburlashi
add(T(436), lp(noise(T(471) - T(436)), 400) * np.linspace(0.3, 1.0, int(SR * (T(471) - T(436)))), 0.35)
add(T(440), sizzle(1.4), 0.25)
# 10 hujayralar: tirik "pufak"lar
for k in range(10): add(T(476) + k * 0.25 + rng.uniform(0, 0.1), pop(rng.uniform(700, 1300)), 0.12)
# 11 kuyish: jazillash + zarba
add(T(543), sizzle(T(588) - T(543)), 0.55); add(T(556), thud(42, 1.2, 0.35), 0.85)
# 13 retseptorlar: elektr chirsillashi, keyin jimlik
add(T(640), crackle(0.9), 0.3); add(T(640), zap(0.5), 0.2)
# 14 timelapse: soat tiqillashi
for k in range(16): add(T(687) + k * 0.13, tick(1500 if k % 2 else 1100), 0.18)
# 15 qayta-qayta: kuyish va o'sish
for f in (761, 791): add(T(f), sizzle(0.6), 0.35)
for k in range(24): add(T(740) + k * 0.13 + rng.uniform(0, 0.05), pop(rng.uniform(600, 1400)), 0.1)
# 16 DNK: sinish
add(T(860), riser(T(889) - T(860)) * 0.7, 0.15); add(T(889), snap(), 0.9); add(T(889), thud(50, 0.9, 0.25), 0.7)
# 17 o'sma: past, xavfli yurak urishi
for f in range(916, 966, 14): add(T(f), heartbeat(), 0.45)
# 18 "sakkiz": og'ir zarba + qo'ng'iroq
add(T(967), thud(38, 1.6, 0.5), 0.95)
t = t_(1.6); add(T(969), (np.sin(2 * np.pi * 330 * t) + 0.5 * np.sin(2 * np.pi * 495 * t)) * env(len(t), 0.003, 0.5) * 0.3, 0.3)

out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
