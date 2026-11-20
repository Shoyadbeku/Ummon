"""Original synthesized news score + SFX (no third-party music), and final mix."""
import numpy as np, subprocess, sys, os
from scipy.signal import butter, sosfilt

SR = 48000
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 348.0
OUT = os.path.join(os.path.dirname(__file__), "..", "audio")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)
N = int(DUR * SR)
t = np.arange(N) / SR

def lp(x, f, order=2): return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)
def hp(x, f, order=2): return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)
def note(m): return 440.0 * 2 ** ((m - 69) / 12)

# intensity envelope over time (0..1) by sections
KEYS = [(0, 0.95), (18.8, 0.9), (19.3, 0.45), (44.0, 0.55), (95.4, 0.5), (120.0, 0.55), (144.0, 0.8),
        (217.5, 0.55), (280.4, 0.8), (316.4, 0.55), (333.0, 0.4), (DUR, 0.35)]
def env_curve():
    e = np.zeros(N)
    for (a, va), (b, vb) in zip(KEYS, KEYS[1:]):
        i0, i1 = int(a * SR), min(N, int(b * SR))
        if i1 > i0:
            ramp = min(i1 - i0, int(0.6 * SR))
            seg = np.full(i1 - i0, vb if False else va)
            e[i0:i1] = seg
    # smooth
    k = int(0.5 * SR)
    c = np.cumsum(np.insert(e, 0, 0)); sm = (c[k:] - c[:-k]) / k
    e[k // 2:k // 2 + len(sm)] = sm
    return e
INT = env_curve()

BPM = 96.0; beat = 60 / BPM; bar = beat * 4
# chord progression (Dm, Bb, F, C) -> roots and triads (midi)
PROG = [(50, [62, 65, 69]), (46, [58, 62, 65]), (53, [60, 65, 69]), (48, [60, 64, 67])]

music = np.zeros(N)
# 1) sub drone on chord roots
drone = np.zeros(N)
pad = np.zeros(N)
nb = int(DUR / bar) + 2
for bi in range(nb):
    root, triad = PROG[(bi // 2) % 4]
    s0 = int(bi * bar * SR); s1 = min(N, int((bi + 1) * bar * SR) + int(0.3 * SR))
    if s0 >= N: break
    tt = np.arange(s1 - s0) / SR
    fade = np.minimum(1, np.minimum(tt / 0.25, (tt[-1] - tt + 1e-3) / 0.3))
    f0 = note(root - 12)
    drone[s0:s1] += (np.sin(2 * np.pi * f0 * tt) * 0.6 + np.sin(2 * np.pi * f0 * 2 * tt) * 0.15) * fade
    # detuned saw pad
    p = np.zeros_like(tt)
    for m in triad:
        for det in (-0.07, 0.0, 0.08):
            f = note(m) * 2 ** (det / 12)
            ph = (f * tt + rng.random()) % 1.0
            p += (2 * ph - 1)
    pad[s0:s1] += p / 9 * fade
pad = lp(pad, 1400, 2)
lfo = 0.75 + 0.25 * np.sin(2 * np.pi * t / (bar * 2))
music += drone * 0.55 + pad * 0.35 * lfo

# 2) pulse: muted 8th-note pluck on root (news "ticking")
pulse = np.zeros(N)
step = beat / 2
k = 0
while k * step < DUR:
    s0 = int(k * step * SR); L = int(0.18 * SR)
    if s0 + L >= N: break
    bi = int(k * step / bar)
    root, triad = PROG[(bi // 2) % 4]
    m = triad[k % 3] + (12 if k % 4 == 3 else 0)
    tt = np.arange(L) / SR
    pulse[s0:s0 + L] += np.sin(2 * np.pi * note(m) * tt) * np.exp(-tt * 28) * (1.0 if k % 2 == 0 else 0.6)
    k += 1
music += lp(pulse, 2500) * 0.22 * np.clip((INT - 0.4) / 0.4, 0, 1)

# 3) ticking hats
hat = np.zeros(N)
k = 0
noise = rng.standard_normal(int(0.05 * SR))
hnoise = hp(noise, 7000)
while k * (beat / 4) < DUR:
    s0 = int(k * beat / 4 * SR); L = len(hnoise)
    if s0 + L >= N: break
    a = 0.5 if k % 4 == 0 else 0.25
    hat[s0:s0 + L] += hnoise * np.exp(-np.arange(L) / SR * 90) * a
    k += 1
music += hat * 0.08 * np.clip((INT - 0.5) / 0.3, 0, 1)

# 4) kick on beats in intense parts
kick = np.zeros(N)
L = int(0.35 * SR); tt = np.arange(L) / SR
kshape = np.sin(2 * np.pi * (45 * tt + 60 * (1 - np.exp(-tt * 30)) / 30)) * np.exp(-tt * 9)
k = 0
while k * beat < DUR:
    s0 = int(k * beat * SR)
    if s0 + L >= N: break
    kick[s0:s0 + L] += kshape
    k += 1
music += kick * 0.55 * np.clip((INT - 0.7) / 0.2, 0, 1)

music *= (0.35 + 0.65 * INT)
music = hp(music, 30)

# ---- SFX ----
sfx = np.zeros(N)
def add(sig, at, gain=1.0):
    s0 = int(at * SR); s1 = min(N, s0 + len(sig))
    if s0 < N: sfx[s0:s1] += sig[:s1 - s0] * gain

def impact(dur=2.5):
    L = int(dur * SR); tt = np.arange(L) / SR
    boom = np.sin(2 * np.pi * (38 * tt + 70 * (1 - np.exp(-tt * 12)) / 12)) * np.exp(-tt * 2.2)
    n = lp(rng.standard_normal(L), 900) * np.exp(-tt * 6) * 0.6
    crack = hp(rng.standard_normal(L), 2500) * np.exp(-tt * 40) * 0.5
    return (boom + n + crack) * 0.9

def whoosh(dur=1.0, up=True):
    L = int(dur * SR); tt = np.arange(L) / SR
    n = rng.standard_normal(L)
    out = np.zeros(L); seg = int(0.02 * SR)
    for i in range(0, L, seg):
        p = i / L; fc = 300 + (5000 if up else 2500) * (p if up else 1 - p)
        out[i:i + seg] = bp(n[max(0, i - 2000):i + seg], fc * 0.6, min(fc * 1.6, 20000))[-len(out[i:i + seg]):]
    shape = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 2
    return out * shape * 1.2

def riser(dur=2.0):
    L = int(dur * SR); tt = np.arange(L) / SR
    f = 200 * (1 + 4 * (tt / dur) ** 2)
    ph = np.cumsum(f) / SR
    s = np.sin(2 * np.pi * ph) * 0.3 + hp(rng.standard_normal(L), 3000) * 0.3
    return s * (tt / dur) ** 2

def stamp_hit():
    L = int(0.8 * SR); tt = np.arange(L) / SR
    return (np.sin(2 * np.pi * 70 * tt) * np.exp(-tt * 10) + lp(rng.standard_normal(L), 2000) * np.exp(-tt * 25) * 0.7)

for at in (0.0, 2.30, 16.55): add(impact(), at, 0.9)
add(riser(2.0), 14.6, 0.6)
add(whoosh(0.9), 19.0, 0.7)
for at in (43.6, 95.1, 119.6, 143.8, 217.3, 280.2):
    add(whoosh(0.8), at, 0.6)
for at in (110.3, 199.9): add(stamp_hit(), at, 0.7)
add(impact(3.5), 342.0, 0.35)

def save(x, name, peak=0.9):
    x = x / (np.max(np.abs(x)) + 1e-9) * peak
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    p = os.path.join(OUT, name)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", p], input=pcm.tobytes(), check=True)
    return p

save(music, "music.wav", 0.8)
save(sfx, "sfx.wav", 0.9)
print("ok")
