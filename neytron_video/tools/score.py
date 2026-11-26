"""Original cinematic underscore, synthesized from scratch (no third-party music).

Usage: python3 score.py events.json narration.wav out_mix.wav
events.json: {"total": sec, "offset": sec, "hits": [t], "whooshes": [t], "tense": [[a, b]]}
Times are in narration seconds; `offset` shifts them onto the video timeline.
"""
import json, sys, wave
import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def read_wav(path):
    w = wave.open(path)
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if w.getnchannels() == 2:
        a = a.reshape(-1, 2).mean(1)
    assert w.getframerate() == SR
    return a


def onepole_lp(x, fc):
    """One-pole low-pass, applied as FFT convolution with its (truncated) impulse response."""
    a = np.exp(-2 * np.pi * fc / SR)
    n = int(SR * 5 / fc) + 1
    k = (1 - a) * a ** np.arange(n)
    return fft_conv(x, k)


def fft_conv(x, k):
    n = len(x) + len(k) - 1
    N = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(k, N), N)[: len(x)]
    return y.astype(np.float32)


def env_follow(x, ms=300):
    n = int(SR * ms / 1000)
    k = np.ones(n, np.float32) / n
    return fft_conv(np.abs(x), k)


def main():
    ev = json.load(open(sys.argv[1]))
    voice = read_wav(sys.argv[2])
    total = ev["total"]
    off = ev.get("offset", 0.0)
    N = int(total * SR)
    t = np.arange(N, dtype=np.float32) / SR
    L = np.zeros(N, np.float32)
    R = np.zeros(N, np.float32)

    # --- harmonic pad: D minor progression, slow crossfades, detuned partials
    D2 = 73.42
    chords = [
        [D2, D2 * 1.5, D2 * 2, D2 * 2.378],  # Dm
        [D2 * 0.891, D2 * 1.335, D2 * 1.782, D2 * 2.245],  # Bb
        [D2 * 0.749, D2 * 1.122, D2 * 1.498, D2 * 1.782],  # Gm
        [D2 * 1.0, D2 * 1.498, D2 * 1.888, D2 * 2.245],  # Dm(add) / A-ish colour
    ]
    seg = 16.0
    nseg = int(np.ceil(total / seg)) + 1
    for ci in range(nseg):
        ch = chords[ci % len(chords)]
        a0 = ci * seg - 4
        a1 = a0 + seg + 8
        m = (t >= max(0, a0)) & (t < a1)
        if not m.any():
            continue
        tt = t[m]
        w = np.clip((tt - a0) / 4, 0, 1) * np.clip((a1 - tt) / 4, 0, 1)
        w = np.sin(w * np.pi / 2) ** 2
        for j, f in enumerate(ch):
            for det, pan in ((-0.6, 0.2), (0.6, 0.8)):
                ph = rng.uniform(0, 2 * np.pi)
                lfo = 0.75 + 0.25 * np.sin(2 * np.pi * (0.05 + 0.02 * j) * tt + ph)
                s = (np.sin(2 * np.pi * (f + det) * tt + ph) + 0.25 * np.sin(2 * np.pi * 2 * (f + det) * tt)) * lfo * w
                amp = 0.05 / (1 + j * 0.6)
                L[m] += s * amp * (1 - pan)
                R[m] += s * amp * pan

    # --- air: filtered noise bed
    air = rng.standard_normal(N).astype(np.float32)
    air = onepole_lp(air, 900) - onepole_lp(air, 200)
    air *= 0.05 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.03 * t))
    L += air
    R += np.roll(air, 2400)

    # --- tension pulse (heartbeat-like sub), only in tense sections
    for a, b in ev.get("tense", []):
        a += off
        b += off
        beat = 60 / 72
        k = a
        while k < b:
            for dt, g in ((0, 1.0), (0.28, 0.6)):
                s0 = int((k + dt) * SR)
                n = int(0.35 * SR)
                if s0 + n >= N:
                    continue
                tt = np.arange(n) / SR
                fade = min(1, (k - a) / 3, (b - k) / 3)
                hit = np.sin(2 * np.pi * (55 - 25 * tt) * tt) * np.exp(-tt * 14) * 0.32 * g * fade
                L[s0 : s0 + n] += hit
                R[s0 : s0 + n] += hit
            k += beat

    # --- impacts
    for h in ev.get("hits", []):
        s0 = int((h + off) * SR)
        n = int(2.5 * SR)
        if s0 + n >= N or s0 < 0:
            continue
        tt = np.arange(n) / SR
        boom = np.sin(2 * np.pi * (48 * np.exp(-tt * 1.5) + 28) * tt) * np.exp(-tt * 2.2) * 0.55
        crack = rng.standard_normal(n) * np.exp(-tt * 18) * 0.08
        L[s0 : s0 + n] += boom + crack
        R[s0 : s0 + n] += boom + crack

    # --- whooshes (rising filtered noise into the cut)
    for wt in ev.get("whooshes", []):
        n = int(0.9 * SR)
        s0 = int((wt + off) * SR) - int(0.6 * SR)
        if s0 < 0 or s0 + n >= N:
            continue
        nz = rng.standard_normal(n).astype(np.float32)
        tt = np.arange(n) / SR
        shape = np.sin(np.clip(tt / 0.9, 0, 1) * np.pi) ** 2
        band = onepole_lp(nz, 2500) - onepole_lp(nz, 400)
        g = band * shape * 0.11
        pan = np.linspace(0.2, 0.8, n)
        L[s0 : s0 + n] += g * (1 - pan)
        R[s0 : s0 + n] += g * pan

    # --- duck music under the voice (sidechain)
    v = np.zeros(N, np.float32)
    vs = int(off * SR)
    v[vs : vs + len(voice)] = voice[: max(0, N - vs)]
    e = env_follow(v, 250)
    e = e / (e.max() + 1e-9)
    duck = 1 - 0.55 * np.clip(e * 6, 0, 1)
    music_gain = 10 ** (-6 / 20)  # bed sits ~18 dB below the narration
    L *= duck * music_gain
    R *= duck * music_gain

    # fade in/out
    fi = np.clip(t / 2.0, 0, 1)
    fo = np.clip((total - t) / 4.0, 0, 1)
    L *= fi * fo
    R *= fi * fo

    vg = 10 ** (-0.9 / 20)  # mono voice on both channels → trim to ~-14 LUFS master
    outL = L + v * vg
    outR = R + v * vg
    peak = max(np.abs(outL).max(), np.abs(outR).max())
    if peak > 0.97:
        outL /= peak / 0.97
        outR /= peak / 0.97
    st = np.stack([outL, outR], 1)
    w = wave.open(sys.argv[3], "wb")
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
    w.close()
    print("wrote", sys.argv[3], f"{total:.1f}s")


if __name__ == "__main__":
    main()
