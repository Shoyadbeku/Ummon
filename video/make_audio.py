"""Ovoz effektlari va fon musiqasini numpy bilan sintez qiladi -> audio/sfx.wav, audio/music.wav"""
import numpy as np, wave, os

SR = 44100
DUR = 29.5
HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(3)
N = int(SR * DUR)


def t_(sec):
    return np.arange(int(SR * sec)) / SR


def lowpass(x, cutoff):
    # bir qutbli oddiy filtr (vaqt bo'yicha o'zgaruvchan cutoff ham bo'lishi mumkin)
    cutoff = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = a[i] * acc + (1 - a[i]) * x[i]
        y[i] = acc
    return y


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def add(buf, sig, at, gain=1.0):
    i = int(at * SR)
    j = min(len(buf), i + len(sig))
    if j > i:
        buf[i:j] += sig[: j - i] * gain


def env(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def whoosh(sec, f0, f1, peak=0.5):
    n = int(SR * sec)
    noise = rng.standard_normal(n)
    cut = np.geomspace(f0, f1, n)
    x = lowpass(noise, cut)
    x = highpass(x, 120)
    tt = np.linspace(0, 1, n)
    shape = np.exp(-((tt - peak) ** 2) / 0.05)
    return x * shape / (np.abs(x).max() + 1e-9)


def car_pass(sec, tc, base=70):
    """mashina o'tib ketishi: doppler bilan motor + shamol"""
    tt = t_(sec)
    rel = tt - tc
    f = base * (1 + 0.18 * -np.tanh(rel * 3))
    ph = 2 * np.pi * np.cumsum(f) / SR
    eng = 0.6 * np.sign(np.sin(ph)) * 0.3 + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3.1 * ph)
    eng = lowpass(eng, 900)
    loud = 1 / (1 + (rel * 2.2) ** 2)
    wind = lowpass(rng.standard_normal(len(tt)), 2500) * 3
    return (eng + wind) * loud


def screech(sec):
    tt = t_(sec)
    f = 2300 + 180 * np.sin(2 * np.pi * 7 * tt) + 300 * rng.standard_normal(len(tt)).cumsum() / SR
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.6 * highpass(rng.standard_normal(len(tt)), 1500)
    return x * env(len(tt), 0.04, 0.35) * 0.5


def thump(f=60, sec=0.35):
    tt = t_(sec)
    return np.sin(2 * np.pi * f * tt * (1 - 0.4 * tt)) * np.exp(-tt * 14)


def chime(f=1318.5, sec=1.4):
    tt = t_(sec)
    x = sum(np.sin(2 * np.pi * f * k * tt) * np.exp(-tt * (3 + 2 * k)) / k for k in (1, 2.01, 3.03))
    return x * env(len(tt), 0.003, 0.1)


def pop(sec=0.25):
    tt = t_(sec)
    f = 300 + 1400 * tt / sec
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 10) * env(len(tt), 0.002, 0.05)


def step():
    n = int(0.09 * SR)
    return lowpass(rng.standard_normal(n), 900) * np.exp(-np.arange(n) / SR * 45) * 2


def bird(sec=0.35):
    tt = t_(sec)
    f = 3200 + 1200 * np.sin(2 * np.pi * 14 * tt)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.02, 0.15) * 0.25


sfx = np.zeros(N)
# fon: shahar shovqini
amb = lowpass(rng.standard_normal(N), 300)
sfx += amb / np.abs(amb).max() * 0.05
for at in (0.8, 2.6, 4.1, 9.3, 11.8, 14.5, 16.1):
    add(sfx, bird(), at, 0.5)

# A: valik "shilq-shilq"
for k in range(10):
    n = int(0.42 * SR)
    sq = lowpass(rng.standard_normal(n), 1800) * np.sin(np.linspace(0, np.pi, n)) ** 2
    add(sfx, sq, 0.2 + k * 0.48, 0.18)
# B: time-lapse whoosh (tepaga)
add(sfx, whoosh(3.4, 300, 6000, 0.7), 5.0, 0.45)
# C: pastga sho'ng'ish
add(sfx, whoosh(3.0, 6000, 400, 0.55), 10.0, 0.45)
add(sfx, chime(), 13.0, 0.35)
add(sfx, chime(1975.5), 13.12, 0.2)
# D: mashinalar to'xtamay o'tib ketadi
add(sfx, car_pass(3.0, 1.5, 65), 17.6, 0.55)
add(sfx, car_pass(3.0, 1.5, 80), 20.3, 0.5)
add(sfx, car_pass(3.0, 1.5, 58), 20.6, 0.45)
# E: haydovchi motori -> ko'zlar "pop" -> tormoz
tt = t_(4.3)
f = 48 + 6 * np.sin(2 * np.pi * 0.7 * tt)
ph = 2 * np.pi * np.cumsum(f) / SR
eng = lowpass(np.sign(np.sin(ph)) * 0.5 + np.sin(2 * ph) * 0.5, 600)
eng *= env(len(tt), 0.3, 1.6)
add(sfx, eng, 23.35, 0.35)
add(sfx, pop(), 26.05, 0.4)
add(sfx, screech(1.6), 26.3, 0.42)
add(sfx, thump(55), 27.85, 0.7)
# F: qadam tovushlari
for k in range(8):
    add(sfx, step(), 28.0 + k * 0.4, 0.35)

sfx /= max(1.0, np.abs(sfx).max() / 0.9)

# ---- fon musiqasi: yengil "qiziqarli" arpejio, 100 bpm
bpm = 100
beat = 60 / bpm
mus = np.zeros(N)
notes = [57, 60, 64, 67, 69, 67, 64, 60,   53, 57, 60, 64, 65, 64, 60, 57,
         55, 59, 62, 67, 71, 67, 62, 59,   52, 56, 59, 64, 68, 64, 59, 56]


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


def pluck(f, sec=0.5):
    tt = t_(sec)
    x = np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt) + 0.1 * np.sin(6 * np.pi * f * tt)
    return x * np.exp(-tt * 7) * env(len(tt), 0.004, 0.05)


k = 0
at = 0.0
while at < DUR:
    add(mus, pluck(midi(notes[k % len(notes)])), at, 0.25)
    if k % 8 == 0:
        root = notes[k % len(notes)] - 24
        tt = t_(beat * 4)
        bass = np.sin(2 * np.pi * midi(root) * tt) * np.exp(-tt * 1.2)
        add(mus, bass, at, 0.35)
    if k % 2 == 0:
        add(mus, thump(50, 0.25), at, 0.25)
    at += beat / 2
    k += 1
mus *= env(N, 0.5, 1.5)
mus /= np.abs(mus).max() / 0.8


def save(name, x):
    x = np.clip(x, -1, 1)
    with wave.open(os.path.join(HERE, "audio", name), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


save("sfx.wav", sfx)
save("music.wav", mus)
print("AUDIO OK")
