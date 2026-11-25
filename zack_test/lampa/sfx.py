# "Qorong'ida o'qish" videosi uchun tovush effektlari (sintez, tashqi fayl kerak emas) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: /tmp/claude-0/wvenv/bin/python -I zack_test/lampa/sfx.py /tmp/claude-0/audio/sfx.wav
import sys, wave
import numpy as np

SR = 48000; DUR = 43.67
SR = 48000; DUR = 41.84
rng = np.random.default_rng(13)
out = np.zeros(int(SR * DUR))
def T(frame): return (frame - 1) / 24.0
CUTS = [25, 56, 102, 136, 172, 239, 269, 336, 390, 430, 492, 560, 599, 664, 694, 718, 758, 796, 851, 909, 938, 960]
def t_(d): return np.arange(int(SR * d)) / SR
def env(n, a=0.005, decay=0.3):
    t = np.arange(n) / SR; return np.minimum(1, t / a) * np.exp(-t / decay)
def lp(x, fc, n=2):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / fc) ** 2) ** (n / 2), len(x))
def hp(x, fc): return x - lp(x, fc, 1)
def add(at, x, gain=1.0):
    i = int(at * SR); j = min(len(out), i + len(x))
    if i < len(out): out[i:j] += gain * x[: j - i]
def noise(d): return rng.standard_normal(int(SR * d))
def whoosh(d=0.6, fc=1200, peak=0.55):
    t = t_(d); shape = np.exp(-((t / d - peak) ** 2) / 0.03)
    return hp(lp(noise(d), fc, 2), fc * 0.2) * shape
def thud(f=60, d=0.5, decay=0.12):
    t = t_(d); sweep = f * (1 + 1.5 * np.exp(-t / 0.03))
    return np.sin(2 * np.pi * np.cumsum(sweep) / SR) * env(len(t), 0.002, decay) + 0.25 * lp(noise(d), 400) * env(len(t), 0.002, 0.04)
def heartbeat():
    return np.concatenate([thud(55, 0.25, 0.07), np.zeros(int(SR * 0.11)), 0.75 * thud(50, 0.4, 0.08)])
def fizz(d, density=900, gain=1.0):                            # gaz pufakchalari chirsillashi
    x = np.zeros(int(SR * d)); n = int(d * density)
    for _ in range(n):
        i = rng.integers(0, len(x) - 200); L = rng.integers(40, 160)
        f = rng.uniform(2500, 9000); tt = np.arange(L) / SR
        x[i:i + L] += np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.0015) * rng.uniform(0.1, 1)
    return x * gain
def plop(f=700):                                              # qand suvga tushishi
    t = t_(0.18); sweep = f * (1 + 2.0 * np.exp(-t / 0.02))
    return np.sin(2 * np.pi * np.cumsum(sweep) / SR) * env(len(t), 0.001, 0.05) + 0.3 * hp(noise(0.18), 2000) * env(len(t), 0.001, 0.02)
def gulp():                                                   # ho'plash
    t = t_(0.28); f = 180 * (1 + 0.8 * np.exp(-t / 0.05))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.01, 0.07) + 0.4 * lp(noise(0.28), 600) * env(len(t), 0.005, 0.05))
def beep(f=880, d=0.16):
    t = t_(d); return np.sin(2 * np.pi * f * t) * np.minimum(1, t / 0.005) * np.minimum(1, (d - t) / 0.02)
def riser(d, f0, f1):
    t = t_(d); f = f0 * (f1 / f0) ** (t / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / d) ** 2
def click():                                                  # o'chirgich "chiq"
    return np.concatenate([hp(noise(0.012), 2500) * env(int(SR * 0.012), 0.0005, 0.003), np.zeros(int(SR * 0.03)),
                           0.5 * thud(2400, 0.04, 0.005)])
def tick(f=3200):
    return hp(noise(0.02), f) * env(int(SR * 0.02), 0.0003, 0.004)
