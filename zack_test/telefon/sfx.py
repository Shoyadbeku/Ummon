# "Bir ko'z bilan telefon" videosi uchun tovush effektlari (sintez, litsenziya muammosi yo'q) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: python3 -I zack_test/telefon/sfx.py /tmp/claude-0/audio/sfx_telefon.wav  (yordamchilar chotka/sfx.py dan)
# Yordamchi funksiyalar quloq/sfx.py (aksirish/sfx.py) dan.
import sys, wave
import numpy as np

SR = 48000; DUR = 41.42
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
def click(d=0.06, f=2500):
    return bp(noise(d), f * 0.5, f * 2) * env(int(SR * d), 0.0005, 0.008)
def zap(d=0.6, f0=2400, f1=300):                     # lazer
    t = t_(d); f = f0 + (f1 - f0) * (t / d) ** 0.5
    return (np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.3 + 0.5 * bp(noise(d), 1500, 7000)) * env(len(t), 0.002, d / 2.5)
def drone(d, f=55):
    t = t_(d); x = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t + 0.3) + 0.25 * np.sin(2 * np.pi * f * 2.01 * t)
    return fade(lp(x + 0.2 * noise(d), 600) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.3 * t)), 0.4, 0.6)
def crackle(d, dens=60):                             # elektr chirsillashi
    x = np.zeros(int(SR * d))
    for _ in range(int(d * dens)):
        i = rng.integers(0, len(x) - 2000); c = click(0.02, rng.uniform(1500, 6000)); x[i:i + len(c)] += c * rng.uniform(0.3, 1)
    return x
def hum(d, f=120):
    t = t_(d); return fade(bp(np.sign(np.sin(2 * np.pi * f * t)) + 0.3 * noise(d), 100, 3000) * 0.25, 0.1, 0.2)

# ---- kadrlar (telefon.py dagi bilan bir xil) ----
SH = dict(hook=1, wide=37, face=75, ots=127, xoff=192, pupil=248, maxpup=335, beam=383, cut=464, retina=522,
          xcalm=620, xburn=694, clash=747, off=801, pov=883, end=947)
F_LAMP, F_DARK, F_MAXP, F_LASER, F_HIT, F_CLASH, F_OFF, F_15 = 14, 231, 335, 567, 605, 766, 818, 898
# tungi xona foni (shahar shovqini + past g'uvillash) xona kadrlarida
for a, b in ((1, 191), (383, 463), (801, 994)):
    add(T(a), fade(lp(noise((b - a) / 24), 300) * 0.05 + drone((b - a) / 24, 48) * 0.05, 0.1, 0.3))
add(T(F_LAMP) - 0.02, click(0.05, 1800), 0.9); add(T(F_LAMP), thud(90, 0.4, 0.08), 0.35)    # lampa o'chirgichi
for f in range(1, 800, 29):                                                              # barmoq bilan surish
    if f < 191 or 383 <= f < 463: add(T(f), bp(noise(0.12), 2000, 8000) * env(int(SR * 0.12), 0.01, 0.04), 0.12)
add(T(SH["wide"]) - 0.25, whoosh(0.5, 1800), 0.35)
add(T(SH["face"]) - 0.2, whoosh(0.4, 1200), 0.25)
add(T(SH["ots"]) - 0.2, whoosh(0.4, 1400), 0.25)
# rentgen
add(T(SH["xoff"]) - 0.6, riser(0.6), 0.5); add(T(SH["xoff"]), thud(60, 0.7, 0.2), 0.7); add(T(SH["xoff"]), hum((248 - 192) / 24, 100), 0.4)
add(T(F_DARK), thud(42, 1.0, 0.35), 1.0); add(T(F_DARK), bp(noise(0.5), 100, 900) * env(int(SR * 0.5), 0.002, 0.15), 0.4)
# makro ko'z: past dron, yurak urishi; "maksimal" — crash zoom
add(T(SH["pupil"]), drone((383 - 248) / 24, 41), 0.35)
for k in range(3): add(T(SH["pupil"]) + 0.6 + k * 1.1, heartbeat(), 0.45)
add(T(F_MAXP) - 0.35, whoosh(0.4, 2400), 0.6); add(T(F_MAXP), thud(55, 0.8, 0.22), 0.9)
# ko'k nur: elektr g'uvillash va o'sib boruvchi tovush
add(T(SH["beam"]), hum((464 - 383) / 24, 240), 0.35); add(T(464) - 2.0, riser(2.0), 0.5)
add(T(SH["cut"]) - 0.3, whoosh(0.5, 3000), 0.7); add(T(SH["cut"]), thud(70, 0.5, 0.12), 0.5)
add(T(SH["cut"]) + 1.1, zap(0.5, 3000, 900), 0.35)
# to'r parda: dron -> lazer -> zarba
add(T(SH["retina"]), drone((620 - 522) / 24, 36), 0.4)
add(T(F_LASER), zap(0.8), 0.6); add(T(F_LASER), hum((F_HIT - F_LASER) / 24 + 0.6, 180), 0.35)
add(T(F_HIT) - 0.5, riser(0.5), 0.5); add(T(F_HIT), thud(38, 1.4, 0.45), 1.1); add(T(F_HIT), crackle(0.8, 80), 0.6)
# moslashgan ko'z (tinch), kuygan ko'z (chirsillash), signal chalkashuvi
add(T(SH["xcalm"]) - 0.25, whoosh(0.5, 1500), 0.5); add(T(SH["xcalm"]), drone((694 - 620) / 24, 65), 0.25)
add(T(SH["xburn"]) - 0.15, whoosh(0.25, 3500), 0.8); add(T(SH["xburn"]), crackle((747 - 694) / 24, 40), 0.35)
add(T(SH["clash"]), crackle((801 - 747) / 24, 120), 0.45); add(T(F_CLASH), thud(45, 0.9, 0.3), 1.0)
for k in range(5): add(T(F_CLASH) + 0.3 + k * 0.33, zap(0.18, rng.uniform(1500, 3500), 400), 0.3)
# telefon o'chadi: chiq + bass tushishi
add(T(F_OFF), click(0.04, 3000), 1.0); add(T(F_OFF) + 0.02, thud(35, 1.6, 0.6), 0.8)
# POV: soat chiqillashi (tezlashgan "15 daqiqa"), past ohang; final dron so'nadi
for k in range(int((T(994) - T(SH["pov"])) / 0.25)): add(T(SH["pov"]) + k * 0.25, click(0.03, 4000 if k % 2 else 3200), 0.35)
add(T(F_15), thud(50, 2.0, 0.8), 0.6); add(T(SH["end"]), drone((994 - 947) / 24, 33), 0.35)

out = out / max(1e-6, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
print("sfx", DUR, "s")
