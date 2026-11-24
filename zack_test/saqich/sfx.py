# "Saqich chaynash" videosi uchun tovush effektlari (sintez, litsenziya muammosi yo'q) -> sfx.wav (48 kHz, mono)
# Ishga tushirish: python3 -I zack_test/saqich/sfx.py /tmp/claude-0/audio/sfx_saqich.wav  (yordamchilar telefon/sfx.py dan)
import sys, wave
import numpy as np

SR = 48000; DUR = 35.84
rng = np.random.default_rng(12)
out = np.zeros(int(SR * DUR))
def T(frame): return (frame - 1) / 24.0             # kadr -> soniya

def t_(d): return np.arange(int(SR * d)) / SR
def env(n, a=0.005, decay=0.3):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / decay)
def lp(x, fc, n=2):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / fc) ** 2) ** (n / 2), len(x))
def hp(x, fc): return x - lp(x, fc, 1)
def bp(x, lo, hi): return hp(lp(x, hi, 2), lo)
def add(at, x, gain=1.0):
    i = int(at * SR); j = min(len(out), i + len(x))
    if j > i: out[i:j] += gain * x[: j - i]
def noise(d): return rng.standard_normal(int(SR * d))
def fade(x, a=0.05, b=0.2):
    n = len(x); e = np.ones(n); na, nb = int(a * SR), int(b * SR)
    e[:na] = np.linspace(0, 1, na); e[n - nb:] = np.linspace(1, 0, nb); return x * e

def thud(f=60, d=0.8, decay=0.25):
    t = t_(d); sweep = f * (1 + 1.5 * np.exp(-t / 0.03))
    return np.sin(2 * np.pi * np.cumsum(sweep) / SR) * env(len(t), 0.002, decay) + 0.3 * lp(noise(d), 400) * env(len(t), 0.002, 0.05)
def whoosh(d=0.7, fc=1400, peak=0.7):
    n = noise(d); t = t_(d); shape = np.exp(-((t / d - peak) ** 2) / 0.03)
    return hp(lp(n, fc, 2), fc * 0.25) * shape
def riser(d=2.0):
    t = t_(d); f = 200 + 1800 * (t / d) ** 2
    return (0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR) + bp(noise(d), 800, 6000) * 0.6) * (t / d) ** 2
def heartbeat():
    return np.concatenate([thud(52, 0.25, 0.06), np.zeros(int(SR * 0.12)), 0.7 * thud(48, 0.4, 0.07)])
def squelch(d=0.25, f0=500):                         # ho'l "chuv" tovushi
    t = t_(d); f = f0 * (1 + 0.8 * np.sin(2 * np.pi * 9 * t)) * np.exp(-t / 0.2)
    return (bp(noise(d), 300, 2500) * 0.7 + 0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * env(len(t), 0.004, d / 3)
def click(d=0.06, f=2500):
    return bp(noise(d), f * 0.5, f * 2) * env(int(SR * d), 0.0005, 0.008)
def zap(d=0.6, f0=2400, f1=300):                     # lazer
    t = t_(d); f = f0 + (f1 - f0) * (t / d) ** 0.5
    return (np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.3 + 0.5 * bp(noise(d), 1500, 7000)) * env(len(t), 0.002, d / 2.5)
def drone(d, f=55):
    t = t_(d); x = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t + 0.3) + 0.25 * np.sin(2 * np.pi * f * 2.01 * t)
    return fade(lp(x + 0.2 * noise(d), 600) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.3 * t)), 0.4, 0.6)
def crackle(d, dens=60):                             # elektr chirsillashi
    x = np.zeros(int(SR * d))
    for _ in range(int(d * dens)):
        i = rng.integers(0, len(x) - 2000); c = click(0.02, rng.uniform(1500, 6000)); x[i:i + len(c)] += c * rng.uniform(0.3, 1)
    return x
