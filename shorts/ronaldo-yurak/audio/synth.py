"""Original score + SFX for the Ronaldo heart short.

Everything here is synthesised from scratch (numpy only), so the music and
sound effects carry no third-party licence. Outputs two stereo 48 kHz stems:
  music.wav  - heartbeat-driven cinematic underscore
  sfx.wav    - impacts, whooshes, risers, ECG beeps, glitches
Timings are in seconds and follow the voice-over word timestamps.
"""
import numpy as np
from scipy.signal import lfilter
import wave
import sys
from pathlib import Path

SR = 48000
DUR = 35.6
N = int(SR * DUR)
rng = np.random.default_rng(7)
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else ".")


def t_arr(d):
    return np.arange(int(SR * d)) / SR


def onepole_lp(x, fc):
    """One-pole low-pass; fc may be scalar or per-sample array."""
    fc = np.broadcast_to(np.asarray(fc, dtype=float), x.shape)
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def lp_fast(x, fc, passes=2):
    # constant-coefficient one-pole via lfilter-like recursion (vectorised in chunks)
    a = np.exp(-2 * np.pi * fc / SR)
    y = x
    for _ in range(passes):
        y = lfilter([1 - a], [1, -a], y)
    return y


def hp(x, fc):
    return x - lp_fast(x, fc, 1)


def place(buf, sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    l = np.cos((pan + 1) * np.pi / 4)
    r = np.sin((pan + 1) * np.pi / 4)
    if sig.ndim == 1:
        buf[i : i + len(sig), 0] += sig * gain * l * np.sqrt(2)
        buf[i : i + len(sig), 1] += sig * gain * r * np.sqrt(2)
    else:
        buf[i : i + len(sig)] += sig * gain


def env_adsr(n, a, d, s, r, sus_level=0.6):
    e = np.zeros(n)
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    S = max(n - A - D - R, 0)
    seg = [np.linspace(0, 1, A, endpoint=False), np.linspace(1, sus_level, D, endpoint=False),
           np.full(S, sus_level), np.linspace(sus_level, 0, R)]
    e2 = np.concatenate(seg)[:n]
    e[: len(e2)] = e2
    return e


def reverb(st, decay=2.2, mix=0.25, pre=0.02):
    n = int(SR * decay)
    tt = np.arange(n) / SR
    out = st.copy()
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-6.9 * tt / decay)
        ir = lp_fast(ir, 6000, 1)
        ir[: int(pre * SR)] = 0
        ir /= np.sqrt(np.sum(ir ** 2))
        L = len(st) + n
        nfft = 1 << (L - 1).bit_length()
        wet = np.fft.irfft(np.fft.rfft(st[:, ch], nfft) * np.fft.rfft(ir, nfft), nfft)[: len(st)]
        out[:, ch] = st[:, ch] * (1 - mix) + wet * mix
    return out


def saw(f, d, detune=0.0):
    t = t_arr(d)
    ph = (f * (1 + detune) * t + rng.random()) % 1.0
    return 2 * ph - 1


# ------------------------------------------------------------------ instruments
def kick(f0=55, d=0.45, punch=1.0):
    t = t_arr(d)
    f = f0 + 90 * punch * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 7) + 0.15 * rng.standard_normal(len(t)) * np.exp(-t * 120)


def heartbeat(gain=1.0):
    """'lub-dub' — two low thumps."""
    lub = kick(48, 0.35, 0.6)
    dub = kick(58, 0.3, 0.5) * 0.7
    out = np.zeros(int(0.65 * SR))
    out[: len(lub)] += lub
    j = int(0.19 * SR)
    out[j : j + len(dub)] += dub[: len(out) - j]
    return lp_fast(out, 400, 1) * gain


def pad(freqs, d, cutoff=1800, att=0.8, rel=1.2):
    sig = np.zeros(int(SR * d))
    for f in freqs:
        for dt in (-0.006, 0.0, 0.007):
            sig += saw(f, d, dt)
    sig /= len(freqs) * 3
    sig = lp_fast(sig, cutoff, 2)
    return sig * env_adsr(len(sig), att, 0.5, 0, rel, 0.85)


def pluck(f, d=0.6):
    t = t_arr(d)
    s = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.3 * np.exp(-t * (4 + 3 * k)) for k in range(1, 7))
    return s * 0.5


def sub_drone(f, d):
    t = t_arr(d)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t + 0.3)
    return s * env_adsr(len(t), 1.5, 0.1, 0, 1.5, 1.0)


def noise(d):
    return rng.standard_normal(int(SR * d))


