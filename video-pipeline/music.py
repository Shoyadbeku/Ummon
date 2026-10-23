# Procedural cinematic ambient score (royalty-free, generated here)
import numpy as np, wave, sys
SR = 44100
dur = float(sys.argv[1]); out = sys.argv[2]
n = int(SR * dur); t = np.arange(n) / SR
rng = np.random.default_rng(7)
def note(m): return 440 * 2 ** ((m - 69) / 12)
# i - VI - III - VII in D minor, 8 s per chord
prog = [[50, 53, 57, 62], [46, 50, 53, 58], [53, 57, 60, 65], [48, 52, 55, 60]]
L = 8.0
mix = np.zeros(n)
def env_chord(idx_t):
    pass
for k in range(int(dur // L) + 2):
    start = k * L; chord = prog[k % 4]
    s0 = int(max(0, (start - 1.5)) * SR); s1 = min(n, int((start + L + 1.5) * SR))
    if s0 >= n: break
    tt = t[s0:s1]; local = tt - (start - 1.5)
    env = np.clip(local / 2.5, 0, 1) * np.clip((L + 3 - local) / 2.5, 0, 1)
    env = env ** 1.5
    for j, m in enumerate(chord):
        f = note(m)
        for det in (-0.12, 0.0, 0.13):  # detuned saw-ish pad (sum of few harmonics)
            ff = f * 2 ** (det / 12)
            ph = rng.random() * 6.28
            w = sum(np.sin(2 * np.pi * ff * h * tt + ph * h) / h ** 1.6 for h in range(1, 5))
            mix[s0:s1] += 0.035 * env * w
    # bass root
    fb = note(chord[0] - 12)
    mix[s0:s1] += 0.12 * env * np.sin(2 * np.pi * fb * tt)
# low drone D
mix += 0.06 * np.sin(2 * np.pi * note(38) * t) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.05 * t))
# soft heartbeat pulse (two thumps every 2 s)
pulse = np.zeros(n)
def thump(at, amp):
    i0 = int(at * SR); ln = int(0.35 * SR)
    if i0 + ln > n: return
    tt = np.arange(ln) / SR
    pulse[i0:i0 + ln] += amp * np.sin(2 * np.pi * (55 - 25 * tt) * tt) * np.exp(-tt * 14)
for b in np.arange(0, dur - 1, 2.0):
    thump(b, 0.5); thump(b + 0.28, 0.3)
# pulse strongest in hook, fades after, returns for the climax region
pulse_env = np.interp(t, [0, 30, 45, dur * 0.62, dur * 0.66, dur * 0.80, dur * 0.85, dur], [1, 1, 0.25, 0.25, 0.8, 0.8, 0.15, 0.1])
mix += pulse * pulse_env
# airy shimmer: filtered noise
noise = rng.standard_normal(n)
k = np.ones(400) / 400
air = noise - np.convolve(noise, k, mode="same")
mix += 0.004 * air * (0.6 + 0.4 * np.sin(2 * np.pi * 0.03 * t))
# global fade in/out
g = np.clip(t / 3, 0, 1) * np.clip((dur - t) / 6, 0, 1)
mix *= g
mix /= np.max(np.abs(mix)) * 1.1
st = np.stack([mix, np.roll(mix, int(0.012 * SR))], 1)
w = wave.open(out, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((st * 32767).astype(np.int16).tobytes()); w.close()
