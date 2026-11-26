"""Original procedural news-documentary music bed + SFX (no third-party samples).
Usage: python3 music.py OUT_DIR TOTAL_SECONDS
"""
import sys, numpy as np, wave

SR = 48000
out_dir, total = sys.argv[1], float(sys.argv[2])
N = int(SR * total)
rng = np.random.default_rng(7)
t = np.arange(N) / SR

def midi(n): return 440.0 * 2 ** ((n - 69) / 12)

def env_adsr(n, a, d, s, r):
    e = np.ones(n) * s
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    a = max(a, 1); e[:a] = np.linspace(0, 1, a)
    e[a:a + d] = np.linspace(1, s, len(e[a:a + d]))
    if r: e[-r:] *= np.linspace(1, 0, r)
    return e

def lowpass(x, fc):
    # one-pole lowpass
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc; y[i] = acc
    return y

BPM = 92.0
beat = 60.0 / BPM
bar = beat * 4
# A minor progression: Am - F - C - G  (2 bars each)
prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [55, 60, 64]), (55, [55, 59, 62])]

mix = np.zeros(N)
pad = np.zeros(N); bass = np.zeros(N); pulse = np.zeros(N); hat = np.zeros(N); kick = np.zeros(N); arp = np.zeros(N)

chord_len = bar * 2
nchords = int(np.ceil(total / chord_len))
for c in range(nchords):
    root, notes = prog[c % 4]
    s = int(c * chord_len * SR); e = min(N, int((c + 1) * chord_len * SR) + int(0.5 * SR))
    n = e - s
    if n <= 0: break
    tt = np.arange(n) / SR
    en = env_adsr(n, 0.8, 0.5, 0.8, 0.8)
    for k, m in enumerate(notes):
        f = midi(m + 12)
        for det in (-0.12, 0.12):
            ff = f * 2 ** (det / 12)
            # soft saw approximation (few harmonics)
            w = sum(np.sin(2 * np.pi * ff * h * tt + k) / h for h in range(1, 5))
            pad[s:e] += 0.05 * en * w
    # sub bass: eighth-note pulse on root
    f = midi(root - 12)
    for q in range(16):
        bs = s + int(q * beat / 2 * SR); be = min(e, bs + int(beat / 2 * 0.9 * SR))
        if bs >= N or be <= bs: continue
        tb = np.arange(be - bs) / SR
        bass[bs:be] += 0.18 * np.sin(2 * np.pi * f * tb) * np.exp(-tb * 3.0)
    # arpeggio (sixteenths, subtle)
    arp_notes = [notes[0] + 24, notes[1] + 24, notes[2] + 24, notes[1] + 24]
    for q in range(32):
        a_s = s + int(q * beat / 4 * SR); a_e = min(N, a_s + int(0.18 * SR))
        if a_s >= N: break
        ta = np.arange(a_e - a_s) / SR
        arp[a_s:a_e] += 0.035 * np.sin(2 * np.pi * midi(arp_notes[q % 4]) * ta) * np.exp(-ta * 18)

# kick on beats 1 & 3, hats on eighths
nb = int(total / beat) + 1
for b in range(nb):
    s = int(b * beat * SR)
    if s >= N: break
    if b % 2 == 0:
        n = min(int(0.35 * SR), N - s); tk = np.arange(n) / SR
        fk = 45 + 70 * np.exp(-tk * 30)
        kick[s:s + n] += 0.35 * np.sin(2 * np.pi * np.cumsum(fk) / SR) * np.exp(-tk * 9)
    for h in range(2):
        hs = s + int(h * beat / 2 * SR); n = min(int(0.05 * SR), N - hs)
        if n <= 0: continue
        th = np.arange(n) / SR
        noise = rng.standard_normal(n); noise = np.diff(np.concatenate([[0], noise]))
        hat[hs:hs + n] += (0.03 if h else 0.02) * noise * np.exp(-th * 80)

# Energy automation (0..1) keyed to narration structure (seconds)
def auto(points):
    xs, ys = zip(*points); return np.interp(t, xs, ys)
energy = auto([(0, 0.95), (22.5, 0.95), (23, 0.55), (30, 0.7), (66, 0.6), (68.5, 0.75), (93, 0.65), (110.8, 0.7), (115.6, 0.6),
               (141.8, 0.75), (176.4, 0.8), (246, 0.6), (256.8, 0.85), (266.4, 0.6), (298, 0.5), (313.4, 0.55), (329, 0.75),
               (345.4, 0.85), (total, 0.85)])
rhythm = auto([(0, 1), (22.8, 1), (23.2, 0.45), (30, 1), (298, 1), (298.5, 0.35), (329, 0.8), (total, 0.8)])

mix = pad * (0.5 + 0.5 * energy) + bass * energy + kick * energy * rhythm + hat * energy * rhythm + arp * energy
# fade in/out
fi = int(1.0 * SR); fo = int(4.0 * SR)
mix[:fi] *= np.linspace(0, 1, fi); mix[-fo:] *= np.linspace(1, 0, fo)
mix /= np.max(np.abs(mix)) + 1e-9
mix *= 0.7

def write(path, x):
    x = np.clip(x, -1, 1)
    st = np.stack([x, x], 1) if x.ndim == 1 else x
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())

# slight stereo width on pad via delay
L = mix.copy(); R = np.concatenate([np.zeros(int(0.012 * SR)), mix[:-int(0.012 * SR)]])
write(f"{out_dir}/music_bed.wav", np.stack([L, R], 1))

# ---- SFX ----
def whoosh(dur=0.8, up=True):
    n = int(dur * SR); tt = np.arange(n) / SR
    noise = rng.standard_normal(n)
    fc = np.linspace(300, 6000, n) if up else np.linspace(6000, 300, n)
    y = np.empty(n); acc = 0.0
    for i in range(n):
        a = np.exp(-2 * np.pi * fc[i] / SR); acc = (1 - a) * noise[i] + a * acc; y[i] = acc
    e = np.sin(np.pi * tt / dur) ** 2
    y = y * e; return y / (np.max(np.abs(y)) + 1e-9) * 0.6

def impact(dur=1.6):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = 38 + 90 * np.exp(-tt * 12)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3.2)
    noise = lowpass(rng.standard_normal(n), 1800) * np.exp(-tt * 14) * 2
    y = body + noise; return y / (np.max(np.abs(y)) + 1e-9) * 0.85

def tick(dur=0.06):
    n = int(dur * SR); tt = np.arange(n) / SR
    y = np.sin(2 * np.pi * 2200 * tt) * np.exp(-tt * 90); return y * 0.4

write(f"{out_dir}/sfx_whoosh.wav", whoosh())
write(f"{out_dir}/sfx_whoosh_down.wav", whoosh(up=False))
write(f"{out_dir}/sfx_impact.wav", impact())
write(f"{out_dir}/sfx_tick.wav", tick())
print("ok")
