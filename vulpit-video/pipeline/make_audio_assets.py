"""Procedurally synthesizes an ORIGINAL cinematic score + SFX (no third-party samples -> no licensing issues).
usage: python make_audio_assets.py music_plan.json out_dir"""
import sys, json, numpy as np
from scipy.signal import fftconvolve, butter, sosfilt
from scipy.io import wavfile
SR = 44100
rng = np.random.default_rng(7)
plan = json.load(open(sys.argv[1])); out = sys.argv[2]

def save(name, x):
    x = np.asarray(x, np.float32)
    if x.ndim == 1: x = np.stack([x, x], 1)
    pk = np.abs(x).max() + 1e-9
    x = x / pk * 0.89
    wavfile.write(f"{out}/{name}.wav", SR, (x * 32767).astype(np.int16))

def lp(x, f, order=2): return sosfilt(butter(order, f, 'low', fs=SR, output='sos'), x, axis=0)
def hp(x, f, order=2): return sosfilt(butter(order, f, 'high', fs=SR, output='sos'), x, axis=0)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x, axis=0)
def env(n, a, r): t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r)
def ir(sec=3.2, decay=1.1):
    n = int(sec * SR); t = np.arange(n) / SR
    e = np.exp(-t * 6.9 / (decay * sec / 1.1 * 2.2))
    l = rng.standard_normal(n) * e; r = rng.standard_normal(n) * e
    l = lp(l, 6000); r = lp(r, 6000); l[:200] *= np.linspace(0, 1, 200); r[:200] *= np.linspace(0, 1, 200)
    return l / np.abs(l).sum() * 40, r / np.abs(r).sum() * 40
IRL, IRR = ir()
def reverb(x, wet=0.35):
    if x.ndim == 1: x = np.stack([x, x], 1)
    l = fftconvolve(x[:, 0], IRL)[:len(x)]; r = fftconvolve(x[:, 1], IRR)[:len(x)]
    return x * (1 - wet) + np.stack([l, r], 1) * wet

# ---------------- SFX ----------------
def sfx_boom():
    n = int(3.5 * SR); t = np.arange(n) / SR
    f = 30 + 70 * np.exp(-t * 9)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    click = lp(rng.standard_normal(n), 1800) * np.exp(-t * 30) * 0.6
    tail = lp(rng.standard_normal(n), 300) * np.exp(-t * 2.2) * 0.25
    return reverb(np.tanh(1.6 * (body + click + tail)), 0.3)
def sfx_whoosh(d=1.1, rev=False):
    n = int(d * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n); x = np.zeros(n)
    # sweeping band via block filtering
    blk = 1024
    for i in range(0, n, blk):
        p = i / n; fc = 300 + 3500 * np.sin(np.pi * p) ** 2
        x[i:i + blk] = bp(noise[i:i + blk], fc * 0.6, min(fc * 1.6, 18000))
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    x = x * e
    if rev: x = x[::-1]
    pan = np.linspace(-0.6, 0.6, n)
    return reverb(np.stack([x * (1 - pan) / 2, x * (1 + pan) / 2], 1), 0.25)
def sfx_riser(d=3.0):
    n = int(d * SR); t = np.arange(n) / SR
    f = 120 * (2 ** (t / d * 3))
    tone = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in (1, 1.5, 2.01))
    noise = hp(rng.standard_normal(n), 2000) * 0.5
    e = (t / d) ** 2.2
    x = (tone * 0.5 + noise) * e
    x[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))
    return reverb(x, 0.4)
def sfx_shimmer():
    n = int(4 * SR); t = np.arange(n) / SR; x = np.zeros(n)
    notes = [587.33, 880, 1174.66, 1318.5, 1760, 2349.3]
    for i, f in enumerate(notes):
        st = int(i * 0.07 * SR); m = n - st
        tt = np.arange(m) / SR
        x[st:] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.76 * tt)) * env(m, 0.005, 1.4) / (1 + i * 0.25)
    return reverb(x, 0.55)
