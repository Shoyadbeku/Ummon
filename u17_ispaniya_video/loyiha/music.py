"""Original underscore + SFX, synthesized from scratch (no third-party audio). Output: build/music.wav, build/sfx.wav"""
import numpy as np, wave
from scipy.signal import butter, sosfilt

SR = 48000
DUR = 310.51
N = int(DUR * SR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)
BPM = 92.0
BEAT = 60 / BPM

def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)
def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)
def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)

def saw(f, tt):
    return 2 * ((f * tt) % 1.0) - 1

def nf(m):  # midi -> Hz
    return 440 * 2 ** ((m - 69) / 12)

# ---- section intensity curves (0..1) for each layer
SECT = [  # (start, end, pad, pulse, kick, hat, pluck, bass, mode)
    (0.0, 9.25, 1.0, 1.0, 1.0, 0.8, 0.0, 1.0, "minor"),
    (9.25, 10.30, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, "minor"),
    (10.30, 13.30, 0.9, 1.0, 1.0, 0.6, 0.0, 1.0, "minor"),
    (13.30, 34.0, 0.7, 0.6, 0.35, 0.35, 0.0, 0.6, "minor"),
    (34.0, 116.6, 0.6, 0.7, 0.55, 0.5, 0.0, 0.7, "minor"),
    (116.6, 151.8, 0.75, 0.85, 0.5, 0.3, 0.0, 0.85, "dark"),
    (151.8, 208.7, 0.65, 0.0, 0.0, 0.0, 0.8, 0.35, "minor"),
    (208.7, 282.3, 0.6, 0.7, 0.55, 0.5, 0.25, 0.7, "minor"),
    (282.3, 308.3, 0.9, 0.9, 0.85, 0.6, 0.4, 1.0, "major"),
    (308.3, DUR, 0.7, 0.0, 0.0, 0.0, 0.0, 0.5, "major"),
]

def curve(idx):
    c = np.zeros(N)
    for s in SECT:
        a, b = int(s[0] * SR), int(s[1] * SR)
        c[a:b] = s[idx]
    k = int(0.35 * SR)  # smooth transitions
    ker = np.ones(k) / k
    return np.convolve(c, ker, mode="same")

PROG = {
    "minor": [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]],   # Am F C G
    "dark":  [[57, 60, 64], [58, 62, 65], [57, 60, 64], [52, 56, 59]],   # Am Bb Am E
    "major": [[48, 52, 55], [55, 59, 62], [57, 60, 64], [53, 57, 60]],   # C G Am F
}
def mode_at(sec):
    for s in SECT:
        if s[0] <= sec < s[1]:
            return s[8]
    return "minor"

BAR = BEAT * 4
CH = BAR * 2  # chord length
nch = int(np.ceil(DUR / CH))

pad = np.zeros(N); bass = np.zeros(N); pulse = np.zeros(N); pluck = np.zeros(N)
for ci in range(nch):
    t0 = ci * CH
    a, b = int(t0 * SR), min(N, int((t0 + CH) * SR) + int(0.3 * SR))
    if a >= N:
        break
    tt = t[a:b] - t0
    mode = mode_at(t0 + 0.01)
    chord = PROG[mode][ci % 4]
    env = np.minimum(1, tt / 0.6) * np.minimum(1, np.maximum(0, (CH + 0.3 - tt) / 0.5))
    seg = np.zeros(b - a)
    for m in chord:
        for det in (-0.12, 0.0, 0.11):
            seg += saw(nf(m) * 2 ** (det / 12), tt + rng.random())
    pad[a:b] += seg * env / 9
    r = nf(chord[0] - 24)
    bass[a:b] += (np.sin(2 * np.pi * r * tt) + 0.3 * np.sin(2 * np.pi * 2 * r * tt)) * env
    # 8th-note pulse on root + fifth
    for k in range(16):
        s0 = t0 + k * BEAT / 2
        ia, ib = int(s0 * SR), min(N, int((s0 + 0.22) * SR))
        if ia >= N:
            break
        u = t[ia:ib] - s0
        m = chord[0] - 12 if k % 4 != 3 else chord[2] - 12
        pulse[ia:ib] += saw(nf(m), u) * np.exp(-u * 16)
    # pluck arpeggio (8ths)
    arp = [chord[0] + 12, chord[1] + 12, chord[2] + 12, chord[1] + 12]
    for k in range(16):
        s0 = t0 + k * BEAT / 2
        ia, ib = int(s0 * SR), min(N, int((s0 + 0.9) * SR))
        if ia >= N:
            break
        u = t[ia:ib] - s0
        f = nf(arp[k % 4])
        pluck[ia:ib] += (np.sin(2 * np.pi * f * u) + 0.35 * np.sin(4 * np.pi * f * u)) * np.exp(-u * 5.5)