def hum(d, f=120):
    t = t_(d); return fade(bp(np.sign(np.sin(2 * np.pi * f * t)) + 0.3 * noise(d), 100, 3000) * 0.25, 0.1, 0.2)

def chew_snd(d=0.16):                                # saqich chaynash: ho'l "chak"
    t = t_(d); return (bp(noise(d), 600, 4000) * 0.6 + 0.3 * squelch(d, 380)[:len(t)]) * env(len(t), 0.003, 0.05)
def creak(d=0.35, f0=180):                           # suyak g'ichirlashi
    t = t_(d); f = f0 * (1 + 0.3 * np.sin(2 * np.pi * 23 * t))
    return (np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.2 + bp(noise(d), 300, 2500) * 0.5) * env(len(t), 0.02, d / 2)
def crack():                                          # "qirs"
    x = thud(70, 0.6, 0.12); c = click(0.03, 3500) * 2.0; n = bp(noise(0.12), 800, 6000) * env(int(SR * 0.12), 0.0005, 0.02) * 1.5
    x[:len(c)] += c; x[:len(n)] += n; return x
def sizzle(d):                                        # kislota vishillashi
    t = t_(d); x = hp(noise(d), 3000) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 7 * t)))
    return fade(x, 0.2, 0.3)
def blip(f=900):                                      # pufakcha / tomchi
    d = 0.08; t = t_(d); ff = f * (1 + 1.5 * t / d)
    return np.sin(2 * np.pi * np.cumsum(ff) / SR) * env(len(t), 0.002, 0.025)

# ---- kadrlar (saqich.py dagi bilan bir xil) ----
SH = dict(hook=1, wide=46, xbody=109, xjaw=183, muscle=245, face=313, ear=372, disc=427, wear=474, yawn=521, pop=571,
          stuck=613, chew2=659, brain=698, acid=753, ulcer=808, end=861)
F_EARX, F_CHID, F_YAWN, F_QIRS, F_GAST = 401, 297, 553, 592, 828
def span(a, b): return (T(SH[b]) - T(SH[a]))
# xona foni (kunduz: yengil shovqin, uzoqdan ko'cha)
for a, b in (("hook", "xbody"), ("face", "disc"), ("yawn", "pop"), ("stuck", "brain")):
    add(T(SH[a]), fade(lp(noise(span(a, b)), 500) * 0.05 + drone(span(a, b), 70) * 0.03, 0.05, 0.2))
# ilgak: o'ram shitirlashi, saqich og'izga, birinchi chaynash
add(0.0, bp(noise(0.5), 2500, 9000) * env(int(SR * 0.5), 0.005, 0.15), 0.35)
add(T(8), whoosh(0.4, 2000), 0.4); add(T(23), chew_snd(0.2), 1.0); add(T(23), thud(110, 0.25, 0.05), 0.4)
# chaynash: jag' yopilganda (davr 17 kadr, 30-kadrdan), yuz kadri, ikkinchi divan (davr 15)
f = 30 + 14
while f < 520:
    room = any(SH[a] <= f < SH[b] for a, b in (("hook", "xbody"), ("face", "disc")))
    add(T(f), chew_snd(), 0.55 if room else 0.18); f += 17
f = 659 + 13
while f < 753: add(T(f), chew_snd(), 0.5 if f < 698 else 0.15); f += 15
# keng plan: timelapse soat chiqillashi (tezlashib boradi)
k = 0; tt = T(SH["wide"])
while tt < T(SH["xbody"]) - 0.05:
    add(tt, click(0.025, 4200 if k % 2 else 3300), 0.3); tt += max(0.045, 0.22 - k * 0.012); k += 1
