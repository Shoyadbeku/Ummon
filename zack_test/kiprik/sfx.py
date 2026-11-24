# "Nafas yo'lidagi kiprikchalar" videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/kiprik/sfx.py /tmp/claude-0/audio/sfx_kiprik.wav
import sys, wave
import numpy as np

SR = 48000; DUR = 41.62
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

tt = np.arange(len(out)) / SR
drone = sum(np.sin(2 * np.pi * f * tt) for f in (49, 58.3, 73.4)) / 3 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.12 * tt))
out += drone * (0.02 + 0.02 * np.clip((tt - 18) / 15, 0, 1))
CUTS = [37, 104, 188, 249, 310, 389, 452, 486, 524, 573, 626, 651, 683, 780, 817, 872, 896, 963]
for f in CUTS: add(T(f) - 0.35, whoosh(0.5, 1600, 0.75), 0.2)
# ilgak: tunnel ichida shamol + zarba
add(T(1), thud(50, 1.0, 0.35), 0.6); add(T(1), wind(1.6) * fade(np.ones(int(SR * 1.6)), 0.05, 0.4), 0.25)
# ko'cha: shahar shovqini
add(T(37), fade(traffic(T(104) - T(37)), 0.1, 0.3), 0.18)
add(T(452), fade(traffic(T(486) - T(452)), 0.05, 0.2), 0.14)
# rentgen: yurak urishi + "konveyer" g'uvillashi
for k in range(6): add(T(106) + k * 0.7, heartbeat(), 0.3)
add(T(188), riser(T(249) - T(188)), 0.16)
# kiprikchalar: shitirlash; sho'ng'ish zarbasi
add(T(249), thud(55, 0.9, 0.3), 0.45)
add(T(249), fade(beat_texture(T(573) - T(249)), 0.2, 0.3), 0.08)
for k in range(10): add(T(392 + k * 6), squelch(0.2, 260 + 15 * k), 0.06)
# sigaret: chirsillash va puflash
add(T(458), inhale(0.75), 0.4); add(T(474), exhale(1.0), 0.3)
# tutun tunnelga bostirib kiradi
add(T(486), whoosh(1.4, 900, 0.4), 0.45); add(T(486), wind(1.5) * fade(np.ones(int(SR * 1.5)), 0.05, 0.5), 0.3)
# zaharli molekulalar: mayda "tink"lar
for k in range(14): add(T(528) + k * 0.13, tick(1400 + 90 * k) * 0.8, 0.1)
# falaj: sekinlashuvchi shitirlash, zarba
add(T(573), fade(beat_texture(T(605) - T(573), 3.0), 0.05, 0.6), 0.07)
add(T(605), thud(44, 1.6, 0.55), 0.8); add(T(605) - 0.12, whoosh(0.25, 3500, 0.8), 0.3)
# soat: tez tiqillash
add(T(626), clock_ticks(T(651) - T(626), 22), 0.13)
# qotgan kiprikchalar: sukunat, past drone
add(T(651), thud(40, 1.2, 0.6), 0.3)
# qatron: yopishqoq tomchilar
for k in range(12): add(T(690 + k * 7), squelch(0.25, 180 + 10 * k), 0.1)
# o'pkada qora dog'lar
add(T(780), thud(46, 1.4, 0.5), 0.5)
# ertalab: qushlar o'rniga yengil akkord, keyin yo'tal
t = t_(1.6); add(T(817), sum(np.sin(2 * np.pi * f * t) for f in (261.6, 329.6, 392.0)) / 3 * env(len(t), 0.3, 0.8), 0.08)
for cf in (849, 860, 878, 890): add(T(cf), cough(0.45), 0.45)
add(T(876), thud(50, 0.8, 0.25), 0.4)
# rentgen yo'tal: har zarbada bum
for cf in (902, 918, 934, 950): add(T(cf), thud(48, 0.9, 0.3), 0.55); add(T(cf), cough(0.35), 0.25)
# yakun: qora bo'lak otiladi
add(T(963), riser(T(995) - T(963)), 0.2)
add(T(995), thud(42, 1.2, 0.5), 0.8); add(T(994), whoosh(0.3, 3000, 0.7), 0.35)
out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
