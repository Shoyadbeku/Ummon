# "Tirnoq ostidagi qon" videosi uchun tovush effektlari (sintez) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/tirnoq/sfx.py /tmp/claude-0/audio/sfx_tirnoq.wav
# Yordamchi funksiyalar yelim/sfx.py dan.
import sys, wave
import numpy as np

SR = 48000; DUR = 41.2
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

def click(f0=3500):                                   # magnitlar "chiq" etib yopishadi
    t = t_(0.08); return (np.sin(2 * np.pi * f0 * t) + 0.5 * np.sin(2 * np.pi * f0 * 1.7 * t)) * env(len(t), 0.0005, 0.012) + hp(noise(0.08), 3000) * env(len(t), 0.0005, 0.004)
def gulp():
    t = t_(0.35); f = 260 - 140 * t / 0.35
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.02, 0.12) + 0.4 * squelch(0.35, 300)
def rumble(d):
    t = t_(d); x = lp(noise(d), 90, 2); return x / (np.abs(x).max() + 1e-9) * np.minimum(1, t / 0.4)
def pad(d, freqs=(220, 277, 330, 415), trem=0.3):     # tush: yumshoq akkord
    t = t_(d); x = sum(np.sin(2 * np.pi * f * t + k) for k, f in enumerate(freqs)) / len(freqs)
    return fade(x * (1 - trem + trem * np.sin(2 * np.pi * 0.7 * t)), 0.4, 0.6)
def glitch_snd(d=1.0):
    x = np.zeros(int(SR * d)); n = int(SR * 0.03)
    for k in range(int(d / 0.03)):
        if rng.random() < 0.55: x[k * n:(k + 1) * n] = np.sign(np.sin(2 * np.pi * rng.uniform(200, 3000) * t_(0.03))) * rng.uniform(0.2, 0.8)
    return bp(x, 300, 8000)

def power_down(d=2.6):
    t = t_(d); f = 520 * np.exp(-t / (d / 2.5)) + 40
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * fade(np.ones(len(t)), 0.02, 0.4) * 0.6
def twitch_snd():                                    # qovoq "tit" etib uchishi
    return mixs(click(rng.uniform(2200, 3200)) * 0.6, squelch(0.08, 900) * 0.5)
def sip():                                            # kofe ho'plash
    return mixs(bp(noise(0.5), 1500, 7000) * env(int(SR * 0.5), 0.05, 0.2) * 0.5, gulp() * 0.7)
def yawn_snd(d=1.6):
    t = t_(d); f = 260 + 80 * np.sin(np.pi * t / d)
    x = bp(noise(d), 300, 2500) * 0.4 + 0.25 * np.sin(2 * np.pi * np.cumsum(f) / SR)
    return x * np.sin(np.pi * t / d) ** 2
def typing(d):
    x = np.zeros(int(SR * d))
    for k in range(int(d * 7)):
        i = int(rng.uniform(0, d - 0.06) * SR); c = click(rng.uniform(1500, 2600)) * rng.uniform(0.2, 0.5)
        x[i:i + len(c)] += c[: len(x) - i]
    return lp(x, 5000)

def rip(d=0.5):                                       # yopishqoq narsa uzilishi (teri/kiprik)
    t = t_(d); x = crackle(d) * 0.9 + bp(noise(d), 500, 4000) * 0.6 * np.exp(-t / (d / 3))
    return x * np.minimum(1, t / 0.01)
def trickle(d):                                       # suyuqlik oqishi
    x = bubbles(d) * 0.6 + bp(noise(d), 1500, 6000) * 0.15
    return fade(x, 0.2, 0.3)
def chime(f0=1046):
    t = t_(1.6); return sum(np.sin(2 * np.pi * f0 * k * t) / k for k in (1, 2, 3)) * env(len(t), 0.003, 0.5) * 0.4

def slam(d=1.0):                                      # eshik qarsillashi
    return mixs(thud(48, d, 0.22), 0.6 * bp(noise(0.15), 200, 3000) * env(int(SR * 0.15), 0.001, 0.03), 0.3 * creak(0.25, 300))