pad = lp(pad, 1500); pulse = lp(pulse, 900)
kick = np.zeros(N); hat = np.zeros(N)
nb = int(DUR / BEAT) + 1
for k in range(nb):
    s0 = k * BEAT
    ia, ib = int(s0 * SR), min(N, int((s0 + 0.35) * SR))
    if ia >= N:
        break
    u = t[ia:ib] - s0
    f = 45 + 85 * np.exp(-u * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    kick[ia:ib] += np.sin(ph) * np.exp(-u * 9)
    for hh in (0.5,):
        s1 = s0 + hh * BEAT
        ja, jb = int(s1 * SR), min(N, int((s1 + 0.06) * SR))
        if ja < N:
            hat[ja:jb] += rng.standard_normal(jb - ja) * np.exp(-(t[ja:jb] - s1) * 70)
hat = hp(hat, 7000)

mix = (pad * 0.55 * curve(2) + pulse * 0.30 * curve(3) + kick * 0.85 * curve(4) + hat * 0.12 * curve(5)
       + pluck * 0.22 * curve(6) + bass * 0.45 * curve(7))
mix = np.tanh(mix * 1.1)

# stereo widening: slight delay on pad
L = mix + 0.15 * np.roll(pad * curve(2), int(0.011 * SR))
R = mix + 0.15 * np.roll(pad * curve(2), int(0.017 * SR))
fadeout = np.clip((DUR - t) / 2.2, 0, 1)
L *= fadeout; R *= fadeout
st = np.stack([L, R], 1)
st /= np.max(np.abs(st)) / 0.89

# ---------------- SFX
sfx = np.zeros(N)
def add(arr, s0, sig):
    ia = int(s0 * SR); ib = min(N, ia + len(sig))
    if ia < N:
        arr[ia:ib] += sig[: ib - ia]

def impact(strength=1.0):
    n = int(2.2 * SR); u = np.arange(n) / SR
    f = 38 + 60 * np.exp(-u * 12)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-u * 2.6)
    noise = lp(rng.standard_normal(n), 2500) * np.exp(-u * 14) * 0.6
    return np.tanh((boom + noise) * 1.6) * strength

def whoosh(d=0.8, strength=0.7):
    n = int(d * SR); u = np.arange(n) / SR
    x = rng.standard_normal(n)
    env = np.sin(np.pi * u / d) ** 2
    lo = bp(x, 300, 1200); hi = bp(x, 1500, 6000)
    mixw = lo * (1 - u / d) + hi * (u / d)
    return mixw * env * strength * 1.8

def riser(d=1.4, strength=0.4):
    n = int(d * SR); u = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 800, 7000)
    return x * (u / d) ** 2.2 * strength

def tick(strength=0.25):
    n = int(0.12 * SR); u = np.arange(n) / SR
    return np.sin(2 * np.pi * 1800 * u) * np.exp(-u * 60) * strength

for s in (0.0, 8.40, 10.30, 282.3):
    add(sfx, s, impact(1.0))
for s in (13.30, 34.0, 116.6, 151.8, 208.7):
    add(sfx, s - 0.35, whoosh(0.8, 0.8)); add(sfx, s, impact(0.55))
for s in (34.0, 116.6, 151.8, 208.7, 282.3):
    add(sfx, s - 1.4, riser(1.4, 0.35))
# small whooshes on scoreboxes / big kinetic text
for s in (59.5, 69.6, 87.35, 103.1, 126.4, 133.8, 162.5, 173.5, 179.1, 202.5, 206.7, 212.5, 216.6, 225.2, 229.5, 276.5, 292.6):
    add(sfx, s - 0.25, whoosh(0.45, 0.35))
for s in (163.2, 164.0, 167.2, 168.6, 38.4, 92.6):
    add(sfx, s, tick(0.3))
add(sfx, 308.4, impact(0.8))
sfx = np.tanh(sfx * 0.9) * 0.9

def wr(path, data):
    data = np.clip(data, -1, 1)
    if data.ndim == 1:
        data = np.stack([data, data], 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((data * 32767).astype(np.int16).tobytes())

wr("build/music.wav", st)
wr("build/sfx.wav", sfx)
print("ok")
