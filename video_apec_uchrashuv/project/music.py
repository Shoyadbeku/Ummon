"""Original synthesized underscore + SFX (no third-party audio)."""
import numpy as np, wave, sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
import scenes as SC

SR = 48000
DUR = SC.END + 0.5
N = int(DUR * SR)
rng = np.random.default_rng(7)
t = np.arange(N) / SR
BPM = 96; beat = 60 / BPM


def onepole(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x); s = 0.0
    # vectorised via lfilter-free recursion in chunks
    from itertools import accumulate
    out = np.empty_like(x)
    acc = 0.0
    for i in range(0, len(x), 4800):
        seg = x[i:i + 4800]
        o = np.empty_like(seg)
        for j, v in enumerate(seg):
            acc = (1 - a) * v + a * acc
            o[j] = acc
        out[i:i + 4800] = o
    return out


def lp(x, fc):
    # cheap FFT lowpass
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / fc) ** 4)
    return np.fft.irfft(X, len(x))


def hp(x, fc):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (fc / np.maximum(f, 1)) ** 4)
    return np.fft.irfft(X, len(x))


def saw(freq, tt):
    return 2 * ((tt * freq) % 1) - 1


def note(m):
    return 440 * 2 ** ((m - 69) / 12)


# --- chord pad: Am F C G (2 bars each = 8 beats)
prog = [[57, 60, 64], [53, 57, 60], [48, 55, 60, 64], [55, 59, 62]]
bar8 = 8 * beat
pad = np.zeros(N)
for k in range(int(DUR / bar8) + 1):
    s0 = int(k * bar8 * SR); s1 = min(N, int((k + 1) * bar8 * SR) + int(0.3 * SR))
    if s0 >= N: break
    tt = t[s0:s1] - t[s0]
    env = np.minimum(1, tt / 1.2) * np.minimum(1, np.maximum(0, (bar8 + 0.3 - tt)) / 0.6)
    ch = prog[k % 4]
    sig = sum(saw(note(m), tt) + saw(note(m) * 1.004, tt + 0.1) + 0.5 * saw(note(m - 12), tt) for m in ch)
    pad[s0:s1] += sig * env / (len(ch) * 2.5)
pad = lp(pad, 900)

# --- sub drone on chord root
sub = np.zeros(N)
roots = [45, 41, 36, 43]
for k in range(int(DUR / bar8) + 1):
    s0 = int(k * bar8 * SR); s1 = min(N, int((k + 1) * bar8 * SR))
    if s0 >= N: break
    tt = t[s0:s1] - t[s0]
    sub[s0:s1] = np.sin(2 * np.pi * note(roots[k % 4]) * tt) * np.minimum(1, tt / 0.05)

# --- pulse: soft kick on 1&3, ticks on 8ths, 16th pluck arp
kick = np.zeros(N); tick = np.zeros(N); arp = np.zeros(N)
klen = int(0.35 * SR); kt = np.arange(klen) / SR
kshape = np.sin(2 * np.pi * (45 * kt + 60 * (1 - np.exp(-kt * 30)) / 30)) * np.exp(-kt * 9)
tlen = int(0.03 * SR); tshape = rng.standard_normal(tlen) * np.exp(-np.arange(tlen) / SR * 180)
alen = int(0.18 * SR); at = np.arange(alen) / SR
nb = int(DUR / beat * 4)
for i in range(nb):
    s0 = int(i * beat / 4 * SR)
    if s0 + alen >= N: break
    if i % 8 == 0:
        kick[s0:s0 + klen] += kshape
    if i % 2 == 0:
        tick[s0:s0 + tlen] += tshape * (1.0 if i % 4 == 2 else 0.55)
    ch = prog[(i // 32) % 4]
    m = ch[(i * 3) % len(ch)] + 12
    arp[s0:s0 + alen] += (saw(note(m), at) * np.exp(-at * 22))
tick = hp(tick, 6000)
arp = lp(arp, 2500)

# --- intensity curve per section (0..1)
sec = np.ones(N) * 0.75
def setr(a, b, v):
    sec[int(a * SR):int(b * SR)] = v
setr(0, 34.5, 1.0); setr(34.5, 123, 0.75); setr(123, 213, 0.7); setr(213, 331, 0.85); setr(331, 382, 0.7); setr(382, DUR, 0.9)
sec = lp(sec, 0.5)
music = (0.55 * pad + 0.5 * sub + 0.55 * kick + 0.10 * tick + 0.10 * arp * sec) * sec
music /= np.max(np.abs(music)) + 1e-9
music *= 0.9
# fade in/out
music *= np.minimum(1, t / 0.4) * np.minimum(1, np.maximum(0, DUR - t) / 3.0)

# --- SFX
sfx = np.zeros(N)
def impact(at_):
    s0 = int(at_ * SR); L = int(1.6 * SR); tt = np.arange(L) / SR
    boom = np.sin(2 * np.pi * (35 * tt + 90 * (1 - np.exp(-tt * 8)) / 8)) * np.exp(-tt * 2.6)
    nz = lp(rng.standard_normal(L), 1800) * np.exp(-tt * 9) * 0.6
    e = min(N, s0 + L) - s0
    sfx[s0:s0 + e] += (boom + nz)[:e] * 0.9
def whoosh(at_, L=0.45, amp=0.35):
    s0 = int((at_ - L * 0.7) * SR); n = int(L * SR); tt = np.arange(n) / SR
    env = np.sin(np.pi * tt / L) ** 2
    x = hp(lp(rng.standard_normal(n), 3500), 400) * env
    s0 = max(0, s0); e = min(N, s0 + n) - s0
    sfx[s0:s0 + e] += x[:e] * amp
def riser(end, L=1.4):
    s0 = int((end - L) * SR); n = int(L * SR); tt = np.arange(n) / SR
    env = (tt / L) ** 2
    x = hp(rng.standard_normal(n), 1500) * env * 0.25 + np.sin(2 * np.pi * (200 * tt + 300 * tt ** 2 / L)) * env * 0.08
    sfx[s0:s0 + n] += x

for s in SC.S:
    if s["tr"] == "flash":
        impact(s["t0"])
        if s["t0"] > 2:
            riser(s["t0"])
    elif s["tr"] == "whip":
        whoosh(s["t0"])
    elif s["t0"] < 34:
        whoosh(s["t0"], amp=0.2)
# hook internal cuts
for x in (2.45, 4.75, 7.85, 9.05, 10.15):
    whoosh(x, amp=0.22)
sfx = np.clip(sfx, -1, 1)


def wr(name, x):
    st = np.stack([x, x], 1)
    st = np.clip(st * 32767, -32768, 32767).astype(np.int16)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())


wr("audio/music.wav", music)
wr("audio/sfx.wav", sfx)
print("ok", DUR)