def creak(d=0.6, f0=90):                                      # mushak tortilishi (past g'ichirlash)
    t = t_(d); f = f0 * (1 + 0.3 * np.sin(2 * np.pi * 7 * t)); x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR))
    return lp(x * (0.6 + 0.4 * lp(noise(d), 30)), 900) * np.sin(np.pi * t / d)

# fon: tungi xona + past drone (chiroq o'chgach)
tt = np.arange(len(out)) / SR
amb = lp(noise(DUR), 300, 3); amb /= np.abs(amb).max(); out += amb * 0.025
hum = np.sin(2 * np.pi * 100 * tt) * 0.012 * (tt < T(15))      # shift chirog'i g'ung'illashi
out += hum
drone = sum(np.sin(2 * np.pi * f * tt) for f in (49, 73.4, 98)) / 3 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.15 * tt))
out += drone * 0.02 * (tt > T(15))
# 1: o'chirgich + qorong'ilik zarbasi
add(T(14), click(), 0.9); add(T(15), thud(42, 1.4, 0.5), 0.7)
# 3: lampa chirog'i yoqiladi (yengil "ting" va g'ung'illash)
add(T(58), click(), 0.4); add(T(58), np.sin(2 * np.pi * 120 * t_(1.8)) * env(int(SR * 1.8), 0.05, 1.2), 0.05)
# 4: telefon ekrani (bildirishnoma)
add(T(104), beep(1320, 0.08), 0.12); add(T(104) + 0.1, beep(1760, 0.1), 0.1)
# 5: soat chiqillashi tezlashadi
t0, t1 = T(136), T(172); n = 0; t = t0
while t < t1:
    add(t, tick(2500 + 800 * (n % 2)), 0.5); n += 1; t += max(0.035, 0.32 * (1 - (t - t0) / (t1 - t0)) ** 2)
# 6, 14-15: mushaklar zo'riqishi
add(T(180), creak(2.4, 70), 0.25); add(T(205), riser(1.2, 120, 500), 0.06)
add(T(600), creak(2.5, 85), 0.18)
for f in range(664, 694, 6): add(T(f), thud(65, 0.3, 0.06), 0.55)
# 9-11: qorachiq kengayishi / torayishi
add(T(345), riser(1.0, 180, 900), 0.1)
add(T(398), thud(1200, 0.08, 0.02), 0.35)
for f, up in ((440, 1), (464, 0), (475, 1), (485, 0)):
    add(T(f), riser(0.3, 200, 1200) if up else riser(0.25, 900, 150), 0.1)
# 12, 13: fokus "vish-vush"
for f in range(492, 598, 9): add(T(f), whoosh(0.3, 2200, 0.5), 0.12)
# 16-17: og'riq pulsi (yurak urishi)
for f in range(700, 758, 10): add(T(f), heartbeat(), 0.7)
# 18: xiralashish — past filtrlangan shovqin
add(T(758), lp(noise(1.6), 500) * np.sin(np.pi * t_(1.6) / 1.6), 0.2)
# 19: pirpirash
add(T(836), thud(300, 0.08, 0.02), 0.25)
# 21: esnash (pastga tushuvchi nafas)
t = t_(1.2); add(T(912), lp(noise(1.2), 700) * np.sin(np.pi * t / 1.2) ** 2, 0.25)
# 22: satrlar suzadi
add(T(938), riser(0.9, 600, 200), 0.06)
# 23: bosh kitobga tushadi, lampa lip-lip qilib o'chadi
add(T(985), thud(80, 0.5, 0.1) + 0.5 * lp(noise(0.5), 1200) * env(int(SR * 0.5), 0.002, 0.05), 0.6)
for f in (986, 988, 991, 992, 995): add(T(f), hp(noise(0.03), 1500) * env(int(SR * 0.03), 0.001, 0.01), 0.25)
add(T(997), click(), 0.7); add(T(997) + 0.04, thud(40, 1.0, 0.35), 0.6)
# kesishlarda "vush"
for f in CUTS:
    add(max(0, T(f) - 0.25), whoosh(0.45, rng.uniform(900, 1600)), 0.2)

out = out / max(1e-6, np.abs(out).max()) * 0.9
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("ok", DUR)
