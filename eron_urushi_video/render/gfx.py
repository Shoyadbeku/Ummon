"""Graphics helpers: fonts, text layers, colours. All sizes are given in 4K units and scaled by S."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import functools, os

FONT_DIR = None
def _find_font(name):
    import subprocess
    out = subprocess.run(["fc-match", "-f", "%{file}", name], capture_output=True, text=True).stdout
    return out

FONTS = {
    "black": _find_font("Inter:style=Black"),
    "xbold": _find_font("Inter:style=ExtraBold"),
    "bold": _find_font("Inter:style=Bold"),
    "semi": _find_font("Inter:style=SemiBold"),
    "med": _find_font("Inter:style=Medium"),
    "reg": _find_font("Inter:style=Regular"),
    "disp": _find_font("Inter Display:style=Black"),
    "dispx": _find_font("Inter Display:style=ExtraBold"),
    "mono": _find_font("JetBrains Mono:style=Bold"),
}

# palette
NAVY = (9, 16, 32)
NAVY2 = (18, 30, 56)
RED = (214, 32, 39)
RED2 = (160, 18, 24)
WHITE = (255, 255, 255)
OFF = (232, 236, 242)
GREY = (150, 160, 178)
GOLD = (245, 185, 30)
TEAL = (40, 170, 190)

class Ctx:
    def __init__(self, W, H, fps=25):
        self.W, self.H, self.fps = W, H, fps
        self.S = W / 3840.0
    def s(self, v):
        return int(round(v * self.S))

@functools.lru_cache(maxsize=256)
def font(kind, px):
    return ImageFont.truetype(FONTS[kind], max(6, int(px)))

def text_size(txt, fnt, tracking=0):
    b = fnt.getbbox(txt)
    w = b[2] - b[0] + max(0, len(txt) - 1) * tracking
    return w, b[3] - b[1], b

def draw_text(draw, xy, txt, fnt, fill, tracking=0, anchor="la"):
    if tracking == 0:
        draw.text(xy, txt, font=fnt, fill=fill, anchor=anchor)
        return
    x, y = xy
    for ch in txt:
        draw.text((x, y), ch, font=fnt, fill=fill, anchor=anchor)
        x += fnt.getlength(ch) + tracking

def wrap(txt, fnt, maxw):
    words = txt.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if fnt.getlength(t) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def rgba_layer(w, h):
    return Image.new("RGBA", (max(1, int(w)), max(1, int(h))), (0, 0, 0, 0))

def shadowed(img, radius, opacity=160, offset=(0, 0)):
    """Return new RGBA image with soft drop shadow behind img (expanded by radius)."""
    pad = radius * 3
    W, H = img.size[0] + pad * 2, img.size[1] + pad * 2
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = img.split()[3]
    sh = Image.new("L", (W, H), 0)
    sh.paste(a, (pad + offset[0], pad + offset[1]))
    sh = sh.filter(ImageFilter.GaussianBlur(radius))
    sh = sh.point(lambda v: v * opacity // 255)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 255)); shadow.putalpha(sh)
    base.alpha_composite(shadow)
    base.alpha_composite(img, (pad, pad))
    return base, pad

def ease_out(x):
    x = min(1, max(0, x)); return 1 - (1 - x) ** 3
def ease_in_out(x):
    x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def ease_out_back(x):
    x = min(1, max(0, x)); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

def to_np(img):
    return np.asarray(img)

def composite(frame, layer_rgba, x, y, alpha=1.0):
    """frame: HxWx3 uint8 numpy (writable). layer_rgba: hxwx4 uint8 numpy. Blend in place."""
    if alpha <= 0.003:
        return
    H, W = frame.shape[:2]
    h, w = layer_rgba.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    L = layer_rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = L[..., 3:4].astype(np.uint16)
    if alpha < 0.997:
        a = (a * int(alpha * 256)) >> 8
    F = frame[y0:y1, x0:x1]
    F[:] = ((L[..., :3].astype(np.uint16) * a + F.astype(np.uint16) * (255 - a)) // 255).astype(np.uint8)