def bell(f0, d=6.0):
    n = int(d * SR); t = np.arange(n) / SR
    partials = [(0.5, 1.0, 3.5), (1, 0.8, 2.6), (1.19, 0.5, 2.0), (1.5, 0.45, 1.6), (2, 0.4, 1.3), (2.51, 0.25, 0.9), (3.0, 0.2, 0.7), (4.07, 0.12, 0.5)]
    x = sum(a * np.sin(2 * np.pi * f0 * r * t + rng.uniform(0, 6)) * np.exp(-t / dd) for r, a, dd in partials)
    x *= np.minimum(1, t / 0.003)
    return x
def sfx_bells():
    n = int(9 * SR); x = np.zeros(n)
    for st, f in [(0, 392), (1.4, 329.6), (2.8, 392), (4.2, 293.7)]:
        b = bell(f); s = int(st * SR); x[s:s + len(b)] += b[:n - s] * 0.6
    return reverb(lp(x, 7000), 0.5)
def sfx_heartbeat():
    n = int(1.2 * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for st, a in [(0, 1), (0.28, 0.7)]:
        s = int(st * SR); tt = t[:n - s]
        x[s:] += a * np.sin(2 * np.pi * (45 + 25 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 14)
    return np.tanh(2 * x)
def sfx_tick():
    n = int(0.25 * SR); t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 3000) * np.exp(-t * 90) + 0.5 * np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 60)
def sfx_flash():   # bright light bloom: airy noise swell + high chord
    n = int(3 * SR); t = np.arange(n) / SR
    air = hp(rng.standard_normal(n), 4000) * np.exp(-t * 1.5) * np.minimum(1, t / 0.05)
    ch = sum(np.sin(2 * np.pi * f * t) for f in (1174.7, 1480, 1760, 2217)) * np.exp(-t * 1.2) * 0.25
    return reverb(air * 0.5 + ch, 0.6)
def sfx_subdrop():
    n = int(2.5 * SR); t = np.arange(n) / SR
    f = 80 * np.exp(-t * 1.2) + 25
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.3) * np.minimum(1, t / 0.01)

for name, fn in [("boom", sfx_boom), ("whoosh", sfx_whoosh), ("whoosh_rev", lambda: sfx_whoosh(1.0, True)), ("riser", sfx_riser),
                 ("shimmer", sfx_shimmer), ("bells", sfx_bells), ("heartbeat", sfx_heartbeat), ("tick", sfx_tick),
                 ("flash", sfx_flash), ("subdrop", sfx_subdrop)]:
    save(name, fn())

# ---------------- MUSIC ----------------
dur = plan["duration"]; N = int(dur * SR); t = np.arange(N) / SR
def midi(m): return 440 * 2 ** ((m - 69) / 12)
# chord voicings (midi) in D minor world
CH = {"Dm": [50, 57, 62, 65, 69], "Bb": [46, 58, 62, 65, 70], "F": [41, 57, 60, 65, 69], "C": [48, 55, 60, 64, 67],
      "Gm": [43, 58, 62, 67, 70], "A": [45, 57, 61, 64, 69], "Am": [45, 57, 60, 64, 69], "Dsus": [50, 57, 62, 64, 69],
      "Ebmaj": [51, 58, 63, 67, 70], "Fmaj7": [41, 57, 60, 64, 69], "Bbmaj7": [46, 57, 62, 65, 69]}
# per-sample parameter curves from plan sections (smoothly interpolated)
def curve(key, default=0.0):
    pts = []
    for s in plan["sections"]:
        pts.append((s["start"], s.get(key, default)))
        pts.append((s["end"] - 0.01, s.get(key, default)))
    xs = np.array([p[0] for p in pts]); ys = np.array([p[1] for p in pts])
    c = np.interp(t, xs, ys)
    k = int(2.5 * SR); kern = np.hanning(k); kern /= kern.sum()   # ~2.5s crossfades between sections
    return fftconvolve(c, kern, mode="same")
