# Self-generated score + SFX (no third-party music => no licensing issues).
import numpy as np, wave, sys
SR = 48000
TOTAL = 357.75
N = int(SR * TOTAL)
rng = np.random.default_rng(7)
t = np.arange(N) / SR


def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    # vectorised via lfilter-like recursion in chunks
    from itertools import accumulate
    out = np.zeros_like(x)
    b = 1 - a
    acc = 0.0
    for i in range(0, len(x), 1 << 16):
        seg = x[i:i + (1 << 16)]
        o = np.empty_like(seg)
        for j, v in enumerate(seg):
            acc = b * v + a * acc
            o[j] = acc
        out[i:i + len(seg)] = o
    return out


def lp_fft(x, fc, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = 1 / np.sqrt(1 + (f / fc) ** (2 * order))
    return np.fft.irfft(X * H, len(x))


def bp_fft(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = (1 / np.sqrt(1 + (f / hi) ** 4)) * (1 / np.sqrt(1 + (lo / np.maximum(f, 1)) ** 4))
    return np.fft.irfft(X * H, len(x))


def note(m):
    return 440 * 2 ** ((m - 69) / 12)


# ---------------- pad: chord progression Dm - Bb - Gm - A (minor, tense)
chords = [[38, 45, 50, 53, 57], [34, 41, 46, 50, 53], [31, 43, 46, 50, 55], [33, 45, 49, 52, 57]]
CH = 12.0  # seconds per chord
pad = np.zeros(N)
for k in range(int(TOTAL / CH) + 1):
    s0 = int(k * CH * SR)
    s1 = min(N, int((k + 1) * CH * SR + 2 * SR))
    if s0 >= N:
        break
    tt = np.arange(s1 - s0) / SR
    env = np.minimum(1, tt / 2.5) * np.minimum(1, np.maximum(0, (s1 - s0) / SR - tt) / 2.0)
    seg = np.zeros(s1 - s0)
    for m in chords[k % 4]:
        f0 = note(m)
        for h, amp in ((1, 1.0), (2, 0.35), (3, 0.18), (4, 0.08)):
            det = 1 + 0.0015 * rng.standard_normal()
            seg += amp * np.sin(2 * np.pi * f0 * h * det * tt + rng.uniform(0, 6.28)) / (1 + 0.3 * (m > 50))
    pad[s0:s1] += seg * env
pad = lp_fft(pad, 900)
pad *= 0.75 + 0.25 * np.sin(2 * np.pi * t / 7.0)
pad /= np.max(np.abs(pad)) + 1e-9

# ---------------- pulse: 96 bpm news-style ticking + low hits
BPM = 96
beat = 60 / BPM
pulse = np.zeros(N)
tick_len = int(0.035 * SR)
tick = rng.standard_normal(tick_len) * np.exp(-np.linspace(0, 8, tick_len))
tick = bp_fft(np.pad(tick, (0, 4096)), 2500, 9000)[:tick_len + 4096]
kick_len = int(0.35 * SR)
kt = np.arange(kick_len) / SR
kick = np.sin(2 * np.pi * (48 * kt + 60 * (1 - np.exp(-kt * 30)) / 30)) * np.exp(-kt * 9)
nb = int(TOTAL / (beat / 2))
for i in range(nb):
    s = int(i * beat / 2 * SR)
    if s + len(tick) < N:
        pulse[s:s + len(tick)] += tick * (0.55 if i % 2 else 0.3)
    if i % 8 == 0 and s + kick_len < N:
        pulse[s:s + kick_len] += kick * 1.6
    if i % 8 == 5 and s + kick_len < N:
        pulse[s:s + kick_len] += kick * 0.8
pulse /= np.max(np.abs(pulse)) + 1e-9

# ---------------- sub drone
sub = np.sin(2 * np.pi * note(26) * t) * 0.5 + np.sin(2 * np.pi * note(38) * t) * 0.25
sub *= 0.6 + 0.4 * np.sin(2 * np.pi * t / 11)

# intensity curve (0..1) per time: louder in hook / bumpers / outro, calmer under quotes
pts = [(0, 1.0), (6.5, 0.85), (11.6, 0.6), (35.0, 0.6), (35.6, 0.95), (37.5, 0.6), (83.0, 0.9), (85, 0.55),
       (144.2, 0.9), (147.7, 0.55), (212.4, 0.95), (215.3, 0.6), (285.0, 0.95), (287, 0.55), (292, 0.45),
       (333.0, 0.75), (345.7, 0.85), (355.0, 0.7), (357.75, 0.0)]
xs, ys = zip(*pts)
inten = np.interp(t, xs, ys)
pulse_gate = np.interp(t, [0, 30, 31, 292, 293, 305, 306, 345, 346, 358], [1, 1, 1, 1, 0.4, 0.4, 1, 1, 0.6, 0.6])

music = (0.55 * pad + 0.30 * pulse * pulse_gate + 0.25 * sub) * inten
music /= np.max(np.abs(music)) + 1e-9

# ---------------- SFX
sfx = np.zeros(N)


def add(sig, at, g=1.0):
    s = int(at * SR)
    e = min(N, s + len(sig))
    if s < N:
        sfx[s:e] += sig[:e - s] * g


def impact(dur=2.5):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (35 * tt + 90 * (1 - np.exp(-tt * 12)) / 12)) * np.exp(-tt * 2.2)
    nz = lp_fft(rng.standard_normal(n), 1800) * np.exp(-tt * 5)
    x = boom + 0.6 * nz / (np.max(np.abs(nz)) + 1e-9)
    return x / np.max(np.abs(x))


def whoosh(dur=0.9, rev=False):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    nz = rng.standard_normal(n)
    # sweeping band via moving FFT bands: approximate with two crossfaded bands
    lo = bp_fft(nz, 300, 1500)
    hi = bp_fft(nz, 1500, 7000)
    k = tt / dur
    x = lo * (1 - k) + hi * k
    env = np.sin(np.pi * np.clip(k, 0, 1)) ** 2
    x = x * env
    if rev:
        x = x[::-1]
    return x / (np.max(np.abs(x)) + 1e-9)


def riser(dur=1.5):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = 200 + 1800 * (tt / dur) ** 2
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3 + 0.7 * bp_fft(rng.standard_normal(n), 800, 6000)
    x *= (tt / dur) ** 2
    return x / (np.max(np.abs(x)) + 1e-9)


IMP = impact()
add(IMP, 0.0, 1.0)
add(IMP, 2.1, 0.8)
for at in (4.2, 37.1, 147.7, 160.9, 172.6, 181.45, 197.7, 215.3, 268.3):
    add(whoosh(0.8), at - 0.35, 0.45)
for at in (35.6, 83.0, 144.2, 212.4, 285.0):
    add(riser(1.2), at - 1.2, 0.35)
    add(IMP, at, 0.55)
for at in (11.6, 17.1, 30.4, 50.65, 62.8, 78.65, 84.55, 103.8, 132.6, 246.7, 254.9, 292.0, 305.7, 320.1, 345.7):
    add(whoosh(0.6), at - 0.25, 0.3)
add(IMP, 50.65, 0.35)
add(IMP, 98.8, 0.35)

sfx /= np.max(np.abs(sfx)) + 1e-9


def write(path, x):
    x = np.clip(x, -1, 1)
    st = np.stack([x, x], 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype('<i2').tobytes())


write(sys.argv[1] + '/music.wav', music * 0.9)
write(sys.argv[1] + '/sfx.wav', sfx * 0.9)
print('ok')