def sizzle(d):                                        # cho'g' tirnoqqa tegishi: "chirs"
    t = t_(d); x = bp(noise(d), 2500, 11000) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 13 * t)))
    return fade(x + 0.4 * crackle(d), 0.02, 0.25)
def flame_snd(d):                                     # gorelka "vuuuf"
    t = t_(d); return fade(bp(noise(d), 120, 1500) * (0.8 + 0.2 * np.sin(2 * np.pi * 5 * t)), 0.15, 0.2)
def spurt(d=0.8):                                     # qon otilishi "psh-shlop"
    t = t_(d); return mixs(squelch(0.35, 260), 0.8 * splash(d) * np.exp(-t / 0.3))

# ---------------- voqealar (kadrlar: STORYBOARD.md) ----------------
SH = [1, 53, 91, 173, 216, 276, 334, 433, 501, 576, 621, 680, 728, 816, 873, 931]
for f in SH[1:]:                                       # kesishlarda whoosh
    add(T(f) - 0.25, whoosh(0.45, 2200, 0.55), 0.3)
for f in (276, 621, 873): add(T(f), thud(60, 0.6, 0.15), 0.5)   # kesim kadrlariga kirish
add(0.0, rumble(41.2) * 0.15, 0.18)
# 1 eshik: yopilish shamoli, qarsillash, quloq shang'illashi
add(T(18), whoosh(0.8, 900, 0.85), 0.5); add(T(40), slam(1.0), 1.0); add(T(40), ring(2.0, 3100), 0.12)
# 2 bolg'a: ko'tarilish, zarba
add(T(66), whoosh(0.5, 1600, 0.8), 0.45); add(T(78), thud(70, 0.5, 0.08), 1.0); add(T(78), click(1800), 0.5)
add(T(78), squelch(0.3, 300), 0.35)
# 3-5 qon yig'iladi, yurak urishi (og'riq to'lqini)
add(T(91), riser(T(170) - T(91)) * 0.6, 0.2)
for f in (96, 115, 134, 153, 180, 199, 222, 242, 262): add(T(f), heartbeat(), 0.75)
for f in (222, 242, 262): add(T(f + 8), zap(0.4), 0.3)
# 6-7 kesim: bosim, asablar "elektr"
add(T(334), riser(T(425) - T(334)) * 0.5, 0.25)
for f in range(354, 430, 14): add(T(f + 2), zap(0.25), 0.25); add(T(f + 2), heartbeat() * 0.5, 0.4)
# 8-9 klinika, gorelka, qizish
add(T(433), flame_snd(T(575) - T(433)), 0.35); add(T(505), riser(T(570) - T(505)), 0.2); add(T(540), crackle(1.2), 0.15)
# 10 tegish
add(T(576), whoosh(0.6, 1200, 0.8), 0.35); add(T(611), sizzle(0.6), 0.7); add(T(611), thud(80, 0.3, 0.05), 0.5)
# 11-12 asab yo'q: tinch akkord
add(T(625), pad(4.2, (262, 330, 392)), 0.22); add(T(690), chime(1046), 0.2)
# 13 eritib teshadi
add(T(728), sizzle(T(815) - T(728)), 0.6); add(T(793), thud(55, 0.6, 0.12), 0.8); add(T(793), crackle(0.8), 0.3)
# 14 favvora
add(T(818), squelch(0.3, 400), 0.4); add(T(826), spurt(1.0), 1.0); add(T(834), trickle(1.4), 0.4)
for k in range(10): add(T(840 + rng.integers(0, 30)), drip(rng.uniform(600, 1300)) * 0.5, 0.35)
# 15-16 bosim tushadi: yengillik
add(T(873), hiss(1.4), 0.4); add(T(873), pad(4.0, (330, 415, 494)), 0.2); add(T(931), pad(2.4, (262, 330, 392, 523)), 0.25)
add(T(940), chime(1318), 0.3); add(40.85, thud(45, 0.4, 0.2), 0.6)

out = np.tanh(out * 1.2) * 0.8
pcm = (np.clip(out, -1, 1) * 32767).astype(np.int16)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("ok", sys.argv[1], len(out) / SR)
