"""60 soniyalik kinematografik saundtrek: musiqa (D Hijoz maqomi), ovoz effektlari va o‘zbekcha diktor ovozi.
Faqat numpy kerak. Ishga tushirish (audio/ papkasida):  python3 make_audio.py
Natija: mix.wav (48 kHz, stereo). Keyin ffmpeg loudnorm bilan -14 LUFS ga keltiriladi.
"""
import json, subprocess, wave
import numpy as np

SR = 48000
DUR = 60.0
N = int(SR * DUR)
rng = np.random.default_rng(1)


def t_axis(n):
    return np.arange(n) / SR


def env_adsr(n, a, d, s, r):
    e = np.ones(n) * s
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na = min(na, n); e[:na] = np.linspace(0, 1, na)
    nd = min(nd, n - na); e[na:na + nd] = np.linspace(1, s, nd)
    if nr > 0 and nr < n: e[-nr:] *= np.linspace(1, 0, nr)
    return e


def fft_filter(x, fn):
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(x.shape[0], 1 / SR)
    g = fn(f)
    return np.fft.irfft(X * (g[:, None] if X.ndim == 2 else g), n=x.shape[0], axis=0)


def lp(f, fc, order=2):
    return 1 / np.sqrt(1 + (f / fc) ** (2 * order))


def hp(f, fc, order=2):
    return 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** (2 * order))


def bp(f, fc, q=2.0):
    return 1 / np.sqrt(1 + q * q * (f / fc - fc / np.maximum(f, 1e-3)) ** 2)


def stft_sweep(x, gain_fn):
    """Vaqt bo‘yicha o‘zgaruvchan filtr: gain_fn(freqs, t) -> gain."""
    n = 2048; hop = 512; win = np.hanning(n)
    out = np.zeros(len(x) + n); norm = np.zeros(len(x) + n)
    f = np.fft.rfftfreq(n, 1 / SR)
    xp = np.concatenate([x, np.zeros(n)])
    for i in range(0, len(x), hop):
        seg = xp[i:i + n] * win
        S = np.fft.rfft(seg) * gain_fn(f, i / SR)
        out[i:i + n] += np.fft.irfft(S, n=n) * win
        norm[i:i + n] += win ** 2
    return (out / np.maximum(norm, 1e-6))[:len(x)]


def pan(x, p):
    """p: -1 chap .. +1 o‘ng"""
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


MIX = {k: np.zeros((N, 2)) for k in ['music', 'perc', 'fx', 'amb', 'vo']}


def add(bus, sig, at, gain=1.0):
    i = int(at * SR)
    if i >= N: return
    if sig.ndim == 1: sig = pan(sig, 0)
    j = min(N, i + len(sig))
    if i < 0:
        sig = sig[-i:]; i = 0
    MIX[bus][i:j] += sig[:j - i] * gain


def note_hz(name):
    names = {'C': -9, 'C#': -8, 'Db': -8, 'D': -7, 'D#': -6, 'Eb': -6, 'E': -5, 'F': -4, 'F#': -3, 'Gb': -3, 'G': -2, 'G#': -1, 'Ab': -1, 'A': 0, 'A#': 1, 'Bb': 1, 'B': 2}
    n, o = name[:-1], int(name[-1])
    return 440 * 2 ** ((names[n] + (o - 4) * 12) / 12)


# ---------------------------------------------------------------- torli cholg‘ular (pad)
def string_pad(freq, dur, amp=1.0, bright=10, attack=1.5, release=2.0, vib=0.004):
    n = int(dur * SR); t = t_axis(n)
    out = np.zeros(n)
    for det in (-0.006, 0.0, 0.0065):
        ph_vib = vib * np.sin(2 * np.pi * (5.1 + det * 40) * t + rng.random() * 6)
        f0 = freq * (1 + det) * (1 + ph_vib)
        phase = 2 * np.pi * np.cumsum(f0) / SR
        for h in range(1, bright + 1):
            if freq * h > 9000: break
            out += np.sin(h * phase + rng.random() * 6) / h * (0.85 ** h)
    out *= env_adsr(n, attack, 0.5, 0.9, release) * amp / 3
    # sekin nafas (bow) modulyatsiyasi
    out *= 1 + 0.12 * np.sin(2 * np.pi * 0.23 * t + rng.random() * 6)
    return out


