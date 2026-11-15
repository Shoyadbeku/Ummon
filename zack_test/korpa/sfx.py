# "Ko'rpani boshga yopib uxlash" videosi uchun tovush effektlari (sintez) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: python3 -I zack_test/korpa/sfx.py /tmp/claude-0/audio/sfx_korpa.wav
# Yordamchi funksiyalar quloq/sfx.py (aksirish/sfx.py) dan.
import sys, wave
import numpy as np

SR = 48000; DUR = 44.68
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
def squelch(d=0.25, f0=500):
    t = t_(d); f = f0 * (1 + 0.8 * np.sin(2 * np.pi * 9 * t)) * np.exp(-t / 0.2)
    return (bp(noise(d), 300, 2500) * 0.7 + 0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * env(len(t), 0.004, d / 3)
def drone(d, f=55):
    t = t_(d); return fade(lp(noise(d), 120, 2) * 3 + 0.4 * np.sin(2 * np.pi * f * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * t)), 0.5, 0.8)
def zap(d=0.5):
    t = t_(d); f = 300 + 2500 * t / d
    sq = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR))
    return bp(sq * 0.5 + noise(d) * 0.3, 400, 6000) * env(len(t), 0.01, d / 2)
def beep(f=880, d=0.14):
    t = t_(d); return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * env(len(t), 0.004, d / 2)
def tick(f=2600):
    t = t_(0.03); return hp(noise(0.03), 1500) * env(len(t), 0.0005, 0.004) + 0.4 * np.sin(2 * np.pi * f * t) * env(len(t), 0.0005, 0.006)
def breath(d=1.4, inhale=False):                    # bo'g'iq nafas (ko'rpa ostida)
    t = t_(d); sh = np.sin(np.pi * t / d) ** 2
    return bp(noise(d), 250 if inhale else 180, 1800 if inhale else 1200) * sh
def pop(f0=900):
    t = t_(0.08); f = f0 * (1 + np.exp(-t / 0.01))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.001, 0.02)
def flow(d):                                        # qon oqimi
    t = t_(d); return fade(lp(noise(d), 260, 2) * (0.6 + 0.4 * np.sin(2 * np.pi * 1.2 * t) ** 8), 0.2, 0.3)
def shiver(d):                                      # tishlar taqillashi
    x = np.zeros(int(SR * d)); t = 0.0
    while t < d - 0.03:
        c = bp(noise(0.015), 1500, 6000) * env(int(SR * 0.015), 0.0005, 0.004)
        i = int(t * SR); x[i:i + len(c)] += c[: len(x) - i] * rng.uniform(0.4, 1.0); t += rng.uniform(0.05, 0.09)
    return x
def ring(d, f=3300):
    return np.sin(2 * np.pi * f * t_(d)) * fade(np.ones(int(SR * d)), 0.05, 0.6)

SHOTS = [1, 48, 116, 165, 215, 269, 309, 342, 376, 425, 471, 510, 560, 604, 640, 690, 730, 771, 797, 846, 870, 913, 960, 1002]
for f in SHOTS[1:]: add(T(f) - 0.25, whoosh(0.5, 1800, 0.5), 0.3)
add(0.0, drone(DUR, 48), 0.10)
# 1 ilgak: titrash, tishlar taqillaydi, yurak
add(0.0, riser(0.6), 0.2); add(0.0, shiver(1.9), 0.3); add(T(10), thud(80, 0.4, 0.08), 0.6)
for k in range(2): add(0.25 + k * 0.85, heartbeat(), 0.35)
# 2 ko'rpa tortiladi
add(T(58), whoosh(1.1, 900, 0.6), 0.6); add(T(76), lp(noise(0.5), 600) * env(int(SR * 0.5), 0.01, 0.15), 0.5)
# 3 iliq, tinch: bo'g'iq nafas
add(T(118), breath(1.4, True), 0.4); add(T(150), breath(1.2), 0.35)
# 4–5 chiqindi gaz: chiqish va qayta yutish
add(T(166), breath(1.6), 0.55); add(T(170), riser(1.2), 0.12)
for k in range(10): add(T(170 + k * 3), pop(rng.uniform(600, 1200)), 0.12)
add(T(215), breath(1.1), 0.45); add(T(242), breath(1.1, True), 0.55)
# 6–7 rentgen: o'pka nafas chiqaradi, gaz traxeyadan
add(T(269), lp(noise(3.0), 300) * 0.5, 0.3); add(T(272), breath(2.4), 0.5); add(T(300), zap(0.4), 0.15)
# 8 "4%" va "zaharli"
add(T(342), thud(60, 0.7, 0.15), 0.85); add(T(361), zap(0.5), 0.35); add(T(361), thud(90, 0.4, 0.08), 0.5)
# 9 CO2 molekulasi
add(T(380), whoosh(1.2, 700, 0.5), 0.4); add(T(384), thud(120, 0.3, 0.06), 0.4)
# 10–11 bo'shliq, urilib qaytish
add(T(425), lp(noise(1.9), 400) * 0.5, 0.25)
for k in range(12): add(T(479 + k * 3), thud(170 + 10 * (k % 3), 0.15, 0.03), 0.35); add(T(479 + k * 3), pop(400), 0.15)
# 12 taymer: soat chiqillashi tezlashadi
for k in range(40): add(T(510) + 2.0 * (k / 40) ** 0.8, tick(), 0.4)
add(T(510), riser(2.0), 0.18)
# 13 kislorod yo'qoladi
for k in range(30): add(T(562) + k * (1.55 / 30), pop(1500 - 25 * k), 0.12)
# 14 keskin tushadi: signal
add(T(604), thud(55, 0.8, 0.18), 0.8)
for k in range(4): add(T(612) + k * 0.32, beep(990), 0.3); add(T(612) + k * 0.32 + 0.15, beep(740), 0.3)
# 15 qon tomiri
add(T(640), flow(2.1), 0.55)
for k in range(3): add(T(642) + k * 0.7, heartbeat(), 0.45)
# 16–17 miya, bo'g'ilish
add(T(690), riser(1.6), 0.18); add(T(730), thud(50, 0.8, 0.2), 0.8)
for k in range(5): add(T(734) + k * 0.33 + rng.uniform(0, 0.08), zap(0.18), 0.22)
add(T(730), ring(1.7, 3100), 0.04)
# 18–19 ertalab, bosh og'rig'i: zirqirash
add(T(771), whoosh(0.8, 1100, 0.6), 0.4)
for k in range(3): add(T(801) + k * 0.67, thud(65, 0.5, 0.12), 0.6)
add(T(797), ring(2.0, 3600), 0.05)
# 20 og'iz qurishi
add(T(846), bp(noise(1.0), 1500, 7000) * env(int(SR * 1.0), 0.05, 0.3), 0.3)
# 21 10 soat: soat
for k in range(36): add(T(872) + k * 0.048, tick(3000), 0.35)
add(T(905), beep(1320, 0.1), 0.3)
# 22–23 kaltaklangandek
add(T(913), thud(48, 1.0, 0.25), 0.8); add(T(960), riser(1.7), 0.2)
# 24 zaharlangan miya: pulsatsiya, yurak, qorong'ilik
add(T(1002), thud(45, 1.0, 0.25), 0.9)
for k in range(4): add(T(1006) + k * 0.7, heartbeat(), 0.5)
add(T(1002), ring(DUR - T(1002) - 0.05, 2900), 0.04)
out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
