# Lichtenberg naqshi (daraxtsimon shoxlangan "paporotnik") teksturasini yasash: numpy, tashqi kutubxonasiz.
# R = chiziq (o'zak), G = paydo bo'lish vaqti (ildizdan masofa, 0..1), B = yumshoq qizarish (halo).
# Ishlatish: python -I lich.py <chiqish.png> [o'lcham] [seed]
import sys, math, subprocess
import numpy as np

def generate(size=2048, seed=3):
    rng = np.random.default_rng(seed)
    I = np.zeros((size, size), np.float32)
    T = np.full((size, size), 9.0, np.float32)
    pts = []                                    # (x, y, w, t)
    # ildiz: chap pastdan (bilakning bir chetidan) o'ngga va yuqoriga tarqaladi
    stack = [(size * 0.04, size * 0.45, 0.12, 9.0, 0.0, 0)]
    while stack:
        x, y, ang, w, t, depth = stack.pop()
        step = 2.2
        L = size * (0.8 if depth == 0 else rng.uniform(0.12, 0.34) * (0.6 ** (depth - 1)))
        d = 0.0; curl = rng.uniform(-0.004, 0.004); a0 = ang
        while d < L and w > 0.55:
            ang += rng.normal(0, 0.12 if depth < 2 else 0.16) + curl - 0.06 * (ang - a0); a0 += curl
            x += math.cos(ang) * step; y += math.sin(ang) * step; d += step; t += step
            if not (0 <= x < size and 0 <= y < size): break
            pts.append((x, y, w, t))
            w *= 0.9995 if depth == 0 else 0.9965
            if rng.random() < (0.022, 0.05, 0.08, 0.12, 0.12)[min(depth, 4)] and depth < 5:
                side = rng.choice((-1, 1))
                stack.append((x, y, ang + side * rng.uniform(0.35, 1.0), w * rng.uniform(0.5, 0.72), t, depth + 1))
    pts = np.array(pts, np.float32)
    tmax = pts[:, 3].max()
    for x, y, w, t in pts:
        r = int(math.ceil(w + 1))
        x0, x1 = max(0, int(x) - r), min(size, int(x) + r + 1)
        y0, y1 = max(0, int(y) - r), min(size, int(y) + r + 1)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        dd = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)
        v = np.clip(w + 0.5 - dd, 0, 1)
        I[y0:y1, x0:x1] = np.maximum(I[y0:y1, x0:x1], v)
        sub = T[y0:y1, x0:x1]; m = v > 0
        sub[m] = np.minimum(sub[m], t / tmax)
    # halo: tez Gauss xiralash (FFT)
    def blur(a, s):
        f = np.fft.rfftfreq(size)[None, :]; g = np.fft.fftfreq(size)[:, None]
        k = np.exp(-2 * (math.pi * s) ** 2 * (f ** 2 + g ** 2))
        return np.fft.irfft2(np.fft.rfft2(a) * k, (size, size))
    H = blur(I, 9.0); H = np.clip(H / max(1e-6, np.percentile(H, 99.7)), 0, 1)
    # vaqt maydonini ham yoyamiz (halo uchun): eng yaqin chiziq vaqti ~ xiralangan T
    Tm = np.where(T > 1.5, 0, T); Wt = (T <= 1.5).astype(np.float32)
    Tb = blur(Tm, 9.0) / np.maximum(blur(Wt, 9.0), 1e-4)
    G = np.where(T <= 1.5, T, np.clip(Tb, 0, 1) * (H > 0.02) + (H <= 0.02) * 1.0)
    return I, G.astype(np.float32), H.astype(np.float32)

if __name__ == "__main__":
    out = sys.argv[1]; size = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    I, G, H = generate(size, seed)
    rgb = (np.stack([I, G, H], -1)[::-1] * 255).clip(0, 255).astype(np.uint8)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size}x{size}", "-i", "-",
                    out], input=rgb.tobytes(), check=True)
    print("ok", out)