def chord(notes, at, dur, amp=0.12, spread=0.6, **kw):
    for k, nm in enumerate(notes):
        s = string_pad(note_hz(nm), dur, amp, **kw)
        add('music', pan(s, (k / max(1, len(notes) - 1) - .5) * 2 * spread), at)


# ---------------------------------------------------------------- ney (qamish nay)
def ney(notes, at, amp=0.16):
    """notes: [(nom, boshlanish, davomiylik)] — legato, portamento bilan."""
    if not notes: return
    total = max(s + d for _, s, d in notes) + 1.0
    n = int(total * SR); t = t_axis(n)
    f = np.zeros(n); e = np.zeros(n)
    for nm, s, d in notes:
        i0, i1 = int(s * SR), int((s + d) * SR)
        f[i0:] = note_hz(nm)
        seg = np.zeros(n); seg[i0:i1] = 1
        e = np.maximum(e, seg)
    # portamento va konvert silliqlash
    k = int(0.06 * SR); ker = np.ones(k) / k
    f = np.convolve(f, ker, mode='same'); f[f < 50] = note_hz(notes[0][0])
    k2 = int(0.18 * SR); e = np.convolve(e, np.ones(k2) / k2, mode='same')
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - notes[0][1]) / 1.5, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    tone = np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)
    breath = fft_filter(rng.standard_normal(n), lambda fr: bp(fr, 2200, 1.2)) * 0.35
    sig = (tone * 0.8 + breath * (0.5 + 0.5 * np.abs(np.sin(ph / 2)))) * e * amp
    add('music', pan(sig, -0.15), at)


# ---------------------------------------------------------------- ud / qonun (Karplus–Strong)
def pluck(freq, dur=2.2, amp=0.25, bright=0.5):
    n = int(dur * SR); L = int(SR / freq)
    buf = rng.uniform(-1, 1, L)
    buf = fft_filter(buf, lambda fr: lp(fr, 2000 + 6000 * bright, 1))
    out = np.zeros(n); pos = 0; prev = buf.copy()
    decay = 0.996
    while pos < n:
        blk = prev.copy(); take = min(L, n - pos)
        out[pos:pos + take] = blk[:take]
        nxt = 0.5 * (blk + np.roll(blk, -1)) * decay
        prev = nxt; pos += L
    out *= np.linspace(1, 0.0, n) ** 1.5
    body = fft_filter(out, lambda fr: 1 + 0.8 * bp(fr, 220, 3) + 0.5 * bp(fr, 900, 4))
    return body * amp


# ---------------------------------------------------------------- zarbli cholg‘ular
def boom(amp=1.0, f0=70, dur=3.5, sub=True):
    n = int(dur * SR); t = t_axis(n)
    f = f0 * (1 + 1.8 * np.exp(-t * 25))
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 1.6)
    click = fft_filter(rng.standard_normal(n), lambda fr: lp(fr, 1800, 2)) * np.exp(-t * 30) * 0.8
    s = body + click
    if sub: s += 0.6 * np.sin(2 * np.pi * 38 * t) * np.exp(-t * 1.2) * (1 - np.exp(-t * 80))
    return np.tanh(s * 1.4) * amp


def taiko(amp=0.8):
    n = int(1.6 * SR); t = t_axis(n)
    f = 95 * (1 + 0.9 * np.exp(-t * 30))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5)
    s += fft_filter(rng.standard_normal(n), lambda fr: bp(fr, 300, 1.5)) * np.exp(-t * 18) * 0.6
    return np.tanh(s * 1.3) * amp


def daf_dum(amp=0.5):
    n = int(0.6 * SR); t = t_axis(n)
    f = 85 * (1 + 0.7 * np.exp(-t * 40))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    jing = fft_filter(rng.standard_normal(n), lambda fr: bp(fr, 7000, 2.5)) * np.exp(-t * 14) * 0.35
    return (s + jing) * amp


def daf_tak(amp=0.3):
    n = int(0.35 * SR); t = t_axis(n)
    s = fft_filter(rng.standard_normal(n), lambda fr: bp(fr, 900, 1.8)) * np.exp(-t * 45)
    s += np.sin(2 * np.pi * 420 * t) * np.exp(-t * 60) * 0.5
    jing = fft_filter(rng.standard_normal(n), lambda fr: bp(fr, 8000, 3)) * np.exp(-t * 18) * 0.5
    return (s + jing) * amp


def shaker(amp=0.08):
    n = int(0.12 * SR); t = t_axis(n)
    return fft_filter(rng.standard_normal(n), lambda fr: hp(fr, 6000, 2)) * np.exp(-t * 40) * amp


