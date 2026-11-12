"""Ovoz effektlarini sintez qilish (mualliflik huquqisiz): whoosh, impact, stamp, pop.
Ishlatish: python3 scripts/make_sfx.py public/sfx
"""
import sys, os, wave
import numpy as np
SR = 44100
out = sys.argv[1] if len(sys.argv) > 1 else 'public/sfx'
os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(1)

def save(name, x):
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.9
    st = np.stack([x, x], 1)
    with wave.open(os.path.join(out, name), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())

def lowpass(x, cutoff):  # cutoff: Hz massivi yoki son (bir qutbli filtr)
    c = np.broadcast_to(np.asarray(cutoff, float), x.shape)
    a = 1 - np.exp(-2 * np.pi * c / SR)
    y = np.zeros_like(x); acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc); y[i] = acc
    return y

# Whoosh: shovqin, filtr yuqoriga-pastga suriladi
n = int(1.3 * SR); t = np.arange(n) / SR
env = np.sin(np.pi * np.clip(t / 1.3, 0, 1)) ** 2
cut = 300 + 4500 * np.sin(np.pi * t / 1.3) ** 3
x = lowpass(rng.standard_normal(n), cut)
x = x - lowpass(x, 150)
save('whoosh.wav', x * env)

# Impact: past chastotali zarba + shovqinli "hit" + uzun dum
n = int(2.5 * SR); t = np.arange(n) / SR
f = 55 * (1 + 1.5 * np.exp(-t * 18))
boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
hit = lowpass(rng.standard_normal(n), 2500) * np.exp(-t * 22)
save('impact.wav', boom * 1.0 + hit * 0.6)

# Stamp: qisqa quruq zarba
n = int(0.5 * SR); t = np.arange(n) / SR
thud = np.sin(2 * np.pi * 110 * t * (1 + 0.8 * np.exp(-t * 40))) * np.exp(-t * 14)
crack = lowpass(rng.standard_normal(n), 4000) * np.exp(-t * 60)
save('stamp.wav', thud + crack * 0.8)

# Pop: yengil UI tovushi (pin, raqam)
n = int(0.35 * SR); t = np.arange(n) / SR
pop = np.sin(2 * np.pi * (900 + 700 * np.exp(-t * 30)) * t) * np.exp(-t * 16)
save('pop.wav', pop * 0.7)
print('ok')
