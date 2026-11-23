"""Procedurally synthesised sound design (no third-party samples -> no licensing issues)."""
import numpy as np, sys, os
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile
SR = 48000
out = sys.argv[1]
rng = np.random.default_rng(7)

def bp(x, lo, hi, order=4):
    return sosfilt(butter(order, [lo, hi], 'bandpass', fs=SR, output='sos'), x)
def lp(x, f, order=4):
    return sosfilt(butter(order, f, 'lowpass', fs=SR, output='sos'), x)
def hp(x, f, order=4):
    return sosfilt(butter(order, f, 'highpass', fs=SR, output='sos'), x)
def pink(n):
    w = rng.standard_normal(n); X = np.fft.rfft(w); f = np.arange(len(X)); f[0] = 1
    return np.fft.irfft(X / np.sqrt(f), n)
def brown(n):
    b = np.cumsum(rng.standard_normal(n)); b -= np.convolve(b, np.ones(4801)/4801, 'same'); return b
def norm(x, peak=0.9):
    return x / (np.max(np.abs(x)) + 1e-9) * peak
def verb(x, t=2.5, mix=0.35):
    n = int(SR*t); ir = rng.standard_normal(n) * np.exp(-np.linspace(0, 7, n)); ir = lp(ir, 6000)
    w = fftconvolve(x, ir)[:len(x)+n]; d = np.concatenate([x, np.zeros(n)]); w = np.pad(w, (0, len(d)-len(w)))
    return (1-mix)*d + mix*norm(w, np.max(np.abs(d)))
def stereo(l, r=None, width=0.0):
    if r is None: r = l
    return np.stack([l, r], 1)
def save(name, x):
    if x.ndim == 1: x = stereo(x)
    wavfile.write(os.path.join(out, name), SR, (np.clip(x, -1, 1)*32767).astype(np.int16))

# 1) Desert wind ambience, 64 s, seamless loop via crossfade
n = SR*64
def windch():
    p = pink(n+SR*4); lfo = 0.55+0.45*np.sin(np.linspace(0, 2*np.pi*5, n+SR*4) + rng.uniform(0, 6))
    g = 0.6+0.4*np.sin(np.linspace(0, 2*np.pi*13, n+SR*4)+rng.uniform(0, 6))
    w = bp(p, 180, 1400, 2)*lfo + 0.35*bp(p, 1500, 4200, 2)*lfo*g
    a = w[:n].copy(); tail = w[n:n+SR*4]; f = np.linspace(0, 1, SR*4)
    a[:SR*4] = a[:SR*4]*f + tail*(1-f); return norm(a, 0.6)
save('wind_amb.wav', stereo(windch(), windch()))

# 2) Whooshes (bandpass sweep)
for i, (dur, f0, f1) in enumerate([(1.1, 300, 4500), (0.8, 500, 6000), (1.6, 200, 3000)]):
    m = int(SR*dur); x = pink(m); t = np.linspace(0, 1, m)
    env = np.sin(np.pi*t**0.7)**2
    y = np.zeros(m); seg = 960
    for s in range(0, m, seg):
        c = f0*(f1/f0)**np.sin(np.pi*s/m*0.5)  # rise
        e = min(s+seg, m); y[s:e] = bp(x[max(0, s-4000):e], c*0.6, min(c*1.6, 20000), 2)[-(e-s):]
    y = y*env; pan = np.linspace(-0.7, 0.7, m)
    save(f'whoosh_{i+1}.wav', stereo(norm(y*(1-pan)/1.7, 0.7), norm(y*(1+pan)/1.7, 0.7)))

# 3) Cinematic sub impact
m = int(SR*3.0); t = np.arange(m)/SR
freq = 30+28*np.exp(-t*6); ph = 2*np.pi*np.cumsum(freq)/SR
sub = np.sin(ph)*np.exp(-t*1.6)
click = lp(rng.standard_normal(m), 2500)*np.exp(-t*30)*0.6
body = lp(brown(m), 300)*np.exp(-t*3); body = norm(body, 0.5)
save('impact.wav', norm(verb(sub+click+body, 2.0, 0.25), 0.85))

# 4) Soft impact (for gentler accents)
m = int(SR*2.2); t = np.arange(m)/SR
s2 = np.sin(2*np.pi*np.cumsum(45+20*np.exp(-t*8))/SR)*np.exp(-t*2.5) + 0.3*lp(rng.standard_normal(m), 800)*np.exp(-t*18)
save('soft_hit.wav', norm(verb(s2, 1.8, 0.3), 0.6))

# 5) Earth rumble / swallowing (8 s)
m = SR*8; t = np.arange(m)/SR
r = lp(brown(m), 110); r = norm(r)
trem = 0.6+0.4*np.abs(np.sin(2*np.pi*(3+4*t/8)*t + rng.uniform(0, 6)))
env = np.clip(t/1.2, 0, 1)*np.clip((8-t)/2.5, 0, 1)
cr = np.zeros(m)
for _ in range(70):
    p = int(rng.uniform(0.5, 6.5)*SR); L = int(SR*rng.uniform(0.02, 0.12))
    if p+L < m: cr[p:p+L] += hp(rng.standard_normal(L), 900)*np.exp(-np.linspace(0, 9, L))*rng.uniform(0.1, 0.5)
deep = np.sin(2*np.pi*np.cumsum(32+6*np.sin(t*1.3))/SR)*0.5
save('rumble.wav', norm(verb((r*trem+deep)*env + cr*env, 3.0, 0.3), 0.9))

# 6) Riser (tension build, 3 s)
m = SR*3; t = np.linspace(0, 1, m); x = pink(m); y = np.zeros(m); seg = 960
for s in range(0, m, seg):
    c = 150*(6000/150)**(s/m); e = min(s+seg, m); y[s:e] = bp(x[max(0, s-4000):e], c*0.7, min(c*1.4, 20000), 2)[-(e-s):]
y *= t**2
tone = np.sin(2*np.pi*np.cumsum(55+110*t**2)/SR)*t**2*0.3
save('riser.wav', norm(y+tone, 0.6))

# 7) Gold shimmer / glint
m = int(SR*2.5); t = np.arange(m)/SR; y = np.zeros(m)
for k, f in enumerate([2093, 2637, 3136, 4186, 5274]):
    d = int(SR*0.07*k); y[d:] += np.sin(2*np.pi*f*t[:m-d])*np.exp(-t[:m-d]*3.2)*(0.5/(k+1)**0.3)
save('shimmer.wav', norm(verb(y, 2.2, 0.45), 0.35))

# 8) Distant thunder (5 s)
m = SR*5; t = np.arange(m)/SR
th = lp(brown(m), 400)*(np.exp(-((t-0.6)/0.25)**2)+0.7*np.exp(-np.clip(t-0.6, 0, None)*0.9)*(t > 0.6))
th += 0.25*bp(rng.standard_normal(m), 800, 3000)*np.exp(-((t-0.55)/0.05)**2)
save('thunder.wav', norm(verb(th, 3.0, 0.35), 0.8))
print('ok')
