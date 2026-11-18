"""Procedurally synthesised SFX bed (no third-party samples -> no licence issues).
Cue times are in seconds and follow the edit in shots.SHOTS (24 fps).
Output: audio/sfx.wav (48 kHz stereo float->16-bit)."""
import numpy as np, wave, os

SR = 48000
DUR = 1049 / 24.0
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rng = np.random.default_rng(7)
L = int(DUR * SR) + SR
bus = np.zeros((L, 2))


def t_(n):
    return np.arange(n) / SR


def env(n, a=0.005, r=0.2, shape=2.0):
    t = t_(n)
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / max(r, 1e-4) * shape)
    return e


def lp(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)):
        s = (1 - a) * x[i] + a * s; y[i] = s
    return y


def lp_fast(x, cutoff):  # vectorised one-pole via cumulative trick (approx, block)
    k = max(1, int(SR / cutoff / 2))
    c = np.cumsum(np.insert(x, 0, 0))
    y = (c[k:] - c[:-k]) / k
    return np.concatenate([y, np.zeros(k - 1)])


def hp_fast(x, cutoff):
    return x - lp_fast(x, cutoff)


def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= L:
        return
    sig = sig[: L - i]
    gl, gr = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    if sig.ndim == 1:
        bus[i:i + len(sig), 0] += sig * gain * gl * 1.414
        bus[i:i + len(sig), 1] += sig * gain * gr * 1.414
    else:
        bus[i:i + len(sig)] += sig * gain


def noise(n):
    return rng.standard_normal(n)


def whoosh(d=0.45, up=True):
    n = int(d * SR); t = t_(n)
    x = noise(n)
    e = np.sin(np.pi * t / d) ** 2
    lo = lp_fast(x, 600 + 2500 * (t / d if up else 1 - t / d).mean())
    hi = hp_fast(lp_fast(x, 4000), 800)
    return (0.6 * lo + 0.5 * hi) * e


def impact(d=1.6, f=48):
    n = int(d * SR); t = t_(n)
    f_t = f * (1 + 1.5 * np.exp(-t * 18))
    body = np.sin(2 * np.pi * np.cumsum(f_t) / SR) * np.exp(-t * 2.6)
    crack = lp_fast(noise(n), 3000) * np.exp(-t * 30)
    return np.tanh(1.6 * (body + 0.5 * crack))


def can_crack():
    n = int(0.9 * SR); t = t_(n)
    click = hp_fast(noise(n), 2500) * np.exp(-t * 300) * 1.4
    pop = hp_fast(noise(n), 1200) * np.exp(-np.maximum(0, t - 0.06) * 60) * (t > 0.06) * 1.2
    hiss = hp_fast(noise(n), 3500) * (np.exp(-np.maximum(0, t - 0.07) * 4.5) * (t > 0.07)) * 0.55
    ring = np.sin(2 * np.pi * 3100 * t) * np.exp(-t * 40) * 0.2
    return click + pop + hiss + ring


def clink():
    n = int(0.5 * SR); t = t_(n)
    s = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) * a for f, d, a in ((2350, 18, .5), (3720, 25, .3), (5210, 35, .2)))
    return s + hp_fast(noise(n), 3000) * np.exp(-t * 200) * 0.5


def squeak(d=0.18, f0=3600):
    n = int(d * SR); t = t_(n)
    f = f0 + 900 * np.sin(np.pi * t / d) + 120 * np.sin(2 * np.pi * 38 * t)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    return s * np.sin(np.pi * t / d) ** 0.7 * 0.5


def scurry(d):
    n = int(d * SR)
    x = np.zeros(n)
    t = 0.0
    while t < d - 0.03:
        k = int(t * SR)
        m = int(0.012 * SR)
        x[k:k + m] += hp_fast(noise(m), 2000) * np.exp(-t_(m) * 400) * rng.uniform(0.4, 1.0)
        t += rng.uniform(0.03, 0.07)
    # metallic tapping on can lids
    tt = t_(n)
    return x * 0.9


def sniff(d):
    n = int(d * SR); out = np.zeros(n); t = 0.0
    while t < d - 0.1:
        m = int(0.06 * SR); k = int(t * SR)
        out[k:k + m] += hp_fast(lp_fast(noise(m), 6000), 1500) * np.sin(np.pi * t_(m) / 0.06) * 0.35
        t += rng.uniform(0.09, 0.16)
    return out


def drip():
    n = int(0.35 * SR); t = t_(n)
    f = 900 + 1400 * np.exp(-t * 35)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22) * 0.8


def hum(d, f=120, buzz=True):
    n = int(d * SR); t = t_(n)
    s = np.sin(2 * np.pi * f * t) * 0.4 + np.sin(2 * np.pi * 2 * f * t) * 0.25
    if buzz:
        s += np.sign(np.sin(2 * np.pi * f * t)) * 0.08
    return s


def drone(d, f=55):
    n = int(d * SR); t = t_(n)
    s = sum(np.sin(2 * np.pi * f * m * t + m) * a for m, a in ((1, .5), (1.5, .25), (2.01, .2), (3, .08)))
    s *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t)
    return s + lp_fast(noise(n), 200) * 0.3