def impact(big=1.0):
    d = 3.2
    t = t_arr(d)
    f = 30 + 110 * np.exp(-t * 9)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    crack = lp_fast(noise(d), 3500, 1) * np.exp(-t * 18)
    s = boom * 1.0 + crack * 0.6 * big
    return np.tanh(s * 1.4) * 0.8


def whoosh(d=0.6, up=True):
    n = int(SR * d)
    x = noise(d)
    prog = np.linspace(0, 1, n)
    fc = 300 + 5000 * (np.sin(np.pi * prog) ** 2 if up else (1 - prog))
    y = onepole_lp(x, fc)
    y = hp(y, 150)
    env = np.sin(np.pi * prog) ** 1.6
    y = y * env
    st = np.zeros((n, 2))
    pan = np.linspace(-0.8, 0.8, n)
    st[:, 0] = y * np.cos((pan + 1) * np.pi / 4)
    st[:, 1] = y * np.sin((pan + 1) * np.pi / 4)
    return st * 1.4


def riser(d=1.6):
    n = int(SR * d)
    prog = np.linspace(0, 1, n)
    x = onepole_lp(noise(d), 200 + 7000 * prog ** 2)
    t = t_arr(d)
    tone = np.sin(2 * np.pi * np.cumsum(200 + 900 * prog ** 2) / SR) * 0.25
    return (hp(x, 200) * 0.8 + tone) * prog ** 2.2


def reverse_swell(d=0.9):
    t = t_arr(d)
    x = lp_fast(noise(d), 5000, 1) * np.exp(-t * 5)
    return x[::-1] * 0.8


def beep(f=1000, d=0.09):
    t = t_arr(d)
    return np.sin(2 * np.pi * f * t) * np.minimum(1, (d - t) * 60) * np.minimum(1, t * 400) * 0.35


def glitch(d=0.25):
    x = noise(d)
    x = np.round(x * 3) / 3
    t = t_arr(d)
    sq = np.sign(np.sin(2 * np.pi * 180 * t))
    g = (x * 0.4 + sq * 0.3) * (np.sin(2 * np.pi * 28 * t) > 0)
    return lp_fast(g, 6000, 1) * 0.5


def tick():
    t = t_arr(0.05)
    return np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 160) * 0.4


# ------------------------------------------------------------------ music
music = np.zeros((N, 2))
D1, A1, F2, Bb1, C2 = 36.71, 55.0, 87.31, 58.27, 65.41

# Drone bed through act 1-2 (ominous)
place(music, sub_drone(D1, 14.6), 0.0, 0.55)
place(music, pad([146.83, 174.61, 220.0], 10.5, 900, 1.5, 1.5), 0.2, 0.28)

# Heartbeats 72 bpm until doctors, then accelerating tachycardia 10.68 -> 14.3
beats = []
t = 0.0
while t < 10.6:
    beats.append((t, 0.9))
    t += 60 / 72
t = 10.68
bpm = 90.0
while t < 14.25:
    beats.append((t, 1.0))
    t += 60 / bpm
    bpm = min(bpm * 1.13, 200)
for bt, g in beats:
    place(music, heartbeat(g), bt, 0.85)

# Recovery 14.4 -> 18.3: calm major-ish pad + slow heartbeat returning to normal
place(music, pad([174.61, 220.0, 261.63, 349.23], 4.4, 1400, 0.6, 1.0), 14.45, 0.3)
for bt in (15.1, 15.95, 16.8, 17.65):
    place(music, heartbeat(0.6), bt, 0.6)
for k, f in enumerate([349.23, 440.0, 523.25, 698.46, 523.25, 440.0, 523.25, 698.46]):
    place(music, pluck(f), 16.1 + k * 0.27, 0.22, pan=(-0.4 if k % 2 else 0.4))

# Act 3 18.5 -> 24.3: epic drums + progression Dm - Bb - F - C
prog = [(18.5, [146.83, 174.61, 220.0], D1 * 2), (19.95, [116.54, 146.83, 174.61], Bb1),
        (21.4, [174.61, 220.0, 261.63], F2 / 2 * 2), (22.85, [130.81, 164.81, 196.0], C2)]
for st_, ch, root in prog:
    place(music, pad(ch + [c * 2 for c in ch], 1.75, 2400, 0.05, 0.6), st_, 0.32)
    place(music, sub_drone(root, 1.6), st_, 0.45)
bt = 18.5
step = 60 / 124
k = 0
while bt < 24.2:
    place(music, kick(52, 0.4, 1.0), bt, 0.75 if k % 2 == 0 else 0.5)
    if k % 2 == 1:
        snare = hp(noise(0.25), 900) * np.exp(-t_arr(0.25) * 18) * 0.35
        place(music, snare, bt, 0.9)
    hat = hp(noise(0.04), 6000) * np.exp(-t_arr(0.04) * 90) * 0.25
    place(music, hat, bt + step / 2, 0.8, pan=0.3)
    bt += step
    k += 1
