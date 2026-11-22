"""Audio mix: cleaned voice + ducked music bed + sound effects -> public/audio/final_mix.wav
Run from the project root:  python3 scripts/mix.py
"""
import re, subprocess, numpy as np

SR = 48000
ROOT = '.'

def load(path, ch=2):
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path, '-f', 'f32le', '-ac', str(ch), '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.float32).copy()
    return a.reshape(-1, ch)

def db(x): return 10 ** (x / 20)

voice = load(f'{ROOT}/public/audio/voice_clean.wav', 1)[:, 0]
N = len(voice) + SR  # one second tail
out_v = np.zeros(N, np.float32); out_v[:len(voice)] = voice

# ---------------- music plan (start, end, file, measured LUFS, offset into track) ----------------
PLAN = [
    (0.0, 84.2, '283', -13.2, 0),     # Trapanomics — dark hip-hop hook
    (84.2, 169.3, '612', -11.2, 0),   # Selpan — drone, Dundee/DMA story
    (169.3, 243.1, '140', -10.8, 0),  # Cyberpunk City — synth, GTA III / Vice City
    (243.1, 311.3, '399', -13.8, 0),  # Billy the Kid — hip-hop, San Andreas
    (311.3, 430.4, '598', -11.2, 10), # We Will Get It — film score, GTA IV / V
    (430.4, 514.5, '605', -9.1, 20),  # Delirium — tension, leak / trailer
    (514.5, 610.3, '370', -16.3, 0),  # Sparta — trap, release dates / complexity
    (610.3, 709.06, '678', -17.3, 0), # Epical Drums 03 — finale
]
music = np.zeros((N, 2), np.float32)
XF = 1.5
for (s, e, f, lufs, off) in PLAN:
    tr = load(f'{ROOT}/public/music/{f}.mp3', 2) * db(-16 - lufs)
    tr = tr[int(off * SR):]
    need = int((e - s + XF) * SR)
    while len(tr) < need:  # loop with short crossfade
        x = int(2 * SR); a = tr[-x:] * np.linspace(1, 0, x)[:, None]; b = tr[:x] * np.linspace(0, 1, x)[:, None]
        tr = np.concatenate([tr[:-x], a + b, tr[x:]])
    seg = tr[:need].copy()
    fi = int(XF * SR)
    seg[:fi] *= np.linspace(0, 1, fi)[:, None] if s > 0 else 1
    seg[-fi:] *= np.linspace(1, 0, fi)[:, None]
    i0 = int(max(0, s - XF / 2) * SR)
    music[i0:i0 + len(seg)] += seg[:max(0, N - i0)]

# ---------------- ducking envelope from voice ----------------
win = int(0.05 * SR)
env = np.sqrt(np.convolve(out_v ** 2, np.ones(win) / win, mode='same'))
active = (env > db(-38)).astype(np.float32)
# attack 40ms / release 450ms smoothing
g = np.zeros_like(active); a_c = np.exp(-1 / (0.04 * SR)); r_c = np.exp(-1 / (0.45 * SR))
# vectorised-ish: process in blocks of 48 samples
blk = 48; ab = active[: len(active) // blk * blk].reshape(-1, blk).max(1)
gb = np.zeros_like(ab); prev = 0.0
for i, x in enumerate(ab):
    c = a_c ** blk if x > prev else r_c ** blk
    prev = x + (prev - x) * c; gb[i] = prev
g = np.repeat(gb, blk); g = np.pad(g, (0, N - len(g)), 'edge')
duck_db = -13.0 * g + -7.0 * (1 - g)  # music under voice -13 dB, in gaps -7 dB (relative to -16 LUFS)
music *= db(duck_db)[:, None]
# fade music in over the first 0.3s (hook starts hard), out over the last 3s
end = int(709.06 * SR); fo = int(3 * SR)
music[end - fo:end] *= np.linspace(1, 0, fo)[:, None]; music[end:] = 0

# ---------------- sound effects from storyboard ----------------
src = open(f'{ROOT}/src/storyboard.tsx', encoding='utf8').read()
cues = []
for line in src.splitlines():
    m = re.search(r"\{t: ([\d.]+),", line); sm = re.search(r"sfx: \[([^\]]*)\]", line)
    if m and sm:
        for name in re.findall(r"'(\w+)'", sm.group(1)):
            cues.append((float(m.group(1)), name))
GAIN = {'whoosh': -17, 'sweep': -17, 'impact': -11, 'bass': -10, 'riser': -15, 'glitch': -19, 'type': -18, 'typing': -22,
        'siren': -22, 'car': -17, 'coin': -15, 'money': -14, 'ding': -17, 'shutter': -15, 'heartbeat': -12, 'orch': -15,
        'pixel': -18, 'news': -16}
PRE = {'whoosh': 0.22, 'sweep': 0.15}
sfx = np.zeros((N, 2), np.float32); cache = {}
for t, name in cues:
    if name not in cache:
        x = load(f'{ROOT}/public/sfx/{name}.mp3', 2); x /= max(1e-6, np.abs(x).max()); cache[name] = x
    x = cache[name]; key = name.split('_')[0].rstrip('0123456789')
    gdb = GAIN.get(key, -16)
    st = int(max(0, t - PRE.get(key, 0)) * SR)
    seg = x[: max(0, N - st)] * db(gdb)
    if key in ('typing', 'siren'):  # long beds: cap to 2.5 s with fade
        L = min(len(seg), int(2.5 * SR)); seg = seg[:L].copy(); f = int(0.4 * SR); seg[-f:] *= np.linspace(1, 0, f)[:, None]
    sfx[st:st + len(seg)] += seg
print(len(cues), 'sfx cues')

mix = music + sfx + np.stack([out_v, out_v], 1)
mix = mix[:end]
# soft limiter
peak = np.abs(mix).max(); print('peak before', peak)
mix = mix * (0.95 / peak) if peak > 0.95 else mix
tmp = f'{ROOT}/public/audio/_premix.wav'
import wave
with wave.open(tmp, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype('<i2').tobytes())
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', tmp, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=9', '-ar', str(SR), f'{ROOT}/public/audio/final_mix.wav'], check=True)
print('done')
