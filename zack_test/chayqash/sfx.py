# "Og'iz chayqash suyuqligi" videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/chayqash/sfx.py /tmp/claude-0/audio/sfx_chayqash.wav
import sys, wave
import numpy as np

SR = 48000; DUR = 31.67
rng = np.random.default_rng(9)
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
def sneeze():                                         # "a-a-apchxi!": nafas olish + keskin shovqin
    a = bp(noise(0.45), 500, 3000) * np.linspace(0, 1, int(SR * 0.45)) ** 2 * 0.25
    b = bp(noise(0.35), 900, 7000) * env(int(SR * 0.35), 0.003, 0.08)
    return np.concatenate([a, b])
def creak(d=0.6):                                     # shtanga temiri g'ichirlashi
    t = t_(d); f = 90 + 30 * np.sin(2 * np.pi * 1.5 * t)
    return bp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5 + 0.5 * noise(d), 200, 2500) * env(len(t), 0.05, d / 2)
def pop():                                            # tomir yorilishi: ho'l "pat"
    return thud(140, 0.3, 0.04) * 0.6 + bp(noise(0.3), 400, 4000) * env(int(SR * 0.3), 0.001, 0.03)
def tick(f0=2200):
    t = t_(0.05); return np.sin(2 * np.pi * f0 * t) * env(len(t), 0.0005, 0.01)
def clock_ticks(d, rate=8):
    x = np.zeros(int(SR * d))
    for k in range(int(d * rate)):
        y = tick(1800 if k % 2 else 2400); i = int(k / rate * SR); x[i:i + len(y)] += y[: len(x) - i]
    return x


def cough(d=0.5):                                     # og'ir yo'tal: keskin portlash + xirillash
    a = bp(noise(0.12), 200, 2500) * env(int(SR * 0.12), 0.002, 0.05)
    b = bp(noise(d), 150, 1800) * env(int(SR * d), 0.01, d / 3) * 0.6
    return np.concatenate([a, b]) + 0.0
def inhale(d=0.8):                                    # sigaret tortish: shivirlovchi nafas + chirsillash
    t = t_(d); x = bp(noise(d), 600, 5000) * np.sin(np.pi * t / d) ** 2 * 0.4
    for k in range(25):
        i = rng.integers(0, len(x) - 400); x[i:i + 300] += bp(noise(300 / SR), 2000, 9000) * env(300, 0.0002, 0.002) * 0.8
    return x
def exhale(d=1.0):
    t = t_(d); return bp(noise(d), 300, 2500) * np.minimum(1, t / 0.08) * np.exp(-t / 0.5) * 0.5
def beat_texture(d, rate=6.0):                        # kiprikchalarning mayda "shitirlashi"
    x = np.zeros(int(SR * d))
    for k in range(int(d * rate * 3)):
        i = int(rng.uniform(0, d) * SR); y = bp(noise(0.03), 1500, 6000) * env(int(SR * 0.03), 0.001, 0.008)
        x[i:i + len(y)] += y[: len(x) - i]
    return x
def wind(d):
    t = t_(d); return lp(noise(d), 500) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * t))
def traffic(d):
    t = t_(d); return lp(noise(d), 220) * 0.8 + bp(noise(d), 400, 900) * 0.2 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.2 * t))


def glug(n=4, d=0.12):                                # suyuqlik qultillashi
    x = np.concatenate([np.zeros(int(SR * 0.05))] + [np.concatenate([squelch(d, 180 + 40 * k) * 0.8, np.zeros(int(SR * 0.08))]) for k in range(n)])
    return x
def fizz(d):                                          # ko'pirish: mayda pufakchalar chirsillashi
    x = bp(noise(d), 3000, 12000) * 0.15
    for k in range(int(d * 120)):
        i = int(rng.uniform(0, d) * SR); y = bp(noise(0.01), 2500, 10000) * env(int(SR * 0.01), 0.0002, 0.002)
        x[i:i + len(y)] += y[: len(x) - i]
    return fade(x, 0.05, 0.2)
def breath(d=1.6, gain=1.0):                          # og'ir, sekin nafas
    t = t_(d); return bp(noise(d), 250, 1800) * np.sin(np.pi * t / d) ** 2 * 0.5 * gain

tt = np.arange(len(out)) / SR
drone = sum(np.sin(2 * np.pi * f * tt) for f in (49, 58.3, 73.4)) / 3 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.12 * tt))
out += drone * (0.02 + 0.03 * np.clip((tt - 14) / 15, 0, 1))
CUTS = [37, 88, 141, 190, 284, 347, 418, 463, 514, 588, 681]
for f in CUTS: add(T(f) - 0.3, whoosh(0.45, 1700, 0.75), 0.22)
# hook: shisha "tink" + zarba
add(T(1), thud(55, 0.9, 0.3), 0.5); add(T(3), tick(3200) * 2, 0.15)
# ichish: qultillash
add(T(66), glug(4), 0.45)
# rentgen: yutish, yurak urishi
add(T(88), squelch(0.35, 220), 0.35)
for k in range(3): add(T(92) + k * 0.7, heartbeat(), 0.28)
# oshqozon: yashil to'lqin + ko'pirish
add(T(141), whoosh(1.2, 700, 0.35), 0.45); add(T(150), fizz(T(190) - T(150)), 0.5)
# bakteriyalar: to'lqin, "pop"lar
add(T(190), fade(wind(T(284) - T(190)), 0.2, 0.3), 0.1)
for k in range(16): add(T(205) + k * 0.22, pop() * 0.5, 0.12)
add(T(220), fizz(2.5), 0.25)
# molekulalar: kristall "tink"lar
for k in range(10): add(T(290) + k * 0.24, tick(1500 + 120 * k), 0.12)
# ko'ngil aynishi: past drone, yurak; qorin og'rig'i zarbasi
add(T(347), riser(T(418) - T(347)) * 0.6, 0.15)
for k in range(4): add(T(352) + k * 0.75, heartbeat(), 0.25)
add(T(418), thud(46, 1.2, 0.4), 0.7)
# bola: sukunat, shisha surilishi
add(T(495), squelch(0.15, 900), 0.12)
# bola rentgen: ogohlantiruvchi yurak urishi (tez)
for k in range(5): add(T(516) + k * 0.5, heartbeat(), 0.35)
add(T(514), thud(44, 1.0, 0.4), 0.5)
# qon tomiri: oqim + og'ir yurak
add(T(588), fade(lp(noise(T(681) - T(588)), 300), 0.2, 0.3), 0.25)
for k in range(5): add(T(592) + k * 0.85, heartbeat(), 0.4)
# polda: sekinlashgan nafas va yurak, oxirida zarba
add(T(681), thud(40, 1.4, 0.6), 0.6)
for k, g in enumerate((1.0, 0.75, 0.5)): add(T(690) + k * 1.0, breath(0.9, g), 0.25)
for k in range(3): add(T(684) + k * 1.1, heartbeat(), 0.3 - 0.07 * k)
out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