add(T(SH["xbody"]) - 0.5, riser(0.5), 0.4)
# rentgen tana: kirish zarbasi, g'uvillash, "aldov" pulsatsiyalari
add(T(SH["xbody"]), thud(60, 0.7, 0.2), 0.8); add(T(SH["xbody"]), hum(span("xbody", "face"), 95), 0.3)
for f in range(SH["xbody"] + 20, SH["xjaw"], 10): add(T(f), heartbeat(), 0.35)
# bo'g'im: suyak g'ichirlashi har chaynashda
add(T(SH["xjaw"]) - 0.2, whoosh(0.4, 1500), 0.4)
for f in range(SH["xjaw"] + 8, SH["face"], 17): add(T(f), creak(0.3, 160 + (f % 50)), 0.3)
# mushak: taranglik, "chidaydi" da crash zoom
add(T(F_CHID) - 0.4, whoosh(0.45, 2600), 0.6); add(T(F_CHID), thud(50, 0.9, 0.28), 1.0)
# quloq -> rentgen chaqnashi
add(T(SH["ear"]) - 0.2, whoosh(0.5, 1200), 0.4); add(T(F_EARX) - 0.3, riser(0.3), 0.4); add(T(F_EARX), thud(65, 0.6, 0.15), 0.7)
# kesim: dron, sekin g'ichirlash; ishqalanish: tez qirillash + chirsillash
add(T(SH["disc"]) - 0.25, whoosh(0.5, 3000), 0.6); add(T(SH["disc"]), drone(span("disc", "yawn"), 41), 0.4)
for f in range(SH["disc"] + 6, SH["wear"], 24): add(T(f), creak(0.5, 120), 0.35)
for f in range(SH["wear"], SH["yawn"] - 2, 7): add(T(f), creak(0.14, 260), 0.45); add(T(f), bp(noise(0.14), 1500, 7000) * env(int(SR * 0.14), 0.005, 0.05), 0.35)
add(T(SH["wear"]), crackle(span("wear", "yawn"), 70), 0.4)
# esnash: whoosh, so'ng rentgenga o'tish -> "qirs"
add(T(SH["yawn"]) - 0.2, whoosh(0.5, 1400), 0.4); add(T(SH["pop"]) - 0.25, whoosh(0.4, 2500), 0.5)
add(T(SH["pop"]), hum(span("pop", "stuck"), 110), 0.25); add(T(F_QIRS) - 0.6, riser(0.6), 0.5)
add(T(F_QIRS), crack(), 1.2); add(T(F_QIRS) + 0.01, thud(40, 1.2, 0.4), 0.9)
# og'iz ochiq qotdi: yurak urishi, past dron
add(T(SH["stuck"]), drone(span("stuck", "chew2"), 46), 0.4)
for k in range(3): add(T(SH["stuck"]) + 0.15 + k * 0.6, heartbeat(), 0.5)
# miya -> nerv impulsi -> oshqozon
add(T(SH["brain"]) - 0.2, whoosh(0.4, 1800), 0.5); add(T(SH["brain"]), thud(70, 0.5, 0.12), 0.5)
add(T(SH["brain"]) + 0.35, zap(1.6, 600, 2400), 0.3); add(T(SH["brain"]), crackle(span("brain", "acid"), 30), 0.25)
# oshqozon ichi: pufakchalar, tomchilar, vishillash; yara: zarba + kuchayuvchi vishillash, qora bilan tugash
add(T(SH["acid"]) - 0.25, whoosh(0.5, 900), 0.5); add(T(SH["acid"]), drone(span("acid", "end"), 38), 0.45)
for k in range(70): add(T(SH["acid"]) + rng.uniform(0, span("acid", "end") - 0.1), blip(rng.uniform(500, 1600)), rng.uniform(0.08, 0.25))
add(T(SH["acid"]), sizzle(span("acid", "end")), 0.12); add(T(SH["ulcer"]), sizzle(span("ulcer", "end")), 0.25)
add(T(F_GAST) - 0.3, whoosh(0.35, 2400), 0.6); add(T(F_GAST), thud(42, 1.4, 0.45), 1.0); add(T(F_GAST), crackle(1.0, 90), 0.35)

out = out / max(1e-6, np.abs(out).max()) * 0.8
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
print("sfx", DUR, "s")