pad_lvl, bright, pulse_lvl, bell_lvl, drone_lvl = curve("pad"), curve("bright", 0.3), curve("pulse"), curve("bells"), curve("drone", 0.5)

# chord timeline
chord_seq = []
for s in plan["sections"]:
    prog = s["chords"]; cl = s.get("chordLen", 8.0); tt = s["start"]; i = 0
    while tt < s["end"]:
        chord_seq.append((tt, min(s["end"], tt + cl), prog[i % len(prog)])); tt += cl; i += 1
pad = np.zeros(N)
for (a, b, name) in chord_seq:
    s0 = int(a * SR); s1 = min(N, int((b + 2.0) * SR)); m = s1 - s0
    tt = np.arange(m) / SR
    e = np.minimum(1, tt / 1.8) * np.clip((b + 2.0 - a - tt) / 2.0, 0, 1)
    x = np.zeros(m)
    for note in CH[name]:
        f = midi(note)
        for det in (-0.12, 0.0, 0.11):
            ph = rng.uniform(0, 2 * np.pi)
            ff = f * 2 ** (det / 12)
            # soft saw-ish: few harmonics
            x += sum(np.sin(2 * np.pi * ff * h * tt + ph * h) / h ** 1.6 for h in (1, 2, 3, 4)) / 3
    pad[s0:s1] += x * e / len(CH[name])
# brightness-controlled filtering: blend dark & bright versions
pad_dark = lp(pad, 700); pad_br = lp(pad, 2600)
padm = (pad_dark * (1 - bright) + pad_br * bright) * pad_lvl
# drone
drone = (np.sin(2 * np.pi * midi(38) * t) + 0.5 * np.sin(2 * np.pi * midi(45) * t + 1) + 0.3 * np.sin(2 * np.pi * midi(26) * t)) * (0.7 + 0.3 * np.sin(2 * np.pi * t / 11))
drone = lp(drone, 400) * drone_lvl * 0.6
# pulse: low heartbeat-like thumps (BPM from section)
pulse = np.zeros(N); hb = sfx_heartbeat()
tt = 0.0
while tt < dur:
    bpm = 64
    for s in plan["sections"]:
        if s["start"] <= tt < s["end"]: bpm = s.get("bpm", 64)
    s0 = int(tt * SR); L = min(len(hb), N - s0); pulse[s0:s0 + L] += hb[:L]
    tt += 60 / bpm
pulse = lp(pulse, 200) * pulse_lvl
# bells / celesta arpeggio (sparse, tonal to current chord)
bl = np.zeros(N); tt = 0.5
cel_cache = {}
def cel(f):
    if f not in cel_cache:
        n = int(2.5 * SR); x = np.arange(n) / SR
        cel_cache[f] = (np.sin(2 * np.pi * f * x) + 0.25 * np.sin(2 * np.pi * f * 3.01 * x)) * np.exp(-x * 2.2) * np.minimum(1, x / 0.004)
    return cel_cache[f]
ci = 0
while tt < dur - 3:
    name = "Dm"
    for (a, b, nm) in chord_seq:
        if a <= tt < b: name = nm
    notes = CH[name][1:]
    f = midi(notes[ci % len(notes)] + 12 + (12 if ci % 7 == 3 else 0)); ci += 1
    s0 = int(tt * SR); c = cel(f); L = min(len(c), N - s0); bl[s0:s0 + L] += c[:L] * 0.25
    tt += 0.75 if ci % 4 else 1.5
bl = bl * bell_lvl
mix = np.stack([padm + drone + pulse * 0.9, padm + drone + pulse * 0.9], 1)
blst = np.stack([bl * 0.7, bl * 1.0], 1)
mix = reverb(mix, 0.3) + reverb(blst, 0.6)
# master fade in/out
fade = np.ones(N); fi = int(plan.get("fadeIn", 0.5) * SR); fo = int(plan.get("fadeOut", 6) * SR)
fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo) ** 1.5
mix = mix * fade[:, None]
mix = hp(mix, 30)
save("music", mix)
print("ok", dur, len(chord_seq), "chords")
