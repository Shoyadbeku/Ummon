# "Balkondan yiqilgan bola" videosi uchun tovush effektlari (sintez) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/balkon/sfx.py /tmp/claude-0/audio/sfx_balkon.wav
# Yordamchi funksiyalar tirnoq_osishi/sfx.py dan; voqealar kadrlari balkon.py bilan bir xil.
import sys, wave
import numpy as np

SR = 48000; DUR = 34.4
rng = np.random.default_rng(23)
out = np.zeros(int(SR * DUR))
def T(frame): return (frame - 1) / 24.0
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
def bell(f0, d=1.2):
    t = t_(d)
    return (np.sin(2 * np.pi * f0 * t) + 0.35 * np.sin(2 * np.pi * 2.76 * f0 * t) * np.exp(-t / 0.2)) * env(len(t), 0.003, 0.45)

# shahar fon shovqini (butun video), uzoqdagi mashinalar
amb = lp(noise(DUR), 500, 2) * 0.5 + bp(noise(DUR), 800, 3000) * 0.05
out += fade(amb, 0.3, 0.5) * 0.12
for at in (1.0, 6.5, 12.0, 18.5, 26.0, 31.0):
    add(at, fade(lp(noise(3.0), 900) * np.sin(np.pi * t_(3.0) / 3.0) ** 2, 0.1, 0.3), 0.08)
# kaptarlar / qushlar (balkon kadrlarida)
for at in (0.3, 1.1, 1.9):
    t = t_(0.18); f = 2600 + 900 * np.sin(2 * np.pi * 9 * t)
    add(at, np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.01, 0.06), 0.05)
# kesishlardagi yengil "whoosh"lar
CUTS = [37, 73, 111, 163, 221, 247, 275, 331, 381, 426, 472, 531, 595, 671, 733]
for f in CUTS:
    add(T(f) - 0.18, whoosh(0.32, 2500, 0.6), 0.22)
# bola yiqiladi: qiyshayish + shamol (kuchayib boradi)
add(T(66), whoosh(0.9, 1600, 0.55), 0.7)
wd = T(228) - T(72); wn = bp(noise(wd), 250, 2200); tt = t_(wd)
wind = wn * (0.15 + 0.85 * (tt / wd) ** 1.5) * (1 + 0.3 * np.sin(2 * np.pi * 0.7 * tt))
add(T(72), fade(wind, 0.4, 0.08), 0.45)
# ayvonga urilish: past zarba + mato "dung"i
add(T(228), thud(55, 1.0, 0.3), 1.0)
t = t_(0.9); boing = np.sin(2 * np.pi * np.cumsum(150 * np.exp(-t / 0.5) + 80 + 6 * np.sin(2 * np.pi * 11 * t)) / SR) * env(len(t), 0.003, 0.25)
add(T(228) + 0.01, boing, 0.55)
add(T(228), bp(noise(0.25), 300, 3000) * env(int(SR * 0.25), 0.002, 0.06), 0.6)
add(T(247), whoosh(0.7, 1800, 0.35), 0.6)                 # yana havoga
add(T(247), thud(70, 0.5, 0.15), 0.4)
# grafika: "pop" va halqa
for at, f0 in ((T(111) + 0.15, 1320), (T(275) + 0.1, 1500), (T(275) + 0.3, 1100)):
    add(at, bell(f0, 0.5), 0.18)
# kafe: chashka jiringlashi
add(T(348), bell(2400, 0.4), 0.12)
# cho'chish: dramatik zarba
add(T(392), riser(0.5), 0.35); add(T(398), thud(45, 1.4, 0.45), 0.9)
# yugurish qadamlari
f = 428.0
while f < 482:
    add(T(f), thud(95, 0.18, 0.04) + 0.4 * hp(noise(0.18), 2000) * env(int(SR * 0.18), 0.001, 0.02), 0.45)
    f += 8.4
# ushlab olish
add(T(486), thud(70, 0.6, 0.12), 0.75); add(T(484), whoosh(0.4, 1500, 0.8), 0.5)
# alla (musiqa qutisi) — tebratib uxlatish
NOTES = [(0, 1047), (0.45, 1319), (0.9, 1568), (1.35, 1319), (1.8, 1175), (2.25, 1047), (2.7, 988), (3.15, 1047)]
for dt, fr in NOTES:
    add(T(595) + dt, bell(fr, 1.4), 0.13)
# ota-ona: yurish qadamlari
f = 672.0
while f < 732:
    add(T(f), lp(noise(0.12), 1500) * env(int(SR * 0.12), 0.002, 0.03), 0.18)
    f += 14
# politsiya sireni (ikki ohangli), oxirida zarba
sd = DUR - T(728); t = t_(sd)
tone = np.where((t // 0.55) % 2 == 0, 470.0, 625.0)
ph = 2 * np.pi * np.cumsum(tone * (1 + 0.004 * np.sin(2 * np.pi * 6 * t))) / SR
saw = sum(np.sin(k * ph) / k for k in range(1, 10))
siren = lp(saw, 2500) * np.minimum(1, t / 1.2)
add(T(728), fade(siren, 0.1, 0.4), 0.3)
add(T(733), thud(50, 1.2, 0.35), 0.8)

out = out / max(1e-6, np.max(np.abs(out))) * 0.85
w = wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb")
w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((out * 32767).astype(np.int16).tobytes()); w.close()
print("sfx", DUR, "s")
