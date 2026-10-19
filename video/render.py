"""Rasmni gapirtirib, ovoz va so'zma-so'z subtitr bilan vertikal video yasaydi.

Faqat CPU: numpy + OpenCV + ffmpeg.
  python3 render.py            -> out/hikoya.mp4
  python3 render.py --preview  -> birinchi 12 soniya, tezkor tekshiruv uchun
"""
import json, subprocess, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 720, 1280, 30
SRC = "assets/tulki.jpg"
AUDIO = "assets/ovoz.mp3"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
PREVIEW = "--preview" in sys.argv

img = cv2.imread(SRC).astype(np.float32)
SH, SW = img.shape[:2]
meta = json.load(open("words.json", encoding="utf-8"))
words = meta["words"]
DUR = meta["duration"] + 0.6
N = int((12 if PREVIEW else DUR) * FPS)

# ---------- ovoz qattiqligi -> og'iz ochilishi ----------
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", AUDIO, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                     capture_output=True).stdout
pcm = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
hop = 16000 // FPS
rms = np.array([np.sqrt(np.mean(pcm[i * hop:(i + 1) * hop] ** 2) + 1e-9) for i in range(len(pcm) // hop)])
db = 20 * np.log10(rms)
lvl = np.clip((db + 42) / 26, 0, 1)            # -42dB -> yopiq, -16dB -> to'liq ochiq
env = np.zeros_like(lvl)
for i in range(1, len(lvl)):                   # tez ochilib, sekinroq yopiladi
    a = 0.75 if lvl[i] > env[i - 1] else 0.45
    env[i] = env[i - 1] + a * (lvl[i] - env[i - 1])
env = np.concatenate([env, np.zeros(N + 10)])

# ---------- og'iz (manba rasm koordinatalarida) ----------
mouth_pts = np.array([(292, 836), (320, 846), (350, 849), (380, 847), (410, 838),
                      (440, 824), (465, 806), (486, 782)], np.float32)
MX0, MX1, MY0, MY1 = 270, 500, 760, 960        # ishlov beriladigan hudud
xs = np.arange(MX0, MX1, dtype=np.float32)
ym = np.interp(xs, mouth_pts[:, 0], mouth_pts[:, 1]).astype(np.float32)
prof = np.interp(xs, [285, 315, 400, 450, 488], [0.0, 1.0, 1.0, 0.45, 0.0]).astype(np.float32)
MAX_OPEN = 22.0
gy, gx = np.mgrid[MY0:MY1, MX0:MX1].astype(np.float32)
mouth_dark = np.array([22, 24, 38], np.float32)   # BGR: to'q qizg'ish-qora
tongue = np.array([70, 80, 150], np.float32)


def talk(src, o):
    """o in [0,1]: pastki jag'ni pastga suradi, oradagi bo'shliqni og'iz ichi bilan to'ldiradi."""
    if o < 0.03:
        return src
    out = src.copy()
    op = o * MAX_OPEN * prof                       # har x uchun ochilish (piksel)
    rel = gy - ym[None, :]                         # og'iz chizig'idan pastga masofa
    fall = np.clip(1 - (rel - op[None, :]) / 75.0, 0, 1)   # 75px pastda deformatsiya so'nadi
    shift = op[None, :] * fall
    below = rel > 0
    mapy = np.where(below, gy - shift, gy).astype(np.float32)
    reg = cv2.remap(src, gx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    gap = below & (rel < op[None, :])
    # og'iz ichi: yuqorida to'q, pastda til
    t = np.clip(rel / np.maximum(op[None, :], 1), 0, 1)[..., None]
    inner = mouth_dark * (1 - 0.6 * t) + tongue * 0.6 * t * (t > 0.55)
    reg = np.where(gap[..., None], inner, reg)
    # pastki lab chizig'i (qora kontur) bo'shliq ostida
    edge = below & (np.abs(rel - op[None, :]) < 2.2) & (op[None, :] > 1.5)
    reg[edge] = reg[edge] * 0.15
    out[MY0:MY1, MX0:MX1] = reg
    return out


# ---------- kadrlar (shot) ----------
# (markaz x, markaz y, kenglik) manba rasmda; zoom: boshidan oxirigacha kattalashish
SHOTS = {
    "wide":   (384, 688, 768),
    "face":   (370, 640, 520),
    "eyes":   (365, 545, 360),
    "mouth":  (370, 770, 420),
    "hand":   (250, 760, 420),
    "glass":  (300, 560, 250),
    "crowd":  (95, 520, 250),
    "lamp":   (680, 230, 330),
    "pin":    (520, 1100, 330),
}
# (boshlanish soniyasi, kadr, zoom_bosh, zoom_oxir, dx, dy, effekt)
EDIT = [
    (0.00, "crowd", 1.00, 1.10, 0, 0, "dim"),
    (2.30, "face", 1.00, 1.06, 0, 0, ""),
    (5.40, "wide", 1.05, 1.12, 0, -10, ""),
    (9.70, "hand", 1.00, 1.08, 10, 0, ""),
    (14.60, "face", 1.08, 1.00, 0, 0, ""),
    (18.20, "mouth", 1.00, 1.06, 0, 0, ""),
    (21.90, "eyes", 1.00, 1.12, 0, 0, ""),
    (25.50, "crowd", 1.05, 1.15, 10, 0, "dim"),
    (29.20, "wide", 1.15, 1.05, 0, 0, ""),
    (33.20, "lamp", 1.00, 1.10, 0, 10, "dim"),
    (36.00, "face", 1.00, 1.05, 0, 0, ""),
    (41.70, "face", 1.05, 1.22, 0, 20, ""),
    (47.40, "eyes", 1.10, 1.25, 0, 0, ""),
    (50.20, "glass", 1.00, 1.15, 0, 0, ""),
    (53.00, "mouth", 1.05, 1.00, 0, 0, ""),
    (56.00, "pin", 1.00, 1.12, 0, 0, ""),
    (59.30, "crowd", 1.10, 1.00, -10, 0, "dim"),
    (62.00, "wide", 1.00, 1.10, 0, 0, ""),
    (66.70, "hand", 1.06, 1.00, 0, 0, ""),
    (69.50, "face", 1.00, 1.08, 0, 0, ""),
    (72.10, "crowd", 1.00, 1.12, 0, 0, "dim"),
    (74.40, "mouth", 1.00, 1.07, 0, 0, ""),
    (78.50, "lamp", 1.10, 1.00, 0, 0, "dim"),
    (82.20, "face", 1.12, 1.00, 0, 0, ""),
    (85.70, "wide", 1.00, 1.05, 0, 0, ""),
    (88.80, "face", 1.00, 1.18, 0, 10, ""),
    (94.75, "eyes", 1.00, 1.15, 0, 0, ""),
    (97.30, "wide", 1.15, 1.00, 0, 0, "end"),
]
EDIT.append((DUR + 1, None, 1, 1, 0, 0, ""))


def shot_at(t):
    for i in range(len(EDIT) - 1):
        if EDIT[i][0] <= t < EDIT[i + 1][0]:
            return EDIT[i], EDIT[i][0], EDIT[i + 1][0]
    return EDIT[-2], EDIT[-2][0], DUR


def ease(u):
    return u * u * (3 - 2 * u)


def camera(t):
    (st, name, z0, z1, dx, dy, fx), a, b = shot_at(t)
    u = ease(np.clip((t - a) / max(b - a, 0.1), 0, 1))
    cx, cy, cw = SHOTS[name]
    z = z0 + (z1 - z0) * u
    cw = cw / z
    cx, cy = cx + dx * u, cy + dy * u
    # qo'lda ushlangan kamera titrashi
    cx += 2.0 * np.sin(t * 1.3) + 1.2 * np.sin(t * 2.9)
    cy += 1.6 * np.sin(t * 1.7 + 1)
    cw = min(cw, SW)
    ch = cw * H / W
    cx = np.clip(cx, cw / 2, SW - cw / 2)
    cy = np.clip(cy, ch / 2, SH - ch / 2)
    return cx, cy, cw, fx, t - a


# ---------- effektlar ----------
rng = np.random.default_rng(1)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
vign = 1 - 0.55 * (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
vign = np.clip(vign, 0.25, 1)[..., None]
sm = rng.random((H // 8 + 64, W // 8 + 64)).astype(np.float32)
sm = cv2.GaussianBlur(sm, (0, 0), 6)
sm = (sm - sm.min()) / (sm.max() - sm.min())
smoke = cv2.resize(sm, None, fx=8, fy=8, interpolation=cv2.INTER_CUBIC)
smoke = np.clip((smoke - 0.5) * 2.2, 0, 1)
smoke_mask = np.clip(1 - yy / (H * 0.75), 0, 1)
grain_bank = [rng.normal(0, 1, (H, W, 1)).astype(np.float32) for _ in range(8)]
tint = np.array([0.86, 0.97, 1.08], np.float32)   # BGR: iliq sepiya


def caption_layer(t):
    cur = None
    for w in words:
        if w["s"] <= t < w["e"] + 0.05:
            cur = w
    if cur is None:
        return None
    txt = cur["w"].strip("'\"“”.,?!—:;").upper()
    if not txt:
        return None
    pop = np.clip((t - cur["s"]) / 0.09, 0, 1)
    size = int(52 * (0.82 + 0.18 * pop))
    font = ImageFont.truetype(FONT, size)
    layer = Image.new("RGBA", (W, 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    tw = d.textlength(txt, font=font)
    d.text(((W - tw) / 2 + 3, 40 + 4), txt, font=font, fill=(0, 0, 0, 170))
    d.text(((W - tw) / 2, 40), txt, font=font, fill=(250, 238, 210, 255),
           stroke_width=3, stroke_fill=(15, 10, 5, 255))
    return np.asarray(layer).astype(np.float32)


CAP_Y = int(H * 0.74)
CROWD_BLUR = cv2.GaussianBlur(img, (0, 0), 1.6)

ff = subprocess.Popen(
    ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
     "-i", "-", "-i", "out/audio.m4a", "-map", "0:v", "-map", "1:a",
     "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
     "-c:a", "copy", "-shortest", "-movflags", "+faststart",
     "out/preview.mp4" if PREVIEW else "out/hikoya.mp4"], stdin=subprocess.PIPE)

prev_name = None
for f in range(N):
    t = f / FPS
    cx, cy, cw, fx, ts = camera(t)
    o = env[f]
    src = talk(CROWD_BLUR if shot_at(t)[0][1] == "crowd" else img, o)
    # bosh/nafas harakati: gapirganda biroz ko'proq tebranadi
    ang = 0.5 * np.sin(t * 0.8) + 0.35 * o * np.sin(t * 5.0)
    s = W / cw
    M = cv2.getRotationMatrix2D((cx, cy), ang, s * (1 + 0.004 * np.sin(t * 1.9)))
    M[0, 2] += W / 2 - cx
    M[1, 2] += H / 2 - cy
    frame = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

    # sham miltillashi + tutun
    flick = 1 + 0.035 * np.sin(t * 7.3) * np.sin(t * 3.1 + 2) + 0.015 * np.sin(t * 17)
    off = int(t * 18) % (smoke.shape[0] - H)
    offx = int(20 * np.sin(t * 0.3)) + 256
    sk = smoke[smoke.shape[0] - H - off: smoke.shape[0] - off, offx: offx + W][..., None]
    frame = frame * flick
    frame = frame + (np.array([150, 180, 210], np.float32) - frame) * (sk * smoke_mask[..., None] * 0.22)
    if fx == "dim":
        frame *= 0.82
    frame = frame * tint
    frame = (frame - 128) * 1.06 + 128
    frame = frame * vign + grain_bank[f % 8] * 7
    # kadr almashganda qisqa yorug'lik chaqnashi
    if ts < 0.1:
        frame = frame + (1 - ts / 0.1) * 40
    if t < 0.5:
        frame *= t / 0.5
    if t > DUR - 1.2:
        frame *= max(DUR - t, 0) / 1.2
    # tasodifiy chang/tirnalish
    if rng.random() < 0.08:
        x = int(rng.integers(0, W))
        cv2.line(frame, (x, 0), (x + int(rng.integers(-20, 20)), H), (210, 225, 235), 1)
    cap = caption_layer(t)
    if cap is not None:
        a = cap[..., 3:4] / 255
        roi = frame[CAP_Y:CAP_Y + 140]
        roi[:] = roi * (1 - a) + cap[..., [2, 1, 0]] * a
    ff.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
    if f % 300 == 0:
        print(f"{f}/{N}", flush=True)
ff.stdin.close()
ff.wait()
print("tayyor")
