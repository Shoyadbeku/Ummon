"""GPU'siz rasm jonlantirish: Depth Anything V2 (ONNX, CPU) + 2.5D parallax kamera + jonli effektlar.

    pip install onnxruntime opencv-python-headless numpy
    curl -L -o depth_anything_v2_vitb.onnx \
      https://github.com/fabio-sim/Depth-Anything-ONNX/releases/download/v2.0.0/depth_anything_v2_vitb.onnx
    python animate/parallax.py --model depth_anything_v2_vitb.onnx

Natija: animate/clips/NN.mp4 va fox_sheep_story_animated.mp4
"""
import argparse
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "wan22"))
from concat import concat  # noqa: E402

FRAMES_DIR = ROOT / "frames"
OUT_DIR = ROOT / "animate" / "clips"
W, H, FPS = 1080, 1920, 24

# Har bir kadr: davomiylik, kamera (zoom boshi/oxiri, parallax kuchi, siljish x/y), effektlar
SCENES = {
    "01.jpg": dict(sec=4, zoom=(1.00, 1.08), par=0.035, pan=(0.015, 0.0), dust=60, breathe=1),
    "02.jpg": dict(sec=4, zoom=(1.04, 1.04), par=0.04, pan=(-0.025, 0.0), dust=40, sparks=(700, 1040), breathe=1),
    "03.jpg": dict(sec=4, zoom=(1.10, 1.00), par=0.03, pan=(0.0, 0.01), dust=30, breathe=1),
    "04.jpg": dict(sec=4, zoom=(1.00, 1.10), par=0.04, pan=(0.0, -0.01), dust=50, shake=0.002),
    "05.jpg": dict(sec=4, zoom=(1.00, 1.12), par=0.06, pan=(0.0, -0.015), dust=40),
    "06.jpg": dict(sec=4, zoom=(1.03, 1.06), par=0.03, pan=(0.02, 0.0), dust=50, breathe=1),
    "07.jpg": dict(sec=4, zoom=(1.00, 1.08), par=0.035, pan=(-0.01, 0.0), dust=40, breathe=1),
    "08.jpg": dict(sec=4, zoom=(1.02, 1.10), par=0.04, pan=(0.0, 0.0), dust=40, shake=0.004, breathe=1),
    "09.jpg": dict(sec=4, zoom=(1.00, 1.07), par=0.03, pan=(0.0, 0.0), dust=30, breathe=1),
    "10.jpg": dict(sec=5, zoom=(1.00, 1.12), par=0.035, pan=(0.01, -0.005), dust=60, breathe=1),
}