# ---------------------------------------------------------------- effektlar
def whoosh(dur=1.0, amp=0.5, f_from=300, f_to=4000, rev=False):
    n = int(dur * SR); x = rng.standard_normal(n)
    def g(fr, tt):
        u = min(1, tt / dur)
        fc = f_from * (f_to / f_from) ** u
        return bp(fr, fc, 1.6)
    s = stft_sweep(x, g)
    e = np.sin(np.linspace(0, np.pi, n)) ** 2
    if rev: e = np.linspace(0, 1, n) ** 3
    return s * e * amp


def riser(dur=2.0, amp=0.35):
    n = int(dur * SR); t = t_axis(n)
    s = whoosh(dur, 1, 200, 6000, rev=True)
    tone = np.sin(2 * np.pi * np.cumsum(200 * 2 ** (3 * t / dur)) / SR) * (t / dur) ** 2 * 0.25
    return (s + tone) * amp


def shimmer(dur=3.0, density=12, amp=0.05, lo=2000, hi=6000, seed=3):
    r = np.random.default_rng(seed)
    n = int(dur * SR); out = np.zeros((n, 2))
    for _ in range(int(density * dur)):
        i = r.integers(0, n); f = r.uniform(lo, hi); L = int(0.5 * SR)
        tt = t_axis(L); s = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 9) * r.uniform(.3, 1)
        j = min(n, i + L); out[i:j] += pan(s[:j - i], r.uniform(-.8, .8))
    return out * amp


def wind(dur, amp=0.2):
    n = int(dur * SR); t = t_axis(n)
    x = rng.standard_normal(n)
    s = stft_sweep(x, lambda fr, tt: bp(fr, 500 + 350 * np.sin(tt * 1.7) + 200 * np.sin(tt * 3.1), 1.2))
    e = np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.8)
    return s * e * amp


def reverb(x, sec=3.2, wet=0.35, damp=3500, seed=9, predelay=0.02):
    r = np.random.default_rng(seed)
    n = int(sec * SR); t = t_axis(n)
    ir = np.zeros((n, 2))
    for c in range(2):
        noise = r.standard_normal(n) * np.exp(-t * 6.9 / sec)
        noise = stft_sweep(noise, lambda fr, tt: lp(fr, damp * np.exp(-tt * 0.6) + 400, 1))
        ir[:, c] = noise
    pd = int(predelay * SR); ir = np.concatenate([np.zeros((pd, 2)), ir])[:n]
    ir /= np.sqrt((ir ** 2).sum(axis=0))
    L = 1 << int(np.ceil(np.log2(len(x) + n)))
    out = np.zeros_like(x)
    for c in range(2):
        y = np.fft.irfft(np.fft.rfft(x[:, c], L) * np.fft.rfft(ir[:, c], L), L)[:len(x)]
        out[:, c] = y
    return x * (1 - wet) + out * wet * 3.0


# ================================================================ KOMPOZITSIYA
# --- Harmoniya (D Hijoz: D Eb F# G A Bb C) ---
# 1-sahna: zulmatdan nur
chord(['D2', 'A2'], 0.3, 7.2, amp=0.16, attack=3.5, release=2.5, bright=6)
chord(['D3', 'F#3', 'A3', 'D4'], 4.2, 6.2, amp=0.09, attack=2.5, release=1.2)
chord(['D2', 'A2', 'D3', 'F#3', 'A3', 'D4', 'F#4'], 7.0, 3.4, amp=0.1, attack=0.08, release=1.2)
ney([('A4', 1.2, 1.4), ('Bb4', 2.6, .5), ('A4', 3.1, .6), ('G4', 3.7, .5), ('F#4', 4.2, 1.0), ('Eb4', 5.2, .5), ('D4', 5.7, 1.3)], 0, amp=0.13)
# 2-sahna: tarqalish (daf ritmi bilan)
chord(['D2', 'D3', 'F#3', 'A3'], 10.0, 5.4, amp=0.1, attack=0.6)
chord(['C2', 'C3', 'Eb3', 'G3'], 15.0, 5.4, amp=0.1, attack=0.8)
# 3-sahna: kutubxona — yumshoq, ud arpedjiolari
chord(['G2', 'G3', 'Bb3', 'D4'], 20.0, 5.4, amp=0.085, attack=1.2)
chord(['Eb2', 'Eb3', 'G3', 'Bb3'], 25.0, 5.4, amp=0.085, attack=1.2)
# 4-sahna: me’morchilik — kuchli
chord(['D2', 'A2', 'D3', 'F#3', 'A3', 'D4'], 30.0, 5.2, amp=0.1, attack=0.3)
chord(['C2', 'G2', 'C3', 'Eb3', 'G3', 'C4'], 35.0, 5.2, amp=0.1, attack=0.4)
# 5-sahna: ilm merosi
chord(['G2', 'D3', 'G3', 'Bb3', 'D4'], 40.0, 5.4, amp=0.09, attack=0.8)
chord(['Eb2', 'Bb2', 'Eb3', 'G3', 'Bb3', 'Eb4'], 45.0, 5.2, amp=0.1, attack=0.8)
# 6-sahna: final
chord(['D2', 'A2', 'D3', 'F#3', 'A3', 'D4', 'F#4', 'A4'], 50.0, 9.8, amp=0.095, attack=1.0, release=3.5)
chord(['D1', 'D2'], 50.0, 9.8, amp=0.14, attack=1.0, release=3.5, bright=5)
ney([('A4', 50.6, .9), ('Bb4', 51.5, .4), ('C5', 51.9, .6), ('Bb4', 52.5, .4), ('A4', 52.9, 1.2), ('G4', 54.2, .5), ('A4', 54.7, .5), ('D5', 55.3, 1.6), ('C5', 56.9, .4), ('Bb4', 57.3, .5), ('A4', 57.8, 1.8)], 0, amp=0.12)

