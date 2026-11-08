# Chivin videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/chivin/sfx.py /tmp/claude-0/audio/sfx_chivin.wav
import sys, wave
import numpy as np

SR = 48000; DUR = 36.3
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
def whine(d, f0=600, loud=None):                     # chivin g'ing'illashi (ingichka, baland)
    t = t_(d)
    f = f0 * (1 + 0.035 * np.sin(2 * np.pi * 2.3 * t) + 0.02 * np.sin(2 * np.pi * 5.7 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum(np.sin(k * ph) / k ** 1.3 for k in range(1, 9))
    x = bp(x, 400, 7000) * (0.8 + 0.2 * np.sin(2 * np.pi * 11 * t))
    if loud is not None: x *= np.interp(t, np.linspace(0, d, len(loud)), loud)
    return fade(x, 0.03, 0.06)
def tick(f0=2400, d=0.06):
    t = t_(d); return (np.sin(2 * np.pi * f0 * t) * 0.6 + bp(noise(d), 1500, 8000) * 0.4) * env(len(t), 0.0005, 0.015)
def ting(f0=3200, d=1.0):
    t = t_(d); return sum(np.sin(2 * np.pi * f0 * k * t) / k for k in (1, 2.76, 5.4)) * env(len(t), 0.002, 0.35) * 0.4
def rasp(d, rate=24 / 7):                            # arra: oldinga-orqaga
    t = t_(d); n = bp(noise(d), 900, 6000)
    return n * (0.25 + 0.75 * np.abs(np.sin(np.pi * rate * t)) ** 2)
def gurgle(d, rate=9.0):
    out_ = np.zeros(int(SR * d))
    for k in range(int(d * rate)):
        s = squelch(0.12, rng.uniform(250, 700)); i = int((k / rate + rng.uniform(0, 0.05)) * SR)
        j = min(len(out_), i + len(s)); out_[i:j] += s[: j - i] * rng.uniform(0.5, 1)
    return out_
def scratch_snd(d, rate=6.5):
    t = t_(d); n = bp(noise(d), 1800, 9000)
    return n * np.abs(np.sin(np.pi * rate * t)) ** 3

tt = np.arange(len(out)) / SR
# fon: past drone, oxirida kuchayadi
drone = sum(np.sin(2 * np.pi * f * tt) for f in (55, 65.4, 82.4)) / 3 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.1 * tt))
out += drone * (0.025 + 0.03 * np.clip((tt - 20) / 14, 0, 1))
# vushlar (kesishlarda)
for f in (22, 43, 87, 137, 200, 264, 334, 407, 514, 573, 619, 648, 716, 797, 831):
    add(T(f) - 0.4, whoosh(0.5, 1700, 0.8), 0.2)
# 1-2: chivin g'ing'illashi (hook, xonaga uchib kiradi)
add(0.0, whine(T(22), 640, [0.6, 0.9, 0.5]), 0.16)
add(T(22), whine(T(43) - T(22), 600, [0.5, 1.0, 0.8]), 0.22)
# 3: crash zoom + teshish
add(T(60), thud(55, 0.9, 0.3), 0.55); add(T(60) - 0.15, whoosh(0.25, 3000, 0.8), 0.3); add(T(62), squelch(0.2, 500), 0.2)
# 4: 6 ta igna — 6 ta "tik"
for k in range(6): add(T(92) + k * 0.13, tick(2000 + 180 * k), 0.25)
add(T(92), riser(T(137) - T(92)), 0.08)
# 5: labium bukiladi (rezina g'ichirlashi)
t = t_(T(199) - T(137)); add(T(137), bp(noise(len(t) / SR), 120, 600) * (0.3 + 0.7 * np.sin(np.pi * t / t[-1])) * 0.6, 0.18)
# 6: stiletlar chiqadi — yaltirash
add(T(212), ting(3200), 0.25); add(T(228), ting(4100, 0.8), 0.18)
# 7: arra
add(T(266), fade(rasp(T(334) - T(266)), 0.05, 0.1), 0.2)
# 8: yara ochiladi (ho'l yirtilish)
for k in range(5): add(T(336) + k * 0.12, squelch(0.25, 300 + 50 * k), 0.17)
# 9: qidirish (mayda chuv-chuv)
for k in range(7): add(T(410) + k * 0.36, squelch(0.15, 450 + 30 * (k % 3)), 0.12)
# 10: qon tomiriga kiradi: crash zoom zarbasi
add(T(486), thud(48, 1.3, 0.45), 0.8); add(T(486) - 0.15, whoosh(0.3, 3500, 0.8), 0.35); add(T(487), squelch(0.3, 380), 0.3)
# 11: so'lak purkaladi
add(T(520), fade(gurgle(T(573) - T(520), 10), 0.05, 0.1), 0.18)
# 12: qon tomiri ichi: yurak urishi + oqim
for k in range(3): add(T(573) + k * 0.65, heartbeat(), 0.45)
add(T(573), fade(lp(noise(T(619) - T(573)), 300) * 4, 0.05, 0.15), 0.12)
# 14: qorni to'ladi (so'rish)
add(T(650), fade(gurgle(T(716) - T(650), 6), 0.05, 0.1), 0.13)
t = t_(T(716) - T(650)); add(T(650), np.sin(2 * np.pi * np.cumsum(90 + 120 * t / t[-1]) / SR) * 0.3 * t / t[-1], 0.2)
# 15: chivin kameraga uchib keladi
add(T(724), whine(T(769) - T(724), 560, [0.1, 0.3, 1.0, 1.0]), 0.3)
# 16: do'mboq: crash zoom
add(T(774), thud(60, 1.0, 0.35), 0.6); add(T(774) - 0.15, whoosh(0.3, 3000, 0.8), 0.3)
# 17: immun hujayralar — pufakchalar yorilishi
for k in range(10): add(T(812) + k * 0.07 + rng.uniform(0, 0.03), tick(900 + 90 * k, 0.05), 0.2)
# 18: qashinish + yakuniy zarba
add(T(833), fade(scratch_snd(T(871) - T(833)), 0.03, 0.05), 0.22)
add(T(866), thud(42, 1.6, 0.6), 0.9)

out = out / max(1e-9, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", round(len(out) / SR, 2), "s")