def estimate_depth(sess, img):
    """Depth Anything V2: 0 = uzoq, 1 = yaqin."""
    x = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), (518, 518), interpolation=cv2.INTER_CUBIC)
    x = (x.astype(np.float32) / 255 - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    x = x.transpose(2, 0, 1)[None].astype(np.float32)
    d = sess.run(None, {sess.get_inputs()[0].name: x})[0][0]
    d = cv2.resize(d, (W, H), interpolation=cv2.INTER_CUBIC)
    d = (d - np.percentile(d, 2)) / (np.percentile(d, 98) - np.percentile(d, 2) + 1e-6)
    d = np.clip(d, 0, 1).astype(np.float32)
    # Old plan chegarasini biroz kengaytirib, qahramonlar qirrasi orqa fonni sudramasin
    d = cv2.dilate(d, np.ones((15, 15), np.uint8))
    return cv2.GaussianBlur(d, (0, 0), 6)


def glow_mask(img):
    """Issiq, yorqin joylar (fonar, sham, ko'z uchquni) — lipillash uchun."""
    f = img.astype(np.float32)
    b, g, r = f[..., 0], f[..., 1], f[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    warm = np.clip((r - b - 25) / 60, 0, 1) * np.clip((lum - 150) / 80, 0, 1)
    return cv2.GaussianBlur(warm, (0, 0), 3)


def ease(u):
    return u * u * (3 - 2 * u)


def render_scene(sess, name, cfg, out_path):
    src = cv2.resize(cv2.imread(str(FRAMES_DIR / name)), (W, H), interpolation=cv2.INTER_AREA)
    depth = estimate_depth(sess, src)
    glow = glow_mask(src)
    halo = cv2.GaussianBlur(glow, (0, 0), 40)
    rng = np.random.default_rng(int(name[:2]))

    n = int(cfg["sec"] * FPS)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, H / 2
    # Qahramonlar markazi taxminan yaqin plan og'irlik markazi
    near = depth > 0.6
    by = float(yy[near].max()) if near.any() else H

    # Zarralar: sekin suzuvchi chang/uchqunlar (yaqinlari kattaroq va tezroq)
    k = cfg.get("dust", 0)
    px, py = rng.uniform(0, W, k), rng.uniform(0, H, k)
    pz = rng.uniform(0.2, 1, k)
    pvx, pvy = rng.normal(0, 6, k), rng.uniform(-18, -4, k)
    pph = rng.uniform(0, 6.28, k)
    flick_ph = rng.uniform(0, 6.28, 3)

    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "17",
         "-preset", "medium", "-pix_fmt", "yuv420p", str(out_path)],
        stdin=subprocess.PIPE)

    for i in range(n):
        t = i / FPS
        u = ease(i / max(n - 1, 1))
        z0, z1 = cfg["zoom"]
        zoom = z0 + (z1 - z0) * u
        dz = (z1 - z0) * u
        pan_x = cfg["pan"][0] * (u - 0.5) * W
        pan_y = cfg["pan"][1] * (u - 0.5) * H
        sh = cfg.get("shake", 0)
        if sh:
            pan_x += sh * W * (np.sin(t * 23) + 0.5 * np.sin(t * 37))
            pan_y += sh * H * 0.5 * np.sin(t * 29)

        # 2.5D: yaqin piksellar ko'proq kattalashadi va ko'proq siljiydi
        par = cfg["par"]
        s = zoom * (1 + dz * depth)
        mx = (xx - cx) / s + cx - pan_x * (1 + depth * par * 40) / zoom
        my = (yy - cy) / s + cy - pan_y * (1 + depth * par * 40) / zoom
        # Yengil "aylanma" parallax (kamera biroz suzadi)
        mx -= depth * par * W * 0.25 * np.sin(2 * np.pi * t / cfg["sec"])
        if cfg.get("breathe"):
            # Nafas olish: yaqin plan pastdan yuqoriga juda kam cho'ziladi
            b = 0.006 * np.sin(2 * np.pi * t / 2.6)
            w = np.clip((depth - 0.5) * 2, 0, 1)
            my += (by - my) * b * w
        frame = cv2.remap(src, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

        # Alanga lipillashi (bir nechta sinus = tartibsiz shovqin)
        fl = (0.55 * np.sin(t * 11 + flick_ph[0]) + 0.3 * np.sin(t * 17.3 + flick_ph[1])
              + 0.15 * np.sin(t * 31 + flick_ph[2]))
        g = cv2.remap(glow, mx, my, cv2.INTER_LINEAR)
        hl = cv2.remap(halo, mx, my, cv2.INTER_LINEAR)
        f = frame.astype(np.float32)
        f *= (1 + 0.18 * fl * g)[..., None]
        f += (hl * (0.10 + 0.06 * fl))[..., None] * np.array([40, 120, 255], np.float32)

        # Zarralar
        if k:
            layer = np.zeros((H, W), np.float32)
            x = (px + pvx * t + 10 * np.sin(t * 0.8 + pph)) % W
            y = (py + pvy * t * pz) % H
            for j in range(k):
                a = 0.35 + 0.35 * np.sin(t * 2 + pph[j])
                cv2.circle(layer, (int(x[j]), int(y[j])), max(1, int(3 * pz[j])), float(a), -1, cv2.LINE_AA)
            layer = cv2.GaussianBlur(layer, (0, 0), 1.2)
            f += layer[..., None] * np.array([120, 190, 255], np.float32)

        # Uchqunlar (masalan, telefon trubkasi atrofida)
        if "sparks" in cfg:
            sx, sy = cfg["sparks"]
            sp = np.zeros((H, W), np.float32)
            for j in range(14):
                ph = (t * 0.9 + j / 14) % 1
                ang = j * 2.4
                r = 20 + 140 * ph
                cv2.circle(sp, (int(sx + r * np.cos(ang)), int(sy - r * np.sin(ang) - 60 * ph)),
                           2, float(1 - ph), -1, cv2.LINE_AA)
            sp = cv2.GaussianBlur(sp, (0, 0), 2)
            f += sp[..., None] * np.array([110, 200, 255], np.float32) * 1.5

        # Film donadorligi + vinyetka nafasi
        f += rng.normal(0, 5, (H // 2, W // 2)).astype(np.float32).repeat(2, 0).repeat(2, 1)[..., None]
        frame = np.clip(f, 0, 255).astype(np.uint8)
        ff.stdin.write(frame.tobytes())

    ff.stdin.close()
    ff.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="depth_anything_v2_*.onnx")
    ap.add_argument("--only", nargs="*", help="faqat shu kadrlar, masalan 01.jpg")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sess = ort.InferenceSession(args.model, providers=["CPUExecutionProvider"])
    clips = []
    for name, cfg in SCENES.items():
        out = OUT_DIR / f"{Path(name).stem}.mp4"
        clips.append(out)
        if args.only and name not in args.only:
            continue
        render_scene(sess, name, cfg, out)
        print(f"done {out.name}", flush=True)
    if not args.only:
        concat(clips, ROOT / "fox_sheep_story_animated.mp4")


if __name__ == "__main__":
    main()