# --- ud arpedjiolari (Hijoz) ---
ud_notes = ['D3', 'F#3', 'A3', 'D4', 'Eb4', 'D4', 'A3', 'F#3']
for k in range(28):
    tt = 20.2 + k * 0.34
    if tt > 29.6: break
    nm = ud_notes[k % 8] if tt < 25 else ['Eb3', 'G3', 'Bb3', 'Eb4', 'D4', 'Bb3', 'G3', 'F#3'][k % 8]
    add('music', pan(pluck(note_hz(nm), 1.8, 0.16, 0.45), 0.35), tt)
for k in range(26):
    tt = 40.3 + k * 0.36
    if tt > 49.6: break
    nm = ['G3', 'Bb3', 'D4', 'G4', 'A4', 'G4', 'D4', 'Bb3'][k % 8] if tt < 45 else ['Eb3', 'G3', 'Bb3', 'Eb4', 'F#4', 'Eb4', 'Bb3', 'G3'][k % 8]
    add('music', pan(pluck(note_hz(nm), 1.6, 0.13, 0.6), -0.3), tt)

# --- bass drone ---
for at, nm, d in [(10, 'D1', 5.2), (15, 'C1', 5.2), (20, 'G1', 5.2), (25, 'Eb1', 5.2), (30, 'D1', 5.2), (35, 'C1', 5.2), (40, 'G1', 5.2), (45, 'Eb1', 5.2)]:
    n = int(d * SR); tt = t_axis(n); f = note_hz(nm)
    s = (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(4 * np.pi * f * tt)) * env_adsr(n, 0.3, .2, .9, 0.8) * 0.16
    add('music', s, at)

# --- daf ritmi (maqsum: D T . T D . T .) 96 BPM ---
BEAT = 60 / 96 / 2
pattern = [('D', 1.0), ('T', .7), (None, 0), ('T', .6), ('D', .9), (None, 0), ('T', .7), (None, 0)]
def groove(t0, t1, level):
    k = 0; tt = t0
    while tt < t1:
        kind, v = pattern[k % 8]
        if kind == 'D': add('perc', pan(daf_dum(0.42 * v * level), -0.1), tt)
        if kind == 'T': add('perc', pan(daf_tak(0.26 * v * level), 0.25), tt)
        add('perc', pan(shaker(0.05 * level * (1.2 if k % 2 else .6)), 0.5), tt + BEAT * .5)
        k += 1; tt += BEAT
groove(12.4, 19.6, 0.8)
groove(20.0, 29.4, 0.35)
groove(30.0, 39.5, 1.0)
groove(40.0, 49.4, 0.7)
groove(50.0, 54.8, 0.55)

# --- zarbalar ---
for at, a in [(0.05, .35), (7.02, 1.0), (10.0, .55), (20.0, .5), (30.0, .7), (33.4, .45), (36.7, .45), (40.0, .55), (50.0, .6), (55.05, .95), (57.25, .7)]:
    add('fx', boom(a), at)