for k in range(24):  # driving arp
    f = [293.66, 349.23, 440.0, 587.33][k % 4] * (1 if k < 12 else 1.122)
    place(music, pluck(f, 0.3), 18.5 + k * step / 2, 0.12, pan=0.5 if k % 2 else -0.5)

# Act 4 24.3: drop to near silence, then emotional build 25.3 -> 31.3, climax 29.1
place(music, sub_drone(D1, 7.2), 24.6, 0.4)
place(music, pad([146.83, 220.0, 293.66], 4.0, 1000, 1.2, 0.8), 25.2, 0.26)
place(music, pad([174.61, 220.0, 261.63, 349.23, 440.0], 3.2, 3200, 0.2, 1.4), 29.1, 0.36)
for bt in (27.56, 28.3):
    place(music, heartbeat(0.9), bt, 0.8)
for k in range(14):
    f = [440.0, 523.25, 587.33, 698.46][k % 4] * (2 ** (k // 4 / 12 * 2))
    place(music, pluck(f, 0.4), 25.4 + k * 0.26, 0.10 + k * 0.006, pan=0.5 if k % 2 else -0.5)
bt = 29.1
while bt < 31.2:
    place(music, kick(50, 0.4, 1.0), bt, 0.6)
    bt += 60 / 124

# Outro 31.46 -> end: suspense ticks + final chord
for k in range(12):
    place(music, tick(), 31.5 + k * 0.25, 0.6, pan=0.3 if k % 2 else -0.3)
place(music, pad([146.83, 174.61, 220.0, 277.18], 3.2, 1600, 0.4, 1.0), 31.46, 0.26)
place(music, sub_drone(D1, 4.0), 31.46, 0.45)

music = reverb(music, 2.6, 0.22)

# ------------------------------------------------------------------ sfx
sfx = np.zeros((N, 2))
place(sfx, impact(1.2), 0.0, 0.9)
place(sfx, glitch(0.22), 0.0, 0.5)
place(sfx, impact(0.6), 0.76, 0.55)
place(sfx, whoosh(0.5), 1.45, 0.6)
place(sfx, glitch(0.18), 3.94, 0.35)
place(sfx, whoosh(0.55), 4.2, 0.65)
place(sfx, whoosh(0.45), 5.05, 0.45)
place(sfx, whoosh(0.5), 6.5, 0.5)
place(sfx, reverse_swell(0.8), 7.5, 0.45)
place(sfx, riser(1.0), 9.7, 0.45)
place(sfx, impact(0.7), 10.68, 0.6)
# ECG beeps on tachy beats
for bt, g in beats:
    if bt >= 10.68:
        place(sfx, beep(1046.5), bt + 0.02, 0.55, pan=0.2)
place(sfx, glitch(0.3), 14.2, 0.4)
place(sfx, whoosh(0.7, up=False), 14.35, 0.5)
place(sfx, tick(), 16.12, 0.8)
place(sfx, whoosh(0.5), 16.85, 0.55)
place(sfx, riser(1.7), 16.8, 0.6)
place(sfx, impact(1.3), 18.5, 0.95)
for at in (19.3, 20.44, 21.42):
    place(sfx, whoosh(0.4), at - 0.2, 0.55)
    place(sfx, impact(0.4), at, 0.35)
place(sfx, whoosh(0.5), 22.6, 0.5)
place(sfx, reverse_swell(0.9), 23.4, 0.55)
place(sfx, impact(0.9), 24.3, 0.75)
place(sfx, glitch(0.2), 24.3, 0.35)
place(sfx, whoosh(0.6), 25.1, 0.4)
place(sfx, whoosh(0.5), 27.6, 0.5)
place(sfx, riser(1.2), 27.9, 0.6)
place(sfx, impact(1.3), 29.1, 0.95)
place(sfx, whoosh(0.5), 30.45, 0.45)
place(sfx, reverse_swell(0.8), 30.66, 0.5)
place(sfx, impact(0.9), 31.46, 0.75)
place(sfx, whoosh(0.4), 32.1, 0.55)
place(sfx, impact(0.5), 32.3, 0.45)
place(sfx, whoosh(0.4), 33.85, 0.55)
place(sfx, impact(1.0), 34.06, 0.8)
sfx = reverb(sfx, 1.8, 0.18)


def write(path, st, peak=0.89):
    st = st / max(np.max(np.abs(st)), 1e-9) * peak
    data = (st * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


write(OUT / "music.wav", music)
write(OUT / "sfx.wav", sfx)
print("ok", [b for b, _ in beats if b >= 10.68])