def heartbeat(d, bpm_from=110, bpm_to=40):
    n = int(d * SR); out = np.zeros(n); t = 0.0
    while t < d - 0.4:
        bpm = bpm_from + (bpm_to - bpm_from) * t / d
        for off, g in ((0, 1.0), (0.22, 0.7)):
            k = int((t + off) * SR); m = int(0.25 * SR)
            if k + m < n:
                tt = t_(m)
                out[k:k + m] += np.sin(2 * np.pi * (55 + 30 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 16) * g
        t += 60.0 / bpm
    return out


def fizz(d):
    n = int(d * SR); x = np.zeros(n)
    for _ in range(int(d * 140)):
        k = rng.integers(0, n - 2000); m = 1500
        f = rng.uniform(1500, 5000)
        x[k:k + m] += np.sin(2 * np.pi * f * t_(m)) * np.exp(-t_(m) * 120) * rng.uniform(0.1, 0.4)
    return x + hp_fast(noise(n), 5000) * 0.08


def creak(d):
    n = int(d * SR); t = t_(n)
    f = 180 + 80 * np.sin(2 * np.pi * 0.7 * t)
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.2
    return lp_fast(s, 1800) * np.sin(np.pi * t / d) ** 0.5


def fade(x, fi=0.3, fo=0.5):
    n = len(x); a, b = int(fi * SR), int(fo * SR)
    e = np.ones(n); e[:a] = np.linspace(0, 1, a); e[n - b:] = np.linspace(1, 0, b)
    return x * e


F = lambda fr: (fr - 1) / 24.0  # frame -> seconds

# ---- beds
add(fade(hum(F(152), 100, buzz=False) * 0.25 + lp_fast(noise(int(F(152) * SR)), 300) * 0.25, 0.05, 0.1), 0, 0.5)   # store/fridge
add(fade(drone(F(670) - F(224), 46), 0.5, 0.6), F(224), 0.45)                     # warehouse drone
add(fade(lp_fast(noise(int((F(670) - F(224)) * SR)), 500) * 0.35, 1, 1), F(224), 0.35)  # wind
add(fade(drone(DUR - F(670), 41), 0.3, 1.2), F(670), 0.4)
# ---- shot 1
add(clink(), F(31), 0.5, -0.3)
add(can_crack(), F(76), 0.9)
add(whoosh(0.35), F(97) - 0.2, 0.6)
add(whoosh(0.3), F(71) - 0.15, 0.5)
add(whoosh(0.3), F(46) - 0.15, 0.4)
# ---- sting
add(impact(2.0, 42), F(152), 1.0)
add(squeak(0.35, 3000), F(186), 0.55, 0.2)
add(squeak(0.25, 3900), F(186) + 0.3, 0.35, 0.2)
add(whoosh(0.6), F(224) - 0.35, 0.7)
# ---- warehouse / rat
add(scurry(F(369) - F(318)), F(318), 0.25, -0.4)
add(scurry(F(456) - F(370)), F(370), 0.6)
add(squeak(0.2), F(380), 0.45, 0.3)
add(squeak(0.16, 4200), F(458), 0.5, -0.1)
add(sniff(F(541) - F(458)), F(458), 0.6)
add(whoosh(0.3), F(471) - 0.15, 0.45)
add(whoosh(0.3), F(541) - 0.15, 0.45)
add(drip(), F(556), 1.0)
add(drip() * 0.4, F(560), 0.6)
# ---- UV
add(whoosh(0.35), F(601) - 0.2, 0.5)
add(clink() * 0.5, F(606), 0.6)
add(fade(hum(F(670) - F(606), 240) * 0.5, 0.4, 0.2), F(606), 0.25)
# ---- tab / bacteria
add(whoosh(0.4), F(670) - 0.25, 0.55)
add(creak(F(770) - F(705)), F(705), 0.5)
slow = can_crack(); slow = np.interp(np.arange(0, len(slow), 0.45), np.arange(len(slow)), slow)
add(lp_fast(slow, 2500), F(752), 0.9)
add(whoosh(0.5), F(781) - 0.3, 0.6)
add(lp_fast(fizz(F(906) - F(781)), 6000), F(781), 0.6)
for k in range(10):
    add(drip() * 0.3, F(805) + k * 0.12 + rng.uniform(0, 0.08), 0.5, rng.uniform(-0.5, 0.5))
# ---- sick / x-ray
add(impact(2.5, 36), F(906), 0.9)
add(heartbeat(DUR - F(906) - 0.6, 115, 45), F(906) + 0.1, 0.9)
add(whoosh(0.5), F(991) - 0.3, 0.6)
add(fade(hum(1.4, 1000, buzz=False) * 0.2, 0.01, 0.3), F(1036), 0.35)  # monitor tone at the end

mx = np.max(np.abs(bus))
bus = bus / mx * 0.7
out = os.path.join(ROOT, "audio", "sfx.wav")
os.makedirs(os.path.dirname(out), exist_ok=True)
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(bus[: int(DUR * SR)], -1, 1) * 32767).astype("<i2").tobytes())
print("wrote", out, f"{DUR:.2f}s")
