"""Original fon musiqasi va ovoz effektlarini sintez qiladi (mualliflik huquqi muammosiz).
Foydalanish: python3 audio.py <out_dir>
Natija: music.wav (stereo 48k) va sfx.wav (stereo 48k)."""
import sys, numpy as np, wave
SR = 48000
DUR = 377.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
out = sys.argv[1]

def write(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())

def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    # vektorlashgan emas, lekin bloklarda tezroq: scipy ishlatmaslik uchun oddiy sikl o'rniga lfilter analogini qilamiz
    from itertools import accumulate
    b = 1 - a
    y = np.fromiter(accumulate(x * b, lambda p, v: p * a + v), dtype=np.float64, count=len(x))
    return y

def note_hz(m): return 440 * 2 ** ((m - 69) / 12)

BPM = 92; beat = 60 / BPM; bar = 4 * beat
t = np.arange(N) / SR

# ---- intensivlik egri chizig'i (bo'limlar bo'yicha) ----
pts = [(0, .9), (8.2, .75), (18, .7), (28, .95), (33.4, .55), (105.5, .8), (110, .55), (160, .7), (174, .5), (197.4, .7), (277.6, .65), (343, .6), (352, .8), (366, .9), (374.4, .7), (377, 0)]
xs, ys = zip(*pts); inten = np.interp(t, xs, ys)

# ---- akkordlar: Dm - Bb - F - C (har biri 2 takt) ----
prog = [[50, 53, 57, 62], [46, 50, 53, 58], [53, 57, 60, 65], [48, 52, 55, 60]]
pad = np.zeros(N)
seg = 2 * bar
for i in range(int(DUR / seg) + 1):
    a0 = int(i * seg * SR); a1 = min(N, int((i + 1) * seg * SR) + int(0.5 * SR))
    if a0 >= N: break
    tt = np.arange(a1 - a0) / SR; chord = prog[i % 4]
    env = np.minimum(1, tt / 0.8) * np.minimum(1, (a1 - a0) / SR - tt) .clip(0, 1)
    s = np.zeros(a1 - a0)
    for m in chord:
        f = note_hz(m)
        for det in (-0.12, 0.0, 0.11):  # yumshoq "supersaw" o'rniga sinuslar + ikkinchi garmonika
            ff = f * 2 ** (det / 12)
            s += np.sin(2 * np.pi * ff * tt) + 0.25 * np.sin(4 * np.pi * ff * tt + 0.3)
    pad[a0:a1] += s * env / 18
pad = onepole_lp(pad, 1800)

# ---- bass puls (8-lik notalar) ----
bass = np.zeros(N); step = beat / 2
roots = [38, 34, 41, 36]
for k in range(int(DUR / step)):
    st = k * step; a0 = int(st * SR); L = int(0.28 * SR)
    if a0 + L >= N: break
    root = roots[int(st // seg) % 4]; tt = np.arange(L) / SR
    e = np.exp(-tt * 9)
    bass[a0:a0 + L] += np.sin(2 * np.pi * note_hz(root) * tt) * e * (1.0 if k % 2 == 0 else 0.6)
bass = onepole_lp(bass, 400) * 0.5

# ---- soat taqillashi (yangiliklar ritmi) ----
tick = np.zeros(N); st16 = beat / 4
noise = rng.standard_normal(int(0.03 * SR))
hp = noise - onepole_lp(noise, 5000)
for k in range(int(DUR / st16)):
    a0 = int(k * st16 * SR)
    if a0 + len(hp) >= N: break
    acc = 1.0 if k % 4 == 0 else 0.45
    tick[a0:a0 + len(hp)] += hp * np.exp(-np.arange(len(hp)) / SR * 140) * acc
tick *= 0.08

# ---- yumshoq baraban (1 va 3-zarb) ----
kick = np.zeros(N)
for k in range(int(DUR / beat)):
    if k % 2: continue
    a0 = int(k * beat * SR); L = int(0.4 * SR)
    if a0 + L >= N: break
    tt = np.arange(L) / SR; f = 45 + 70 * np.exp(-tt * 30)
    kick[a0:a0 + L] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 8)
kick *= 0.35

music = pad * 0.55 + bass * inten + tick * np.clip(inten * 1.3 - 0.3, 0, 1) + kick * np.clip(inten * 1.5 - 0.6, 0, 1)
music *= (0.6 + 0.4 * inten)
fade = np.minimum(1, t / 0.5) * np.clip((DUR - t) / 2.5, 0, 1)
music *= fade
music /= np.max(np.abs(music)) + 1e-9
# stereo kengligi: o'ng kanalga kichik kechikish
d = int(0.012 * SR)
L = music; R = np.concatenate([np.zeros(d), music[:-d]])
write(f'{out}/music.wav', np.stack([L, R], 1) * 0.8)

# ---- SFX ----
sfx = np.zeros(N)
def impact(at, g=1.0):
    a0 = int(at * SR); L = int(1.6 * SR); tt = np.arange(L) / SR
    f = 38 + 90 * np.exp(-tt * 12)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3.2)
    nz = rng.standard_normal(L); nz = onepole_lp(nz, 900) * np.exp(-tt * 10) * 1.6
    sfx[a0:a0 + L] += (s + nz) * g
def whoosh(at, dur=0.7, g=0.6):
    L = int(dur * SR); a0 = int((at - dur * 0.6) * SR); tt = np.arange(L) / SR
    nz = rng.standard_normal(L)
    # harakatlanuvchi filtr: past va baland chastotali shovqin aralashmasi
    lo = onepole_lp(nz, 600); hi = onepole_lp(nz, 4000)
    mix = np.sin(np.pi * tt / dur) ** 2
    s = (lo * (1 - mix) + hi * mix) * np.sin(np.pi * tt / dur) ** 1.5
    sfx[max(0, a0):a0 + L] += s[: N - a0] * g
def riser(at, dur=2.0, g=0.35):
    L = int(dur * SR); a0 = int((at - dur) * SR); tt = np.arange(L) / SR
    f = 200 + 1800 * (tt / dur) ** 2
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * (tt / dur) ** 2 * 0.4 + onepole_lp(rng.standard_normal(L), 3000) * (tt / dur) ** 3
    sfx[a0:a0 + L] += s * g
for at in (0.02, 6.15, 28.1, 105.5): impact(at, 0.9)
riser(28.1, 2.2)
for at in (2.7, 8.25, 20.2, 33.4, 36.4, 58.85, 71.8, 91.7, 125.85, 160.3, 173.7, 197.4, 200.35, 202.1, 209.4, 227.0, 229.6, 246.55, 249.1, 258.3, 277.6, 293.8, 302.85, 336.4, 352.15, 366.3, 374.4):
    whoosh(at)
sfx /= np.max(np.abs(sfx)) + 1e-9
write(f'{out}/sfx.wav', np.stack([sfx, sfx], 1) * 0.7)
print('ok')