for at in [7.02, 30.0, 55.05]:
    add('perc', taiko(0.5), at); add('perc', taiko(0.35), at + 0.18)
for at in [9.0, 18.9, 29.0, 39.0, 48.9]:
    add('perc', taiko(0.22), at); add('perc', taiko(0.28), at + 0.31); add('perc', taiko(0.36), at + 0.62)

# --- risers / whooshes ---
for at in [5.0, 8.2, 18.2, 28.3, 38.2, 48.2, 53.6]:
    r = riser(1.8 if at not in (5.0, 53.6) else 2.0, 0.3)
    add('fx', pan(r, 0), at)
for at, d in [(10.0, .9), (12.2, .8), (18.3, .7), (20.0, .9), (23.4, .7), (30.0, .9), (33.4, .7), (36.7, .7), (40.0, .9), (43.0, .7), (46.4, .7), (50.0, 1.0)]:
    w = whoosh(d, 0.35, 250, 5000)
    add('fx', np.stack([w, np.roll(w, 400)], 1), at - d * .45)
# usturlob / qo‘lyozma: yengil metall va qog‘oz shitirlashi
add('fx', pan(whoosh(0.6, 0.12, 3000, 7000), .3), 23.6)  # varaq aylanishi

# --- ambient ---
add('amb', pan(wind(3.0, 0.22), 0), 10.0)
add('amb', pan(wind(10.0, 0.06), 0), 50.0)
add('amb', shimmer(7.0, 10, 0.05), 0.5)
add('amb', shimmer(3.0, 18, 0.06, seed=5), 55.0)
add('amb', shimmer(4.0, 12, 0.05, seed=7), 46.0)
add('amb', shimmer(3.0, 8, 0.04, seed=8), 20.0)
n = int(10 * SR); room = fft_filter(rng.standard_normal(n), lambda f: lp(f, 400, 2)) * 0.02
add('amb', pan(room, 0), 20.0)

# ================================================================ DIKTOR OVOZI
def load_wav(path):
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return a

segs = json.load(open('vo_matn.json'))
for s in segs:
    v = load_wav(f"vo/{s['id']}.wav")
    # EQ: past chastotada iliqlik, 3 kHz da aniqlik, 80 Hz dan past kesish
    v = fft_filter(v, lambda f: hp(f, 80, 2) * (1 + 0.35 * bp(f, 160, 1.2) + 0.25 * bp(f, 3200, 1.0)))
    # yumshoq kompressiya
    v = np.tanh(v * 2.2) / np.tanh(2.2)
    add('vo', pan(v, 0), s['start'])
MIX['vo'] = reverb(MIX['vo'], 1.2, 0.10, 4000, predelay=0.01)

# ================================================================ MIKSHER
music = reverb(MIX['music'], 3.6, 0.38)
perc = reverb(MIX['perc'], 2.2, 0.22, 5000)
fx = reverb(MIX['fx'], 2.8, 0.25)
amb = MIX['amb']
vo = MIX['vo']
# diktor ovozi ostida musiqani pasaytirish (sidechain)
lvl = np.abs(vo).max(axis=1)
k = int(0.25 * SR); envv = np.convolve(lvl, np.ones(k) / k, mode='same')
envv = envv / (envv.max() + 1e-9)
duck = 1 - 0.62 * np.clip(envv * 4, 0, 1)
duck = np.convolve(duck, np.ones(k) / k, mode='same')[:, None]
bed = (music * 0.95 + perc * 0.85 + amb * 0.9) * duck + fx * 0.75
mix = bed * 0.8 + vo * 2.2
# yakuniy so‘nish (60 s)
tt = t_axis(N); mix *= np.clip((60 - tt) / 0.9, 0, 1)[:, None]
mix *= np.clip(tt / 0.05, 0, 1)[:, None]
mix = mix / (np.abs(mix).max() + 1e-9) * 0.98
mix = np.tanh(mix * 1.5) / np.tanh(1.5)
pcm = (mix * 32767 * 0.95).astype(np.int16)
with wave.open('mix.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('mix.wav tayyor')
# nazorat: diktor ovozi va fon nisbati (ovoz faol joylarda)
act = envv > 0.15
if act.any():
    r_vo = np.sqrt(((vo * 2.2)[act] ** 2).mean()); r_bed = np.sqrt(((bed * 0.8)[act] ** 2).mean())
    print(f'ovoz/fon nisbati: {20 * np.log10(r_vo / r_bed):.1f} dB')
