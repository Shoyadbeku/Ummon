"""News-documentary renderer: draws every frame with PIL and pipes raw RGB to ffmpeg.
Usage: python3 render.py OUT.mp4 [start_frame end_frame]
"""
import sys, os, json, math, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

BASE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.dirname(BASE)
IMG = os.path.join(SCR, "img")
W, H, FPS = 1080, 1920, 30

# ---------------------------------------------------------------- style
NAVY = (9, 22, 44); NAVY2 = (16, 38, 72); WHITE = (255, 255, 255); OFF = (226, 232, 240)
RED = (226, 54, 54); BLUE = (30, 155, 215); GREEN = (40, 175, 90); GOLD = (245, 185, 50); GREY = (150, 160, 175)
FD = "/usr/share/fonts/opentype/inter/"

@functools.lru_cache(maxsize=None)
def F(size, weight="Bold"):
    return ImageFont.truetype(FD + f"Inter-{weight}.otf", size)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k
def prog(t, t0, dur): return ease((t - t0) / dur) if dur > 0 else (1.0 if t >= t0 else 0.0)
def fade(t, t_in, t_out=None, d=0.35):
    a = clamp((t - t_in) / d)
    if t_out is not None: a = min(a, clamp((t_out - t) / d))
    return a

# ---------------------------------------------------------------- word timings
TR = json.load(open(os.path.join(SCR, "tr_large.json")))
def seg(i): return TR[i]["start"]
def segend(i): return TR[i]["end"]
def wt(i, k): return TR[i]["words"][k][0]

# ---------------------------------------------------------------- photos & credits
CREDITS = {}

@functools.lru_cache(maxsize=None)
def have(k):
    p = os.path.join(IMG, k + ".jpg")
    if not os.path.exists(p): return False
    try:
        with Image.open(p) as im: im.load()
        return True
    except Exception:
        return False
def pick(*keys):
    for k in keys:
        if have(k): return k
    return None

def grade(im):
    im = ImageEnhance.Contrast(im).enhance(1.08)
    im = ImageEnhance.Color(im).enhance(0.92)
    a = np.asarray(im).astype(np.float32)
    # subtle teal shadows / warm highlights
    lum = a.mean(2, keepdims=True) / 255.0
    a[..., 2:3] += (1 - lum) * 10; a[..., 0:1] += lum * 6
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

BOTGRAD = None
def botgrad():
    global BOTGRAD
    if BOTGRAD is None:
        y = np.linspace(0, 1, H)[:, None, None]
        BOTGRAD = (1 - 0.7 * np.clip((y - 0.6) / 0.4, 0, 1) ** 1.3).astype(np.float32)
    return BOTGRAD
VIGNETTE = None
def vignette():
    global VIGNETTE
    if VIGNETTE is None:
        y, x = np.mgrid[0:H, 0:W]
        d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
        VIGNETTE = np.clip(1.0 - 0.38 * np.clip(d - 0.55, 0, None) ** 1.6, 0.55, 1)[..., None].astype(np.float32)
    return VIGNETTE

@functools.lru_cache(maxsize=None)
def load_photo(key, blur=0):
    im = Image.open(os.path.join(IMG, key + ".jpg")).convert("RGB")
    # cover 1920x1080 at zoom 1.25 headroom
    s = max(W * 1.25 / im.width, H * 1.25 / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    im = grade(im)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    return im

def ken_burns(key, t, t0, t1, z0=1.0, z1=1.12, c0=(0.5, 0.5), c1=(0.5, 0.5), blur=0):
    im = load_photo(key, blur)
    k = ease_io((t - t0) / max(0.01, t1 - t0))
    z = lerp(z0, z1, k); cx = lerp(c0[0], c1[0], k); cy = lerp(c0[1], c1[1], k)
    # base crop = largest 16:9 that fits, divided by zoom
    bw = min(im.width, im.height * W / H); bh = bw * H / W
    cw, ch = bw / z, bh / z
    x = clamp(cx * im.width - cw / 2, 0, im.width - cw); y = clamp(cy * im.height - ch / 2, 0, im.height - ch)
    return im.transform((W, H), Image.EXTENT, (x, y, x + cw, y + ch), Image.BILINEAR)

@functools.lru_cache(maxsize=None)
def bg_gradient():
    y = np.linspace(0, 1, H)[:, None, None]; x = np.linspace(0, 1, W)[None, :, None]
    a = np.array(NAVY, np.float32); b = np.array(NAVY2, np.float32)
    g = a + (b - a) * (0.6 * (1 - y) + 0.4 * x)
    im = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8))
    arr = np.asarray(im).astype(np.float32)
    grid = np.zeros((H, W), np.float32); grid[:, ::80] = 1; grid[::80, :] = 1
    arr += grid[..., None] * 3
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def darken(im, k):
    if k <= 0: return im
    return Image.blend(im, Image.new("RGB", im.size, NAVY), k)

# ---------------------------------------------------------------- drawing helpers
def text_w(s, f): return f.getlength(s)

def draw_text(d, xy, s, size, fill=WHITE, weight="Bold", anchor="la", alpha=1.0, shadow=True):
    f = F(size, weight)
    col = fill + (int(255 * alpha),)
    if shadow and alpha > 0:
        d.text((xy[0] + 2, xy[1] + 3), s, font=f, fill=(0, 0, 0, int(140 * alpha)), anchor=anchor)
    d.text(xy, s, font=f, fill=col, anchor=anchor)

def wrap(s, f, maxw):
    words = s.split(); lines = []; cur = ""
    for w_ in words:
        c = (cur + " " + w_).strip()
        if f.getlength(c) <= maxw: cur = c
        else:
            if cur: lines.append(cur)
            cur = w_
    if cur: lines.append(cur)
    return lines

def panel(d, box, alpha=1.0, fill=NAVY, radius=18, border=None):
    d.rounded_rectangle(box, radius=radius, fill=fill + (int(225 * alpha),),
                        outline=(border + (int(255 * alpha),)) if border else None, width=3 if border else 0)

def ring(d, cx, cy, r, frac, color, alpha, width=26):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, int(40 * alpha)), width=width)
    if frac > 0:
        d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * frac, fill=color + (int(255 * alpha),), width=width)

def fmt_int(n): return f"{int(round(n)):,}".replace(",", " ")

# ---------------------------------------------------------------- overlay elements (absolute times)
class El:
    def __init__(self, fn, t0, t1): self.fn, self.t0, self.t1 = fn, t0, t1

def E(t0, t1):
    def deco(fn): return El(fn, t0, t1)
    return deco

def headline(text, t0, t1, y=150, size=64, color=WHITE, tag=None, tagcol=RED):
    def fn(d, t):
        a = fade(t, t0, t1); k = prog(t, t0, 0.5)
        f = F(size, "ExtraBold"); lines = wrap(text, f, 1500)
        yy = y
        if tag:
            tw = text_w(tag, F(30, "Bold")) + 36
            x0 = W / 2 - tw / 2
            d.rectangle((x0, yy - 64, x0 + tw * k, yy - 18), fill=tagcol + (int(255 * a),))
            draw_text(d, (W / 2, yy - 41), tag, 30, anchor="mm", alpha=a * k, shadow=False)
        for ln in lines:
            draw_text(d, (W / 2, yy + (1 - k) * 30), ln, size, fill=color, anchor="ma", alpha=a)
            yy += size * 1.18
    return El(fn, t0, t1)

def lower_third(name, title, t0, t1):
    def fn(d, t):
        a = fade(t, t0, t1, 0.3); k = prog(t, t0, 0.6)
        x, y = 90, 800
        wname = text_w(name, F(44, "ExtraBold")); wt_ = text_w(title, F(28, "Medium"))
        wbox = max(wname, wt_) + 60
        d.rectangle((x, y, x + 10, y + 120), fill=RED + (int(255 * a),))
        d.rectangle((x + 10, y, x + 10 + wbox * k, y + 70), fill=(255, 255, 255, int(240 * a)))
        d.rectangle((x + 10, y + 70, x + 10 + wbox * k, y + 120), fill=NAVY + (int(235 * a),))
        if k > 0.6:
            aa = a * clamp((k - 0.6) / 0.4)
            d.text((x + 34, y + 35), name, font=F(44, "ExtraBold"), fill=NAVY + (int(255 * aa),), anchor="lm")
            d.text((x + 34, y + 95), title, font=F(28, "Medium"), fill=OFF + (int(255 * aa),), anchor="lm")
    return El(fn, t0, t1)

def stat_ring(cx, cy, pct, label, t0, t1, color=BLUE, r=150, size=88):
    def fn(d, t):
        a = fade(t, t0, t1); k = prog(t, t0, 1.4)
        ring(d, cx, cy, r, pct / 100 * k, color, a)
        draw_text(d, (cx, cy - 6), f"{round(pct * k)}%", size, anchor="mm", alpha=a)
        for i, ln in enumerate(wrap(label, F(30, "SemiBold"), 2 * r + 160)):
            draw_text(d, (cx, cy + r + 50 + i * 38), ln, 30, fill=OFF, weight="SemiBold", anchor="ma", alpha=a)
    return El(fn, t0, t1)

def counter(cx, cy, n, label, t0, t1, prefix="", suffix="", size=120, color=WHITE, dur=1.2, sub_size=34):
    def fn(d, t):
        a = fade(t, t0, t1); k = prog(t, t0, dur)
        draw_text(d, (cx, cy), prefix + fmt_int(n * k) + suffix, size, fill=color, weight="ExtraBold", anchor="mm", alpha=a)
        for i, ln in enumerate(wrap(label, F(sub_size, "SemiBold"), 620)):
            draw_text(d, (cx, cy + size * 0.62 + 10 + i * sub_size * 1.25), ln, sub_size, fill=OFF, weight="SemiBold", anchor="ma", alpha=a)
    return El(fn, t0, t1)

def card(x, y, w, title, body, t0, t1, accent=BLUE, icon=None, title_size=40, body_size=30):
    def fn(d, t):
        a = fade(t, t0, t1); k = prog(t, t0, 0.5)
        yy = y + (1 - k) * 40
        bl = wrap(body, F(body_size, "Medium"), w - 60) if body else []
        tl = wrap(title, F(title_size, "ExtraBold"), w - 60)
        h = 40 + len(tl) * title_size * 1.2 + (16 + len(bl) * body_size * 1.3 if bl else 0) + 30
        panel(d, (x, yy, x + w, yy + h), a * 0.95)
        d.rectangle((x, yy, x + 10, yy + h), fill=accent + (int(255 * a),))
        cy = yy + 36
        for ln in tl:
            draw_text(d, (x + 36, cy), ln, title_size, weight="ExtraBold", alpha=a, shadow=False); cy += title_size * 1.2
        cy += 16
        for ln in bl:
            draw_text(d, (x + 36, cy), ln, body_size, fill=OFF, weight="Medium", alpha=a, shadow=False); cy += body_size * 1.3
    return El(fn, t0, t1)

def bumper(text, t0, t1, sub=None, color=RED):
    def fn(d, t):
        a = fade(t, t0, t1, 0.25); k = prog(t, t0, 0.45)
        f = F(96, "Black"); tw = text_w(text, f)
        d.rectangle((W / 2 - (tw / 2 + 50) * k, H / 2 - 90, W / 2 + (tw / 2 + 50) * k, H / 2 + 70), fill=color + (int(235 * a),))
        draw_text(d, (W / 2, H / 2 - 10), text, 96, weight="Black", anchor="mm", alpha=a * clamp(k * 1.5))
        if sub: draw_text(d, (W / 2, H / 2 + 120), sub, 40, fill=OFF, weight="SemiBold", anchor="mm", alpha=a)
    return El(fn, t0, t1)

def quote(text, src, t0, t1, y=330, size=56):
    def fn(d, t):
        a = fade(t, t0, t1); k = prog(t, t0, 0.6)
        lines = wrap(text, F(size, "Bold"), 1450)
        draw_text(d, (200, y - 40), "“", 200, fill=RED, weight="Black", alpha=a, shadow=False)
        yy = y + 60
        for i, ln in enumerate(lines):
            kk = prog(t, t0 + 0.15 * i, 0.5)
            draw_text(d, (240 + (1 - kk) * 40, yy), ln, size, alpha=a * kk); yy += size * 1.3
        draw_text(d, (240, yy + 24), src, 28, fill=GREY, weight="Medium", alpha=a)
    return El(fn, t0, t1)

def chip(text, x, y, t0, t1, color=BLUE, size=36, anchor="l"):
    def fn(d, t):
        a = fade(t, t0, t1); k = prog(t, t0, 0.4)
        f = F(size, "Bold"); tw = text_w(text, f) + 50; h = size * 1.7
        x0 = x if anchor == "l" else x - tw / 2
        d.rounded_rectangle((x0, y, x0 + tw * k, y + h), radius=h / 2, fill=color + (int(240 * a),))
        if k > 0.5: d.text((x0 + 25, y + h / 2), text, font=f, fill=(255, 255, 255, int(255 * a * clamp((k - .5) * 2))), anchor="lm")
    return El(fn, t0, t1)

def group(*els): return list(els)

# ---- special graphics
def years_blocks(t0, t1, mode="intro", y=520):
    """11 grade blocks; new 'Tayyorlov' block slides in at the START."""
    def fn(d, t):
        a = fade(t, t0, t1); bw, gap = 118, 12
        n = 12; total_w = n * bw + (n - 1) * gap; x0 = (W - total_w) / 2
        kin = prog(t, t0 + 1.0, 0.8) if mode == "intro" else 1.0
        for i in range(11):
            x = x0 + (bw + gap) * (i + kin)
            appear = prog(t, t0 + 0.04 * i, 0.4)
            d.rounded_rectangle((x, y + (1 - appear) * 30, x + bw, y + 150 + (1 - appear) * 30), radius=12,
                                fill=NAVY2 + (int(240 * a * appear),), outline=(255, 255, 255, int(70 * a)), width=2)
            draw_text(d, (x + bw / 2, y + 75), f"{i + 1}", 56, anchor="mm", alpha=a * appear, shadow=False)
            draw_text(d, (x + bw / 2, y + 128), "sinf", 22, fill=GREY, weight="Medium", anchor="mm", alpha=a * appear, shadow=False)
        # crossed "12-sinf" ghost at end (myth)
        if mode == "intro":
            gx = x0 + 11 * (bw + gap) + (bw + gap) * 1.0
            ga = a * (1 - prog(t, t0 + 0.9, 0.4)) * prog(t, t0 + 0.1, 0.3)
            if ga > 0.01:
                d.rounded_rectangle((gx - (bw + gap), y, gx - gap, y + 150), radius=12, outline=(255, 255, 255, int(120 * ga)), width=3)
                draw_text(d, (gx - (bw + gap) + bw / 2, y + 75), "12?", 46, fill=GREY, anchor="mm", alpha=ga, shadow=False)
        # new block at start
        k = kin
        if k > 0:
            x = x0 - (1 - k) * 300
            d.rounded_rectangle((x, y - 10, x + bw, y + 160), radius=12, fill=GOLD + (int(255 * a * k),))
            draw_text(d, (x + bw / 2, y + 60), "+1", 54, fill=NAVY, weight="Black", anchor="mm", alpha=a * k, shadow=False)
            draw_text(d, (x + bw / 2, y + 118), "tayyorlov", 20, fill=NAVY, weight="Bold", anchor="mm", alpha=a * k, shadow=False)
            draw_text(d, (x + bw / 2, y + 205), "6 yosh", 30, fill=GOLD, anchor="mm", alpha=a * k)
            # arrow
            d.line((x + bw / 2, y - 30, x + bw / 2, y - 80), fill=GOLD + (int(255 * a * k),), width=5)
            draw_text(d, (x + bw / 2 + 30, y - 110), "Yangi yil — BOSHIDA", 40, fill=GOLD, weight="ExtraBold", anchor="lm", alpha=a * k)
    return El(fn, t0, t1)

def structure_bar(t0, t1, marks):
    """1+4+5+2 stacked bar; marks = start times for each segment."""
    parts = [(1, "Tayyorlov", GOLD), (4, "Boshlang‘ich", BLUE), (5, "Tayanch", GREEN), (2, "Yuqori sinflar", RED)]
    def fn(d, t):
        a = fade(t, t0, t1); x0, y, wtot, h = 160, 470, 1600, 150
        draw_text(d, (W / 2, 300), "12 YILLIK TIZIM TUZILMASI", 54, weight="ExtraBold", anchor="mm", alpha=a)
        draw_text(d, (W / 2, 365), "2025-yil sentyabrda e’lon qilingan taklif", 30, fill=GREY, weight="Medium", anchor="mm", alpha=a)
        x = x0
        for (n, lbl, col), tm in zip(parts, marks):
            w_ = wtot * n / 12; k = prog(t, tm, 0.5)
            if k > 0:
                d.rectangle((x, y, x + w_ * k - 6, y + h), fill=col + (int(250 * a),))
                if k > 0.7:
                    draw_text(d, (x + w_ / 2, y + h / 2), f"{n}", 70, fill=WHITE if col != GOLD else NAVY, weight="Black", anchor="mm", alpha=a, shadow=False)
                    draw_text(d, (x + w_ / 2, y + h + 50), lbl, 32, weight="Bold", anchor="mm", alpha=a)
                    draw_text(d, (x + w_ / 2, y + h + 92), "yil", 26, fill=GREY, weight="Medium", anchor="mm", alpha=a)
            x += w_
    return El(fn, t0, t1)

def history(t0, t1, m2, m3):
    def fn(d, t):
        a = fade(t, t0, t1)
        rows = [(t0, "2017-yilgacha", [(9, "maktab", BLUE), (3, "kollej / litsey", GREEN)], "= 12"),
                (m2, "2017-yildan", [(11, "maktab", BLUE)], "= 11"),
                (m3, "Endi", [(1, "+1", GOLD), (11, "maktab", BLUE)], "= 12")]
        y = 260
        for tm, lab, parts, res in rows:
            k = prog(t, tm, 0.6);
            if k <= 0: y += 230; continue
            draw_text(d, (150, y + 50), lab, 40, weight="ExtraBold", anchor="lm", alpha=a * k)
            x = 520; unit = 86
            for n, l, c in parts:
                w_ = unit * n * k
                d.rectangle((x, y, x + w_ - 6, y + 100), fill=c + (int(240 * a),))
                if k > 0.8:
                    draw_text(d, (x + w_ / 2, y + 50), l if l == "+1" else f"{n} · {l}", 30, fill=NAVY if c == GOLD else WHITE, weight="Bold", anchor="mm", alpha=a, shadow=False)
                x += unit * n
            draw_text(d, (x + 30, y + 50), res, 54, fill=GOLD if res == "= 12" else OFF, weight="Black", anchor="lm", alpha=a * k)
            y += 230
    return El(fn, t0, t1)

def flow(t0, t1, steps, y=470, marks=None, title=None, done=None):
    """Horizontal process boxes with arrows. steps=[(title, sub, color)]"""
    def fn(d, t):
        a = fade(t, t0, t1); n = len(steps); bw, gap = 380, 90
        x0 = (W - (n * bw + (n - 1) * gap)) / 2
        if title: draw_text(d, (W / 2, y - 150), title, 54, weight="ExtraBold", anchor="mm", alpha=a)
        for i, (tt, sub, col) in enumerate(steps):
            tm = marks[i] if marks else t0 + 0.3 * i
            k = prog(t, tm, 0.5)
            if k <= 0: continue
            x = x0 + i * (bw + gap)
            panel(d, (x, y + (1 - k) * 30, x + bw, y + 220 + (1 - k) * 30), a * k, border=col)
            tl = wrap(tt, F(40, "ExtraBold"), bw - 40); sl = wrap(sub, F(26, "Medium"), bw - 40) if sub else []
            hh = len(tl) * 46 + (12 + len(sl) * 32 if sl else 0)
            yy = y + (1 - k) * 30 + 110 - hh / 2 + 23
            for j, ln in enumerate(tl):
                draw_text(d, (x + bw / 2, yy + j * 46), ln, 40, weight="ExtraBold", anchor="mm", alpha=a * k, shadow=False)
            yy += len(tl) * 46 + 12 - 23 + 16
            for j, ln in enumerate(sl):
                draw_text(d, (x + bw / 2, yy + j * 32), ln, 26, fill=OFF, weight="Medium", anchor="mm", alpha=a * k, shadow=False)
            if done and i < len(done) and done[i]:
                d.ellipse((x + bw - 50, y - 20, x + bw + 10, y + 40), fill=GREEN + (int(255 * a * k),))
                draw_text(d, (x + bw - 20, y + 10), "✓", 36, anchor="mm", alpha=a * k, shadow=False, weight="Black")
            if i < n - 1:
                ka = prog(t, tm + 0.3, 0.4)
                ax = x + bw + 12
                d.line((ax, y + 110, ax + (gap - 24) * ka, y + 110), fill=(255, 255, 255, int(200 * a)), width=6)
                if ka > 0.9: d.polygon([(ax + gap - 24, y + 96), (ax + gap - 6, y + 110), (ax + gap - 24, y + 124)], fill=(255, 255, 255, int(200 * a)))
    return El(fn, t0, t1)

GEO = json.load(open(os.path.join(SCR, "geo", "uzb.json")))["features"][0]["geometry"]["coordinates"][0]
def uz_map(t0, t1, cx=1400, cy=560, scale=34, label=None, box=False):
    def fn(d, t):
        a = fade(t, t0, t1); k = prog(t, t0, 1.0)
        if box:
            panel(d, (cx - 15 * scale * 0.76, cy - 6.5 * scale, cx + 14 * scale * 0.76, cy + 6.5 * scale), a * 0.95)
        lon0, lat0 = 64.5, 41.4
        pts = [(cx + (lo - lon0) * scale * math.cos(math.radians(41)), cy - (la - lat0) * scale) for lo, la in GEO]
        npts = max(2, int(len(pts) * k))
        if box: d.polygon(pts, fill=NAVY2 + (int(255 * a),))
        d.polygon(pts, fill=BLUE + (int(60 * a * k),))
        d.line(pts[:npts] + ([pts[0]] if k >= 1 else []), fill=BLUE + (int(255 * a),), width=4)
        if label: draw_text(d, (cx, cy + 240), label, 30, fill=OFF, weight="SemiBold", anchor="mm", alpha=a)
    return El(fn, t0, t1)

WORLD = None
def world_map(t0, t1, alpha=0.35):
    global WORLD
    if WORLD is None:
        g = json.load(open(os.path.join(SCR, "geo", "world.json")))
        polys = []
        for f in g["features"]:
            geo = f["geometry"]; cs = geo["coordinates"]
            rings = [cs[0]] if geo["type"] == "Polygon" else [p[0] for p in cs]
            for r in rings:
                polys.append([((lo + 180) / 360 * W, (90 - la) / 180 * H * 1.0 + 40) for lo, la in r if la > -60])
        WORLD = polys
    def fn(d, t):
        a = fade(t, t0, t1, 0.6)
        for p in WORLD:
            if len(p) > 2: d.polygon(p, fill=(60, 110, 170, int(255 * alpha * a)), outline=(120, 170, 230, int(255 * alpha * a)))
    return El(fn, t0, t1)

def checklist(items, t0, t1, x=260, y=330, title=None):
    """items=[(text, mark, t_in)] mark in {'?','✓','!'}"""
    def fn(d, t):
        a = fade(t, t0, t1)
        if title: draw_text(d, (x, y - 110), title, 54, weight="ExtraBold", alpha=a)
        yy = y
        for text, mark, tin in items:
            k = prog(t, tin, 0.5)
            if k <= 0: yy += 140; continue
            col = {"?": GOLD, "✓": GREEN, "!": RED}[mark]
            d.ellipse((x, yy, x + 80, yy + 80), fill=col + (int(255 * a * k),))
            draw_text(d, (x + 40, yy + 40), mark, 46, fill=NAVY, weight="Black", anchor="mm", alpha=a * k, shadow=False)
            for j, ln in enumerate(wrap(text, F(44, "Bold"), 1300)):
                draw_text(d, (x + 120 + (1 - k) * 40, yy + 40 + j * 52), ln, 44, anchor="lm", alpha=a * k)
            yy += 140
    return El(fn, t0, t1)

def stamp(text, t0, t1, sub=None, color=GREEN):
    def fn(d, t):
        a = fade(t, t0, t1); k = prog(t, t0, 0.35)
        s = lerp(2.2, 1.0, k); size = int(150 * s)
        draw_text(d, (W / 2, H / 2 - 40), text, size, fill=color, weight="Black", anchor="mm", alpha=a * clamp(k * 2))
        if sub: draw_text(d, (W / 2, H / 2 + 90), sub, 44, fill=WHITE, weight="SemiBold", anchor="mm", alpha=a * k)
    return El(fn, t0, t1)

# ---------------------------------------------------------------- shots
class Shot:
    def __init__(self, t0, t1, bg, credit=None, els=(), trans="fade", ticker=True):
        self.t0, self.t1, self.bg, self.credit, self.els, self.trans, self.ticker = t0, t1, bg, credit, list(els), trans, ticker

def P(key, z0=1.0, z1=1.12, c0=(0.5, 0.5), c1=(0.5, 0.5), dark=0.0, blur=0):
    if key is None or not have(key):
        return G()
    def bg(t, sh):
        im = ken_burns(key, t, sh.t0, sh.t1, z0, z1, c0, c1, blur)
        return darken(im, dark)
    bg.key = key
    return bg

def G(dark_photo=None, dark=0.78, blur=10):
    def bg(t, sh):
        if dark_photo and have(dark_photo):
            return darken(ken_burns(dark_photo, t, sh.t0, sh.t1, 1.05, 1.12, blur=blur), dark)
        return bg_gradient().copy()
    bg.key = dark_photo if (dark_photo and have(dark_photo)) else None
    return bg

def cred(bgfn, override=None):
    if override: return override
    k = getattr(bgfn, "key", None)
    return CREDITS.get(k) if k else None


# ======================= v2: Sindarov – Gukesh (World Chess Championship 2026) =======================
AUDIO_END = 345.40
TOTAL = AUDIO_END + 8.0

CREDITS = {
    "sind_olymp45": "ARXIV: 45-OLIMPIADA, 2024 · FOTO: MiroJP / Wikimedia Commons · CC BY-SA 4.0",
    "sind_46": "ARXIV: 46-OLIMPIADA, SAMARQAND, 2026 · FOTO: TheBoburshokh / Wikimedia Commons · CC BY 4.0",
    "sind_br": "ARXIV · FOTO: Bunyod Rustamov / Wikimedia Commons · CC BY 4.0",
    "sind_tb": "ARXIV · FOTO: TheBoburshokh / Wikimedia Commons · CC BY 4.0",
    "sind_tata": "ARXIV: TATA STEEL, 2023 · FOTO: Frans Peeters / Wikimedia Commons · CC BY-SA 2.0",
    "sind_ha": "ARXIV · FOTO: Husniddin Ato / Wikimedia Commons · CC BY-SA 4.0",
    "naro1": "ARXIV: NARODITSKY MEMORIAL, 2026 · FOTO: ChessKelly / Wikimedia Commons · CC BY 4.0",
    "guk24": "ARXIV, 2024 · FOTO: Frans Peeters / Wikimedia Commons · CC BY-SA 2.0",
    "guk25": "ARXIV, 2025 · FOTO: Frans Peeters / Wikimedia Commons · CC BY-SA 2.0",
    "guk_tata24": "ARXIV: TATA STEEL, 2024 · FOTO: Frans Peeters / Wikimedia Commons · CC BY-SA 2.0",
    "guk_cand1": "ARXIV: NOMZODLAR TURNIRI, 2024 · FOTO: Eldar Azimov / Wikimedia Commons · CC BY-SA 4.0",
    "guk_cand3": "ARXIV: NOMZODLAR TURNIRI, 2024 · FOTO: Eldar Azimov / Wikimedia Commons · CC BY-SA 4.0",
    "bodmer": "KOLONYI, MARTIN BODMER JAMG‘ARMASI · FOTO: Alpra ArazeL / Wikimedia Commons · CC BY-SA 4.0",
    "bodmer2": "KOLONYI, MARTIN BODMER JAMG‘ARMASI, 2014 · FOTO: Jacklee / Wikimedia Commons · CC BY-SA 3.0",
    "bodmer3": "KOLONYI, MARTIN BODMER JAMG‘ARMASI, 2014 · FOTO: Jacklee / Wikimedia Commons · CC BY-SA 3.0",
    "bodmer_view": "KOLONYIDAN JENEVA KO‘LIGA KO‘RINISH, 2014 · FOTO: Jacklee / Wikimedia Commons · CC BY-SA 3.0",
    "bodmer_view2": "KOLONYIDAN JENEVA KO‘LIGA KO‘RINISH, 2014 · FOTO: Jacklee / Wikimedia Commons · CC BY-SA 3.0",
    "team44": "ARXIV: 44-OLIMPIADA, 2022 · FOTO: Yoshlar ishlari agentligi / Wikimedia Commons · CC BY-SA 4.0",
    "team44b": "ARXIV: 44-OLIMPIADA, 2022 · FOTO: Yoshlar ishlari agentligi / Wikimedia Commons · CC BY-SA 4.0",
    "team46": "ARXIV: 46-OLIMPIADA, SAMARQAND, 2026 · FOTO: TheBoburshokh / Wikimedia Commons · CC BY 4.0",
    "carlsen": "ARXIV, 2025 · FOTO: Miroslav Vajdic / Wikimedia Commons · CC BY 4.0",
    "weiyi": "ARXIV, 2024 · FOTO: Frans Peeters / Wikimedia Commons · CC BY-SA 2.0",
    "weiyi26": "ARXIV: OLIMPIADA, 2026 · FOTO: Yunfan Zhao / Lichess / Wikimedia Commons · CC BY-SA 4.0",
}

UZ = (30, 155, 215); IN = (255, 153, 51)
PIECE_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
@functools.lru_cache(maxsize=None)
def PF(size): return ImageFont.truetype(PIECE_FONT, size)
GLYPH = {"k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟"}

def fen_board(fen):
    rows = fen.split()[0].split("/"); b = {}
    for r, row in enumerate(rows):
        c = 0
        for ch in row:
            if ch.isdigit(): c += int(ch)
            else: b[(r, c)] = ch; c += 1
    return b

def chessboard(fen, t0, t1, x=160, y=150, size=760, highlight=(), title=None, sub=None, arrows=()):
    """Accurate position diagram from FEN; highlighted squares e.g. ('e4','f6')."""
    B = fen_board(fen); sq = size / 8
    def rc(s): return 8 - int(s[1]), "abcdefgh".index(s[0])
    hl = {rc(s) for s in highlight}
    def fn(d, t):
        a = fade(t, t0, t1); k = prog(t, t0, 0.5)
        panel(d, (x - 30, y - 30, x + size + 30, y + size + 30), a, radius=12)
        for r in range(8):
            for c in range(8):
                light = (r + c) % 2 == 0
                col = (232, 220, 196) if light else (150, 112, 82)
                if (r, c) in hl: col = (246, 214, 92) if light else (214, 176, 60)
                d.rectangle((x + c * sq, y + r * sq, x + (c + 1) * sq, y + (r + 1) * sq), fill=col + (int(255 * a),))
        for i in range(8):
            d.text((x - 18, y + i * sq + sq / 2), str(8 - i), font=F(20, "SemiBold"), fill=OFF + (int(200 * a),), anchor="mm")
            d.text((x + i * sq + sq / 2, y + size + 16), "abcdefgh"[i], font=F(20, "SemiBold"), fill=OFF + (int(200 * a),), anchor="mm")
        n = 0
        for (r, c), p in sorted(B.items()):
            n += 1; kk = prog(t, t0 + 0.15 + 0.012 * n, 0.3)
            if kk <= 0: continue
            g = GLYPH[p.lower()]; cx, cy = x + c * sq + sq / 2, y + r * sq + sq / 2 + 4
            if p.isupper():
                d.text((cx, cy), g, font=PF(int(sq * 0.82)), fill=(255, 255, 255, int(255 * a * kk)), anchor="mm", stroke_width=3, stroke_fill=(20, 20, 20, int(255 * a * kk)))
            else:
                d.text((cx, cy), g, font=PF(int(sq * 0.82)), fill=(20, 20, 20, int(255 * a * kk)), anchor="mm", stroke_width=1, stroke_fill=(250, 250, 250, int(160 * a * kk)))
        for (s1, s2, tin) in arrows:
            ka = prog(t, tin, 0.4)
            if ka <= 0: continue
            r1, c1 = rc(s1); r2, c2 = rc(s2)
            p1 = (x + c1 * sq + sq / 2, y + r1 * sq + sq / 2); p2 = (x + c2 * sq + sq / 2, y + r2 * sq + sq / 2)
            pe = (lerp(p1[0], p2[0], ka), lerp(p1[1], p2[1], ka))
            d.line((p1, pe), fill=(40, 175, 90, int(220 * a)), width=12)
        if title: draw_text(d, (x + size + 90, y + 40), title, 56, weight="ExtraBold", alpha=a)
        if sub:
            for i, ln in enumerate(wrap(sub, F(32, "Medium"), 820)):
                draw_text(d, (x + size + 90, y + 120 + i * 42), ln, 32, fill=OFF, weight="Medium", alpha=a)
    return El(fn, t0, t1)

def flag(d, kind, x, y, w, h, a):
    if kind == "UZ":
        d.rectangle((x, y, x + w, y + h / 3), fill=(0, 153, 181, int(255 * a)))
        d.rectangle((x, y + h / 3, x + w, y + 2 * h / 3), fill=(255, 255, 255, int(255 * a)))
        d.rectangle((x, y + 2 * h / 3, x + w, y + h), fill=(30, 181, 58, int(255 * a)))
        d.rectangle((x, y + h / 3 - 2, x + w, y + h / 3 + 2), fill=(206, 17, 38, int(255 * a)))
        d.rectangle((x, y + 2 * h / 3 - 2, x + w, y + 2 * h / 3 + 2), fill=(206, 17, 38, int(255 * a)))
    else:
        d.rectangle((x, y, x + w, y + h / 3), fill=(255, 153, 51, int(255 * a)))
        d.rectangle((x, y + h / 3, x + w, y + 2 * h / 3), fill=(255, 255, 255, int(255 * a)))
        d.rectangle((x, y + 2 * h / 3, x + w, y + h), fill=(19, 136, 8, int(255 * a)))
        r = h / 7; d.ellipse((x + w / 2 - r, y + h / 2 - r, x + w / 2 + r, y + h / 2 + r), outline=(0, 0, 128, int(255 * a)), width=2)

def scoreboard(t0, t1, s1="1", s2="1", y=380, sub=None, scale=1.0):
    def fn(d, t):
        a = fade(t, t0, t1); k = prog(t, t0, 0.5)
        w = 1400 * scale; x0 = W / 2 - w / 2; h = 220 * scale
        panel(d, (x0, y, x0 + w, y + h), a)
        flag(d, "UZ", x0 + 40 * scale, y + 70 * scale, 120 * scale, 80 * scale, a)
        flag(d, "IN", x0 + w - 160 * scale, y + 70 * scale, 120 * scale, 80 * scale, a)
        draw_text(d, (x0 + 190 * scale, y + h / 2), "SINDAROV", int(56 * scale), weight="ExtraBold", anchor="lm", alpha=a, shadow=False)
        draw_text(d, (x0 + w - 190 * scale, y + h / 2), "GUKESH", int(56 * scale), weight="ExtraBold", anchor="rm", alpha=a, shadow=False)
        draw_text(d, (W / 2, y + h / 2), f"{s1} — {s2}", int(lerp(160, 110, k) * scale), fill=GOLD, weight="Black", anchor="mm", alpha=a, shadow=False)
        if sub: draw_text(d, (W / 2, y + h + 50 * scale), sub, int(38 * scale), fill=OFF, weight="SemiBold", anchor="mm", alpha=a)
    return El(fn, t0, t1)

def split_bg(kl, kr):
    def bg(t, sh):
        im = Image.new("RGB", (W, H), NAVY)
        for i, k in enumerate((kl, kr)):
            if k and have(k):
                ph = ken_burns(k, t, sh.t0, sh.t1, 1.0, 1.08, (0.5, 0.4), (0.5, 0.42))
                half = ph.crop((W / 4, 0, W * 3 / 4, H)).resize((W // 2, H))
                im.paste(half, (i * W // 2, 0))
        d = ImageDraw.Draw(im); d.rectangle((W / 2 - 4, 0, W / 2 + 4, H), fill=GOLD)
        return im
    bg.key = None; bg.keys = [k for k in (kl, kr) if k and have(k)]
    return bg

WORLDP = None
def geo_map(t0, t1, lon0, lat0, scale, dots=(), title=None, alpha=1.0):
    """Equirectangular zoomed map; dots=[(lon, lat, label, t_in)]."""
    global WORLDP
    if WORLDP is None:
        g = json.load(open(os.path.join(SCR, "geo", "world.json"))); WORLDP = []
        for f in g["features"]:
            geo = f["geometry"]; cs = geo["coordinates"]
            rings = [cs[0]] if geo["type"] == "Polygon" else [p[0] for p in cs]
            for r in rings: WORLDP.append((r, min(p[0] for p in r), max(p[0] for p in r), min(p[1] for p in r), max(p[1] for p in r)))
    def P_(lo, la): return (W / 2 + (lo - lon0) * scale, H / 2 - (la - lat0) * scale * 1.15)
    def fn(d, t):
        a = fade(t, t0, t1, 0.5) * alpha
        lmin, lmax = lon0 - W / 2 / scale - 2, lon0 + W / 2 / scale + 2
        amin, amax = lat0 - H / 2 / scale - 2, lat0 + H / 2 / scale + 2
        for r, x0, x1, y0, y1 in WORLDP:
            if x1 < lmin or x0 > lmax or y1 < amin or y0 > amax: continue
            d.polygon([P_(lo, la) for lo, la in r], fill=(38, 78, 130, int(255 * a)), outline=(110, 160, 220, int(255 * a)))
        for lo, la, lab, tin in dots:
            k = prog(t, tin, 0.5)
            if k <= 0: continue
            px, py = P_(lo, la); rr = 12 + 26 * (1 - k)
            d.ellipse((px - rr, py - rr, px + rr, py + rr), outline=GOLD + (int(255 * a * k),), width=4)
            d.ellipse((px - 9, py - 9, px + 9, py + 9), fill=RED + (int(255 * a * k),))
            draw_text(d, (px + 26, py - 4), lab, 40, weight="ExtraBold", anchor="lm", alpha=a * k)
        if title: draw_text(d, (W / 2, 120), title, 60, weight="ExtraBold", anchor="mm", alpha=a)
    return El(fn, t0, t1)

def calendar(t0, t1, focus=()):
    """24 Nov – 12 Dec 2026. focus=[(day_key, t_in)] e.g. ('27N', 273.4)."""
    days = [("24N", "24", "1"), ("25N", "25", "2"), ("26N", "26", "3"), ("27N", "27", "DAM"), ("28N", "28", "4"), ("29N", "29", "5"),
            ("30N", "30", "6"), ("01D", "1", "DAM"), ("02D", "2", "7"), ("03D", "3", "8"), ("04D", "4", "9"), ("05D", "5", "DAM"),
            ("06D", "6", "10"), ("07D", "7", "11"), ("08D", "8", "12"), ("09D", "9", "DAM"), ("10D", "10", "13"), ("11D", "11", "14"), ("12D", "12", "TB")]
    # 24 Nov 2026 is a Tuesday -> column 1 (Mon=0)
    def fn(d, t):
        a = fade(t, t0, t1); cw, ch = 200, 140; x0 = (W - 7 * cw) / 2; y0 = 250
        for i, nm in enumerate(["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]):
            draw_text(d, (x0 + i * cw + cw / 2, y0 - 40), nm, 30, fill=GREY, weight="SemiBold", anchor="mm", alpha=a)
        fk = {k: tin for k, tin in focus}
        for n, (key, dd, g) in enumerate(days):
            idx = n + 1; c = idx % 7; r = idx // 7
            k = prog(t, t0 + 0.03 * n, 0.3)
            x, y = x0 + c * cw, y0 + r * ch
            col = NAVY2 if g not in ("DAM", "TB") else ((60, 70, 90) if g == "DAM" else RED)
            hi = key in fk and t >= fk[key]
            d.rounded_rectangle((x + 6, y + 6, x + cw - 6, y + ch - 6), radius=12, fill=col + (int(240 * a * k),),
                                outline=(GOLD + (int(255 * a),)) if hi else (255, 255, 255, int(40 * a)), width=6 if hi else 2)
            mon = "noy" if key.endswith("N") else "dek"
            draw_text(d, (x + 22, y + 30), f"{dd} {mon}", 26, fill=OFF, weight="SemiBold", anchor="lm", alpha=a * k, shadow=False)
            lab = {"DAM": "dam olish", "TB": "tay-brek"}.get(g, f"{g}-partiya")
            draw_text(d, (x + cw / 2, y + 88), lab, 34 if g not in ("DAM", "TB") else 30, weight="ExtraBold", anchor="mm", alpha=a * k, shadow=False,
                      fill=GOLD if hi else WHITE)
    return El(fn, t0, t1)

def rating_bars(t0, t1):
    def fn(d, t):
        a = fade(t, t0, t1); lo, hi = 2600, 2800; x0, wmax = 520, 1180
        draw_text(d, (W / 2, 190), "FIDE REYTINGI · NOYABR 2026", 50, weight="ExtraBold", anchor="mm", alpha=a)
        rows = [("Sindarov", 2782, UZ, t0 + 0.3, "dunyoda 4-o‘rin"), ("Gukesh", 2700, IN, t0 + 4.6, "≈ 2700")]
        for i, (nm, v, col, tin, note) in enumerate(rows):
            k = prog(t, tin, 1.0); y = 360 + i * 230
            if k <= 0: continue
            draw_text(d, (x0 - 40, y + 50), nm, 52, weight="ExtraBold", anchor="rm", alpha=a)
            d.rectangle((x0, y, x0 + wmax * (v - lo) / (hi - lo) * k, y + 100), fill=col + (int(240 * a),))
            draw_text(d, (x0 + wmax * (v - lo) / (hi - lo) * k + 20, y + 50), f"{'' if i == 0 else '≈'}{int(lo + (v - lo) * k)}", 56, fill=GOLD, weight="Black", anchor="lm", alpha=a)
            draw_text(d, (x0, y + 140), note, 32, fill=OFF, weight="SemiBold", alpha=a * k)
        draw_text(d, (x0, 860), "shkala 2600 dan boshlanadi", 22, fill=GREY, weight="Medium", alpha=a)
    return El(fn, t0, t1)

def h2h(t0, t1, marks):
    res = [("G‘", GREEN, "Sindarov yutdi"), ("G‘", GREEN, "Sindarov yutdi"), ("½", GREY, "durang")]
    def fn(d, t):
        a = fade(t, t0, t1)
        draw_text(d, (W / 2, 200), "KLASSIK SHAXMATDA O‘ZARO UCHRASHUVLAR", 50, weight="ExtraBold", anchor="mm", alpha=a)
        for i, ((s, col, lab), tin) in enumerate(zip(res, marks)):
            k = prog(t, tin, 0.4)
            if k <= 0: continue
            cx = W / 2 + (i - 1) * 380; cy = 480; r = 130 * (0.6 + 0.4 * k)
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col + (int(240 * a),))
            draw_text(d, (cx, cy), s, 110, weight="Black", anchor="mm", alpha=a, shadow=False)
            draw_text(d, (cx, cy + 190), lab, 34, fill=OFF, weight="SemiBold", anchor="mm", alpha=a)
        if len(marks) > 3 and t >= marks[3]:
            draw_text(d, (W / 2, 820), "Sindarov 2 · durang 1 · Gukesh 0", 48, fill=GOLD, weight="ExtraBold", anchor="mm", alpha=a * prog(t, marks[3], 0.4))
    return El(fn, t0, t1)

def titles_split(t0, t1, ttl, ttr, tl=None, tr=None):
    def fn(d, t):
        for (txt, sub, x, tin) in ((ttl, tl, W / 4, t0), (ttr, tr, 3 * W / 4, t0 + 0.25)):
            if not txt: continue
            a = fade(t, tin, t1); k = prog(t, tin, 0.4)
            f = F(54, "ExtraBold"); tw = f.getlength(txt) + 60
            d.rectangle((x - tw / 2, 760, x - tw / 2 + tw * k, 840), fill=NAVY + (int(230 * a),))
            if k > 0.5: draw_text(d, (x, 800), txt, 54, weight="ExtraBold", anchor="mm", alpha=a)
            if sub: draw_text(d, (x, 880), sub, 34, fill=GOLD, weight="Bold", anchor="mm", alpha=a)
    return El(fn, t0, t1)

def big(text, t0, t1, y=None, size=140, color=WHITE, sub=None):
    def fn(d, t):
        a = fade(t, t0, t1); k = prog(t, t0, 0.4)
        yy = (H / 2 - 40) if y is None else y
        draw_text(d, (W / 2, yy + (1 - k) * 30), text, size, fill=color, weight="Black", anchor="mm", alpha=a)
        if sub:
            for i, ln in enumerate(wrap(sub, F(44, "SemiBold"), 1500)):
                draw_text(d, (W / 2, yy + size * 0.75 + i * 56), ln, 44, fill=OFF, weight="SemiBold", anchor="mm", alpha=a)
    return El(fn, t0, t1)

def build():
    S = []
    def add(t0, t1, bg, els=(), credit=None, trans="fade", ticker=True):
        c = credit if credit is not None else cred(bg)
        if c is None and getattr(bg, "keys", None):
            c = "  |  ".join(CREDITS[k].replace(" / Wikimedia Commons", "") for k in bg.keys)
        S.append(Shot(t0, t1, bg, c, els, trans, ticker))
    sind = pick("sind_olymp45", "sind_46", "sind_br", "sind_tb")
    sind2 = pick("sind_46", "sind_br", "sind_tb", "sind_ha", "sind_olymp45")
    sind3 = pick("sind_br", "sind_tb", "sind_ha", "naro1", "sind_46")
    sind_young = pick("sind_tata", "sind_ha")
    guk = pick("guk24", "guk_tata24", "guk25")
    guk2 = pick("guk_cand1", "guk_cand3", "guk25", "guk_tata24")
    guk3 = pick("guk25", "guk_cand3", "guk_tata24", "guk24")
    bod = pick("bodmer", "bodmer2", "bodmer3")
    bod2 = pick("bodmer2", "bodmer3")
    lake = pick("bodmer_view", "bodmer_view2")
    t44 = pick("team44b", "team44"); t44b = pick("team44") if t44 == "team44b" else None; t46 = pick("team46")
    lake2 = pick("bodmer_view2")
    wy = pick("weiyi", "weiyi26"); mc = pick("carlsen")
    BERLIN = "r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    LONDON = "rnbqkbnr/pppppppp/8/8/3P1B2/8/PPP1PPPP/RN1QKBNR b KQkq - 1 2"

    # ---- HOOK 0–22.8
    add(0.0, 7.0, split_bg(sind, guk), [
        El(lambda d, t: (draw_text(d, (W / 4, 470), "20", 260, weight="Black", anchor="mm", alpha=fade(t, 0.9, 2.4, 0.15)),
                         draw_text(d, (3 * W / 4, 470), "20", 260, weight="Black", anchor="mm", alpha=fade(t, 1.3, 2.4, 0.15))), 0.8, 2.4),
        El(lambda d, t: draw_text(d, (W / 2, 120), "yosh", 64, fill=GOLD, weight="ExtraBold", anchor="mm", alpha=fade(t, 1.4, 2.4, 0.15)), 1.4, 2.4),
        titles_split(wt(1, 2), 7.0, "DA’VOGAR", "JAHON CHEMPIONI", "Toshkentda tug‘ilgan", None),
    ], trans="cut", ticker=False)
    add(7.0, 12.0, G(), [big("ENG YOSH", 7.2, 12.0, y=420, size=170, color=GOLD, sub="jahon chempionligi uchun o‘yin — shaxmat tarixida hech qachon bunday yosh raqiblar to‘qnashmagan")], trans="cut", ticker=False)
    add(12.0, 16.0, P(lake, 1.0, 1.15, (0.5, 0.55), (0.5, 0.45)), [headline("JENEVA", 12.2, 16.0, y=140, size=96, tag="SHVEYSARIYA")], ticker=False)
    add(16.0, 20.5, P(sind, 1.05, 1.2, (0.5, 0.4), (0.5, 0.35)), [lower_third("Javohir Sindarov", "Jahon chempioni tojiga hech qachon bunchalik yaqin bo‘lmagan", 16.3, 20.5)], ticker=False)
    add(20.5, 22.8, G(), [scoreboard(20.6, 22.8, sub="2 partiyadan keyin · hisob teng")], trans="cut", ticker=False)
    add(22.8, 30.0, G(), [checklist([("Ikki partiyada aslida nima bo‘ldi?", "?", 23.0), ("Nega mutaxassislar Sindarovni favorit deb hisoblamoqda?", "?", 25.5)], 22.9, 30.0, x=200, y=380)])
    # ---- FACTS 30–66.7
    add(30.0, 31.6, G(), [bumper("ASOSIY FAKTLAR", 30.05, 31.6)], trans="cut")
    add(31.6, 38.6, G(), [geo_map(31.6, 38.6, 6.8, 46.3, 120, dots=[(6.18, 46.22, "Kolonyi · Jeneva", 34.0)], title=None),
                          card(110, 140, 780, "24-NOYABR 2026", "Jahon chempionati o‘yini boshlandi", 31.7, 38.6, accent=RED, title_size=64, body_size=36)])
    add(38.6, 41.4, P(bod, 1.0, 1.12), [card(110 if bod else W / 2 - 600, 720 if bod else 380, 900 if bod else 1200, "Martin Bodmer jamg‘armasi", "o‘yin mezboni · Kolonyi", 38.7, 41.4, accent=GOLD, title_size=40 if bod else 64, body_size=30 if bod else 40)])
    add(41.4, 45.1, P(guk, 1.0, 1.12, (0.5, 0.4), (0.5, 0.38)), [lower_third("Gukesh Dommaraju", "Jahon chempioni · Hindiston", 41.5, 45.1)])
    add(45.1, 48.4, P(sind2, 1.0, 1.12, (0.5, 0.4), (0.5, 0.38)), [lower_third("Javohir Sindarov", "Grossmeyster · O‘zbekiston", 45.2, 48.4)])
    add(48.4, 60.0, G(), [
        El(lambda d, t: [ (lambda i, k: (d.rounded_rectangle((260 + i * 100, 300, 340 + i * 100, 380), radius=10, fill=NAVY2 + (int(255 * k * fade(t, 48.5, 60)),), outline=(255, 255, 255, int(90 * k)), width=2),
                                         draw_text(d, (300 + i * 100, 340), str(i + 1), 34, anchor="mm", alpha=k * fade(t, 48.5, 60), shadow=False)))(i, prog(t, 49.6 + 0.08 * i, 0.3)) for i in range(14)], 48.5, 60.0),
        El(lambda d, t: draw_text(d, (W / 2, 200), "14 ta klassik partiya", 60, weight="ExtraBold", anchor="mm", alpha=fade(t, 48.5, 60)), 48.5, 60.0),
        big("7½ ochko", 52.0, 60.0, y=560, size=130, color=GOLD, sub="birinchi to‘plagan — jahon chempioni"),
        chip("7 : 7 bo‘lsa → tezkor shaxmatda qo‘shimcha partiyalar", W / 2, 830, 55.9, 60.0, color=RED, size=38, anchor="c"),
    ])
    add(60.0, 66.7, G(), [counter(W / 2, 400, 2500000, "mukofot jamg‘armasi", 60.1, 66.7, prefix="$", size=170, color=GOLD),
                          chip("+ $200 000 — har bir g‘alaba uchun", W / 2, 720, 63.5, 66.7, color=GREEN, size=44, anchor="c")])
    # ---- GAME 1 66.7–93.2
    add(66.7, 68.5, G(), [bumper("1-PARTIYA", 66.75, 68.5, sub="Seshanba, 24-noyabr")], trans="cut")
    add(68.5, 82.7, G(), [chessboard(BERLIN, 68.6, 82.7, highlight=("b5", "f6"), title="Berlin himoyasi",
                                     sub="Oq — Sindarov · Qora — Gukesh. 1.e4 e5 2.Nf3 Nc6 3.Bb5 Nf6"),
                          chip("Bosim — Sindarovda", 1010, 520, 76.2, 82.7, color=UZ, size=40),
                          chip("Gukesh — vaqt tanqisligida", 1010, 620, 79.0, 82.7, color=RED, size=40)])
    add(82.7, 93.2, P(pick("guk_tata24") or guk2, 1.0, 1.12, (0.5, 0.4), (0.5, 0.36), dark=0.3), [
        big("½ — ½", 88.2, 93.2, y=420, size=170, color=GOLD, sub="38-yurishda durang")])
    # ---- GAME 2 93.2–110.8
    add(93.2, 104.2, G(), [chessboard(LONDON, 93.3, 104.2, highlight=("d4", "f4"), title="London tizimi",
                                      sub="2-partiya, chorshanba. Oq — Gukesh. Sxema: 1.d4 va 2.Bf4"),
                           chip("20 yurish · durang", 1010, 560, 101.0, 104.2, color=GREY, size=44)])
    add(104.2, 108.0, P(guk3, 1.0, 1.1, (0.5, 0.4), (0.5, 0.36)), [lower_third("Gukesh Dommaraju", "2-partiyadan keyin", 104.3, 108.0)])
    add(108.0, 110.8, G(), [scoreboard(108.1, 110.8, sub="ikki partiyadan keyin")], trans="cut")
    add(110.8, 115.6, G(), [big("3-PARTIYA", 111.0, 115.6, y=400, size=150, sub="bugun · 26-noyabr · oq donalar yana Sindarovda")])
    # ---- PATH 115.6–176.4
    add(115.6, 124.7, P(sind_young, 1.0, 1.12, (0.5, 0.4), (0.5, 0.36)), [
        card(110, 220, 760, "8-dekabr 2005", "Toshkentda tug‘ilgan", 118.0, 124.7, accent=UZ, title_size=60, body_size=40),
        chip("Shaxmatni bobosi Komil Sindarov o‘rgatgan", 110, 520, 121.8, 124.7, color=GOLD, size=36)])
    add(124.7, 132.3, G(), [big("12 yosh 10 oy", 124.9, 132.3, y=400, size=150, color=GOLD, sub="grossmeyster unvoni — o‘sha paytda tarixdagi ikkinchi eng yosh natija")])
    add(132.3, 136.9, P(t44b, 1.0, 1.1, dark=0.6), [big("2 × OLIMPIADA G‘OLIBI", 132.5, 136.9, y=460, size=110, color=GOLD, sub="O‘zbekiston terma jamoasi tarkibida")])
    add(136.9, 139.4, P(t44, 1.0, 1.1), [card(110, 720, 760, "2022 · Chennay", "44-Shaxmat olimpiadasi — oltin", 137.0, 139.4, accent=GOLD)])
    add(139.4, 141.8, P(t46, 1.0, 1.1), [card(110, 720, 760, "2026 · Samarqand", "46-Shaxmat olimpiadasi — oltin", 139.5, 141.8, accent=GOLD)])
    add(141.8, 151.1, G(), [geo_map(141.8, 151.1, 76, 18, 52, dots=[(73.83, 15.49, "Goa · Jahon kubogi 2025", 144.4)]),
                            chip("Sindarov ro‘yxatda atigi 16-o‘rinda edi", 110, 820, 148.1, 151.1, color=RED, size=40)])
    add(151.1, 157.8, P(wy, 1.0, 1.1, (0.5, 0.4), (0.5, 0.36)), ([lower_third("Vey I (Xitoy)", "Jahon kubogi 2025 finalida Sindarovga yutqazdi", 151.2, 154.5)] if wy else
                                                                 [card(W / 2 - 600, 260, 1200, "Final: Sindarov — Vey I (Xitoy)", "Jahon kubogi 2025 · g‘olib tay-brekda aniqlandi", 151.2, 157.8, accent=RED, title_size=56, body_size=38)]) +
                                                                [card(110 if wy else W / 2 - 600, 220 if wy else 560, 820 if wy else 1200, "Eng yosh g‘olib", "va Jahon kubogining ilk o‘zbekistonlik g‘olibi", 154.5, 157.8, accent=GOLD)])
    add(157.8, 166.6, G(), [geo_map(157.8, 166.6, 30, 37, 60, dots=[(32.39, 34.88, "Kipr · Da’vogarlar turniri", 160.8)]),
                            chip("2026-yil bahori", 110, 820, 160.9, 166.6, color=BLUE, size=40)])
    add(166.6, 176.4, G(), [stat_ring(560, 470, 71.4, "10 / 14 ochko", 166.0, 176.4, color=GOLD, r=170, size=1),
        El(lambda d, t: draw_text(d, (560, 465), "10/14", 92, fill=WHITE, weight="Black", anchor="mm", alpha=fade(t, 166.7, 176.4)), 166.6, 176.4),
        El(lambda d, t: [ (lambda i, lab, col, tin: (d.rectangle((1000, 300 + i * 130, 1000 + 70 * n * prog(t, tin, 0.6), 390 + i * 130), fill=col + (int(240 * fade(t, 166.7, 176.4)),)),
                                                    draw_text(d, (990, 345 + i * 130), lab, 40, weight="ExtraBold", anchor="rm", alpha=fade(t, 166.7, 176.4))))(i, lab, col, tin)
                         for i, (lab, n, col, tin) in enumerate([("6 g‘alaba", 6, GREEN, 166.6), ("8 durang", 8, GREY, 167.5), ("0 mag‘lubiyat", 0, RED, 168.5)])], 166.6, 176.4),
        chip("Format tarixidagi eng yuqori natija", 1000, 720, 170.0, 176.4, color=GOLD, size=36),
        chip("G‘alaba — bir tur qolganida", 1000, 810, 173.4, 176.4, color=BLUE, size=36)])
    # ---- WHY 176.4–246.6
    add(176.4, 179.0, G(), [bumper("NEGA MUHIM?", 176.45, 179.0)], trans="cut")
    add(179.0, 196.7, G(), [El(lambda d, t: draw_text(d, (W / 2, 100), "1 · KUCHLAR NISBATI", 40, fill=GOLD, weight="ExtraBold", anchor="mm", alpha=fade(t, 179.1, 196.7)), 179.0, 196.7),
                            rating_bars(180.9, 196.7),
                            chip("Chempion reytingda da’vogardan ancha pastda — kam uchraydigan holat", W / 2, 930, 189.7, 196.7, color=RED, size=34, anchor="c")])
    add(196.7, 209.0, G(), [El(lambda d, t: draw_text(d, (W / 2, 100), "2 · O‘ZARO UCHRASHUVLAR", 40, fill=GOLD, weight="ExtraBold", anchor="mm", alpha=fade(t, 196.8, 209)), 196.7, 209.0),
                            h2h(198.7, 209.0, [201.6, 202.4, 203.7, 205.2])])
    add(209.0, 217.0, P(mc, 1.0, 1.12, (0.5, 0.4), (0.5, 0.36)), [
        El(lambda d, t: draw_text(d, (W / 2, 100), "3 · MUTAXASSISLAR FIKRI", 40, fill=GOLD, weight="ExtraBold", anchor="mm", alpha=fade(t, 209.1, 217)), 209.0, 217.0),
        lower_third("Magnus Karlsen", "Sobiq jahon chempioni", 211.0, 217.0),
        card(1000, 300, 820, "“Ancha aniq favorit”", "Sindarov haqida · Chess.com", 213.0, 217.0, accent=GOLD, title_size=50)])
    add(217.0, 222.7, P(sind3, 1.0, 1.1, (0.5, 0.4), (0.5, 0.36), dark=0.5), [big("50 / 50", 219.1, 222.7, y=440, size=170, color=GOLD, sub="Sindarov o‘z imkoniyatlari haqida (o‘yindan oldin)")])
    add(222.7, 239.4, P(guk2, 1.05, 1.15, (0.5, 0.4), (0.5, 0.35), dark=0.35), [
        headline("Gukeshni yengil raqib deb o‘ylamaslik kerak", 222.8, 226.0, y=150, size=54),
        card(110, 260, 900, "2024 · Singapur", "Ding Lirenni (Xitoy) yengdi", 226.0, 239.4, accent=IN, title_size=56, body_size=38),
        card(110, 520, 900, "18 yosh", "tarixdagi eng yosh mutlaq jahon chempioni", 230.9, 239.4, accent=GOLD, title_size=56, body_size=38)])
    add(239.4, 246.6, P(guk, 1.12, 1.0, (0.5, 0.36), (0.5, 0.4), dark=0.45), [
        quote("Men biror narsani himoya qilish uchun kelmadim. Men hammasini yana qaytadan yutish uchun keldim", "Gukesh Dommaraju · o‘yin oldidan matbuot anjumani", 241.2, 246.6, y=300, size=54)])
    # ---- UZBEKISTAN 246.6–266.4
    add(246.6, 256.8, G(), [headline("O‘zbekiston uchun — shunchaki sport natijasi emas", 246.7, 256.8, y=160, size=54),
                            card(260, 360, 1400, "2004 · Rustam Qosimjonov", "FIDE jahon chempioni", 249.4, 256.8, accent=UZ, title_size=56, body_size=40),
                            chip("O‘sha paytda ikki xil chempionlik unvoni mavjud edi", W / 2, 680, 253.2, 256.8, color=RED, size=38, anchor="c")])
    add(256.8, 266.4, P(t46 or pick("naro1") or sind2, 1.0, 1.12, (0.4, 0.45), (0.35, 0.42), dark=0.55), [big("BIRINCHI MUTLAQ", 258.6, 266.4, y=380, size=120, color=GOLD, sub="O‘zbekistondan chiqqan jahon chempioni — agar Sindarov g‘alaba qozonsa")])
    # ---- NEXT 266.4–313.4
    add(266.4, 271.8, G(), [bumper("ENDI NIMA BO‘LADI?", 266.45, 269.6), big("12 partiya oldinda", 269.6, 271.8, y=480, size=100, color=GOLD)])
    add(271.8, 298.1, G(), [El(lambda d, t: draw_text(d, (W / 2, 130), "O‘YIN TAQVIMI · 24-NOYABR — 12-DEKABR 2026", 46, weight="ExtraBold", anchor="mm", alpha=fade(t, 271.9, 298.1)), 271.8, 298.1),
                            calendar(271.9, 298.1, focus=[("26N", 271.8), ("27N", 273.4), ("01D", 276.6), ("05D", 276.9), ("09D", 277.2), ("12D", 279.6), ("08D", 288.7)]),
                            chip("8-dekabr — Javohir 21 yoshga to‘ladi · 12-partiya", W / 2, 960, 288.8, 298.1, color=GOLD, size=36, anchor="c")])
    add(298.1, 308.1, G(), [big("Reyting ≠ kafolat", 299.7, 308.1, y=400, size=120, sub="Jahon chempionati o‘yinlari ko‘pincha bitta xato yoki bitta kutilmagan debyut bilan hal bo‘ladi")])
    add(308.1, 313.4, G(), [scoreboard(308.2, 313.4, sub="kurash endi boshlandi")])
    # ---- CONCLUSION 313.4–345.4
    add(313.4, 320.7, split_bg(sind2, guk3), [titles_split(316.0, 320.7, "Birinchi zarba", "Bosim ostida himoya")])
    add(320.7, 329.3, P(t46 or lake2 or sind, 1.0, 1.12, dark=0.35), [headline("Keyingi ikki hafta ichida…", 324.0, 329.3, y=860, size=54)])
    add(329.3, 333.5, P(guk3, 1.0, 1.1, (0.5, 0.4), (0.5, 0.36), dark=0.3), [headline("…yoki tajribali chempion yana hayratda qoldiradi", 329.4, 333.5, y=860, size=50)])
    add(333.5, AUDIO_END, G(), [headline("Sizningcha?", 333.6, AUDIO_END, y=150, size=80),
        card(300, 360, 620, "A · 14 partiyada", "Sindarov klassik partiyalarda g‘alaba qozonadi", 333.7, AUDIO_END, accent=UZ, title_size=50),
        card(1000, 360, 620, "B · Tezkor shaxmatda", "taqdir tay-brekda hal bo‘ladi", 337.8, AUDIO_END, accent=RED, title_size=50),
        chip("Fikringizni izohlarda yozing", W / 2, 760, 340.5, AUDIO_END, color=RED, size=44, anchor="c")])
    add(AUDIO_END, TOTAL, G(), [credits_roll(AUDIO_END, TOTAL)], credit="", ticker=False)
    S = sorted([s for s in S if s.t1 > s.t0], key=lambda s: s.t0)
    for a_, b_ in zip(S, S[1:]):
        assert abs(a_.t1 - b_.t0) < 1e-6, (a_.t0, a_.t1, b_.t0)
    return S


# ======================= v3: 9:16 SHORT — Sindarov–Gukesh game 3 =======================
AUDIO_END = 32.40
TOTAL = 33.2
CREDITS = dict(CREDITS)
CREDITS.update({
    "sind_olymp45": "ARXIV: 45-OLIMPIADA, 2024 · MiroJP / Wikimedia · CC BY-SA 4.0",
    "sind_ha": "ARXIV · Husniddin Ato / Wikimedia · CC BY-SA 4.0",
    "sind_tb": "ARXIV · TheBoburshokh / Wikimedia · CC BY 4.0",
    "guk24": "ARXIV, 2024 · Frans Peeters / Wikimedia · CC BY-SA 2.0",
    "guk_tata24": "ARXIV: TATA STEEL, 2024 · Frans Peeters / Wikimedia · CC BY-SA 2.0",
    "guk25": "ARXIV, 2025 · Frans Peeters / Wikimedia · CC BY-SA 2.0",
    "carlsen": "ARXIV, 2025 · Miroslav Vajdic / Wikimedia · CC BY 4.0",
    "bodmer_view": "KOLONYI, JENEVA, 2014 · Jacklee / Wikimedia · CC BY-SA 3.0",
    "bodmer2": "KOLONYI, BODMER JAMG‘ARMASI · Jacklee / Wikimedia · CC BY-SA 3.0",
})

def stack_bg(kt, kb, dark=0.15):
    """Two photos stacked (top/bottom) for 9:16."""
    def bg(t, sh):
        im = Image.new("RGB", (W, H), NAVY)
        for i, k in enumerate((kt, kb)):
            if k and have(k):
                src = load_photo(k)
                kk = ease_io((t - sh.t0) / max(0.01, sh.t1 - sh.t0)); z = lerp(1.0, 1.08, kk)
                tw, th = W, H // 2
                cw = min(src.width, src.height * tw / th) / z; ch = cw * th / tw
                x = (src.width - cw) / 2; y = clamp(src.height * 0.38 - ch / 2, 0, src.height - ch)
                im.paste(src.transform((tw, th), Image.EXTENT, (x, y, x + cw, y + ch), Image.BILINEAR), (0, i * th))
        im = darken(im, dark)
        ImageDraw.Draw(im).rectangle((0, H / 2 - 5, W, H / 2 + 5), fill=GOLD)
        return im
    bg.key = None; bg.keys = [k for k in (kt, kb) if k and have(k)]
    return bg

def tag(text, y, t0, t1, color=RED, size=44, x=None):
    def fn(d, t):
        a = fade(t, t0, t1, 0.2); k = prog(t, t0, 0.3)
        f = F(size, "Black"); tw = f.getlength(text) + 50; h = size * 1.6
        x0 = (W - tw) / 2 if x is None else x
        d.rectangle((x0, y, x0 + tw * k, y + h), fill=color + (int(245 * a),))
        if k > 0.5: d.text((x0 + 25, y + h / 2), text, font=f, fill=(255, 255, 255, int(255 * a)), anchor="lm")
    return El(fn, t0, t1)

def bigv(text, y, t0, t1, size=200, color=WHITE, pop=True, band=False):
    def fn(d, t):
        a = fade(t, t0, t1, 0.2); k = prog(t, t0, 0.3)
        if band: d.rectangle((0, y - size * 0.62, W, y + size * 0.62), fill=NAVY + (int(235 * a),))
        s = int(size * (lerp(1.35, 1.0, k) if pop else 1))
        draw_text(d, (W / 2, y), text, s, fill=color, weight="Black", anchor="mm", alpha=a)
    return El(fn, t0, t1)

def name_card(name, title, y, t0, t1, accent=RED):
    def fn(d, t):
        a = fade(t, t0, t1, 0.25); k = prog(t, t0, 0.4)
        w = max(F(58, "ExtraBold").getlength(name), F(34, "SemiBold").getlength(title)) + 70
        x0 = (W - w) / 2
        d.rectangle((x0, y, x0 + w * k, y + 84), fill=(255, 255, 255, int(240 * a)))
        d.rectangle((x0, y + 84, x0 + w * k, y + 140), fill=NAVY + (int(235 * a),))
        d.rectangle((x0 - 12, y, x0, y + 140), fill=accent + (int(255 * a),))
        if k > 0.6:
            d.text((W / 2, y + 42), name, font=F(58, "ExtraBold"), fill=NAVY + (int(255 * a),), anchor="mm")
            d.text((W / 2, y + 112), title, font=F(34, "SemiBold"), fill=OFF + (int(255 * a),), anchor="mm")
    return El(fn, t0, t1)

def score_v(y, t0, t1, s="1½ — 1½"):
    def fn(d, t):
        a = fade(t, t0, t1, 0.2); k = prog(t, t0, 0.35)
        panel(d, (60, y, W - 60, y + 420), a * 0.96)
        flag(d, "UZ", 120, y + 50, 150, 100, a); flag(d, "IN", W - 270, y + 50, 150, 100, a)
        draw_text(d, (195, y + 200), "SINDAROV", 40, weight="ExtraBold", anchor="mm", alpha=a, shadow=False)
        draw_text(d, (W - 195, y + 200), "GUKESH", 40, weight="ExtraBold", anchor="mm", alpha=a, shadow=False)
        draw_text(d, (W / 2, y + 120), s, int(lerp(130, 96, k)), fill=GOLD, weight="Black", anchor="mm", alpha=a, shadow=False)
        draw_text(d, (W / 2, y + 330), "3 partiyadan keyin", 42, fill=OFF, weight="SemiBold", anchor="mm", alpha=a, shadow=False)
    return El(fn, t0, t1)

def games_grid(y, t0, t1, played=3):
    def fn(d, t):
        a = fade(t, t0, t1, 0.2); cw = 128; x0 = (W - 7 * cw) / 2
        for i in range(14):
            k = prog(t, t0 + 0.05 * i, 0.25); r, c = divmod(i, 7)
            x, yy = x0 + c * cw, y + r * 150
            done = i < played
            d.rounded_rectangle((x + 8, yy, x + cw - 8, yy + 128), radius=14, fill=(GREY if done else NAVY2) + (int(240 * a * k),),
                                outline=(GOLD + (int(255 * a),)) if not done else None, width=4)
            draw_text(d, (x + cw / 2, yy + 64), "½" if done else str(i + 1), 52, weight="Black", anchor="mm", alpha=a * k, shadow=False,
                      fill=WHITE if done else GOLD)
    return El(fn, t0, t1)

# --- word-by-word captions from corrected text distributed over segment time
CAP = []
def build_captions():
    lines = [l.strip() for l in open(os.path.join(SCR, "corrected.txt")) if l.strip()]
    for s, txt in zip(TR, lines):
        words = txt.split(); a, b = s["start"], s["end"]
        tot = sum(len(w) + 1 for w in words); acc = 0
        chunk = []; c0 = a
        for i, w_ in enumerate(words):
            acc += len(w_) + 1; chunk.append(w_)
            tt = a + (b - a) * acc / tot
            if len(chunk) == 3 or i == len(words) - 1 or w_.endswith((",", ".", "?", ":")):
                CAP.append((c0, tt, " ".join(chunk))); chunk = []; c0 = tt

def captions_el():
    if not CAP: build_captions()
    def fn(d, t):
        for a_, b_, txt in CAP:
            if a_ <= t < b_ + 0.08:
                k = prog(t, a_, 0.12)
                f = F(78, "Black"); lines = wrap(txt.upper(), f, 960)
                y = 1330 - (len(lines) - 1) * 46
                for ln in lines:
                    s = int(78 * lerp(1.12, 1.0, k))
                    d.text((W / 2, y), ln, font=F(s, "Black"), fill=(255, 255, 255, 255), anchor="mm", stroke_width=9, stroke_fill=(0, 0, 0, 255))
                    y += 92
                break
    return El(fn, 0, AUDIO_END)

def build():
    S = []
    def add(t0, t1, bg, els=(), credit=None, trans="cut"):
        c = credit if credit is not None else cred(bg)
        if c is None and getattr(bg, "keys", None):
            c = "  |  ".join(CREDITS[k] for k in bg.keys)
        S.append(Shot(t0, t1, bg, c, list(els) + [captions_el()], trans, False))
    sind = pick("sind_olymp45", "sind_tb"); guk = pick("guk24", "guk25", "guk_tata24")
    sind_b = pick("sind_ha", "sind_tb"); sind_c = pick("sind_tb", "sind_olymp45")
    lake = pick("bodmer_view", "bodmer2"); mc = pick("carlsen"); guk_b = pick("guk_tata24", "guk25", "guk24")
    add(0.0, 3.6, stack_bg(sind, guk, 0.2), [tag("JAHON CHEMPIONATI · 3-PARTIYA", 120, 0.0, 3.6, color=RED, size=40),
                                              bigv("YANA DURANG", H / 2, 1.9, 3.6, size=130, color=GOLD, band=True)])
    add(3.6, 5.6, P(lake, 1.0, 1.12, (0.5, 0.5), (0.55, 0.45)), [tag("JENEVA", 260, 3.7, 5.6, color=BLUE, size=64)], trans="fade")
    add(5.6, 8.8, P(sind_b, 1.05, 1.18, (0.4, 0.4), (0.38, 0.36)), [name_card("Javohir Sindarov", "oq donalar bilan", 300, 5.7, 8.8, accent=UZ)])
    add(8.8, 12.0, G(), [bigv("60", 620, 8.9, 12.0, size=330, color=GOLD), bigv("YURISH", 830, 9.1, 12.0, size=90),
                         bigv("½ — ½", 1050, 10.9, 12.0, size=130, color=WHITE)])
    add(12.0, 14.2, G(), [score_v(520, 12.05, 14.2)])
    add(14.2, 18.4, P(sind_c, 1.0, 1.12, (0.45, 0.4), (0.42, 0.36), dark=0.25), [bigv("2782", 420, 14.6, 18.4, size=210, color=GOLD),
                                                                                tag("DUNYODA 4-O‘RIN", 560, 16.0, 18.4, color=UZ, size=52)])
    add(18.4, 20.6, P(mc, 1.0, 1.1, (0.5, 0.4), (0.5, 0.36), dark=0.2), [name_card("Magnus Karlsen", "Sindarov — favorit", 300, 18.5, 20.6, accent=GOLD)])
    add(20.6, 23.2, P(guk_b, 1.0, 1.12, (0.6, 0.4), (0.62, 0.36), dark=0.2), [name_card("Gukesh Dommaraju", "jahon chempioni · Hindiston", 300, 20.7, 23.2, accent=IN)])
    add(23.2, 25.1, G(), [bigv("11 PARTIYA", 420, 23.3, 25.1, size=120, color=GOLD), bigv("oldinda", 540, 23.4, 25.1, size=60, pop=False),
                          games_grid(640, 23.3, 25.1)])
    add(25.1, 27.8, G(), [bigv("7½", 640, 25.2, 27.8, size=380, color=GOLD), bigv("OCHKO = TOJ", 900, 25.6, 27.8, size=90)])
    add(27.8, TOTAL, stack_bg(sind_c, guk, 0.35), [bigv("KIM?", H / 2, 27.9, TOTAL, size=200, color=GOLD, band=True),
                                                    tag("IZOHLARDA YOZING", 240, 30.6, TOTAL, color=RED, size=56)], trans="fade")
    S = sorted(S, key=lambda s: s.t0)
    for a_, b_ in zip(S, S[1:]): assert abs(a_.t1 - b_.t0) < 1e-6
    return S

def used_photo_credits():
    keys = []
    for sh in SHOTS_FOR_CREDITS:
        for k in ([getattr(sh.bg, "key", None)] + list(getattr(sh.bg, "keys", []) or [])):
            if k and k not in keys: keys.append(k)
    out = []
    for k in keys:
        c = CREDITS[k].split("FOTO: ")[-1].replace(" / Wikimedia Commons", "")
        if c not in out: out.append(c)
    return out

SHOTS_FOR_CREDITS = []
def credits_roll(t0, t1):
    def fn(d, t):
        photos = used_photo_credits()
        lines = ["VIDEO MANBALARI / FOOTAGE SOURCES", "", "Fotosuratlar (Wikimedia Commons, arxiv — boshqa tadbirlardan):"]
        row = ""
        for p in photos:
            if len(row) + len(p) > 95: lines.append(row); row = ""
            row = (row + "  ·  " + p) if row else p
        if row: lines.append(row)
        lines += ["", "Faktlar: FIDE · Wikipedia · Chess.com · Qazinform · UzA (24–26.11.2026)",
                  "Xarita: Natural Earth / world.geo.json  ·  Shaxmat diagrammalari, musiqa va SFX: original",
                  "", "Barcha havolalar va litsenziyalar — video tavsifida"]
        a = fade(t, t0, t1, 0.6); y = 230
        for i, ln in enumerate(lines):
            draw_text(d, (W / 2, y + i * 54), ln, 46 if i == 0 else 30, fill=GOLD if i == 0 else OFF,
                      weight="ExtraBold" if i == 0 else "Medium", anchor="mm", alpha=a)
    return El(fn, t0, t1)

TICKER = "JAHON SHAXMAT CHEMPIONATI · KOLONYI, JENEVA  ·  SINDAROV — GUKESH: 1 — 1  ·  14 PARTIYA, 7½ OCHKOGACHA  ·  O‘YIN 12-DEKABRGACHA DAVOM ETADI  ·  "
def draw_chrome(d, t, sh):
    # ticker
    if sh.ticker:
        a = fade(t, 14.0, None, 0.5) if t < 15 else 1.0
        y0 = H - 58
        d.rectangle((0, y0, W, H), fill=(255, 255, 255, int(235 * a)))
        d.rectangle((0, y0, 230, H), fill=RED + (int(255 * a),))
        d.text((115, y0 + 29), "SHAXMAT", font=F(30, "Black"), fill=(255, 255, 255, int(255 * a)), anchor="mm")
        f = F(28, "Bold"); tw = f.getlength(TICKER); x = 250 - (t * 110) % tw
        while x < W:
            d.text((x, y0 + 29), TICKER, font=f, fill=NAVY + (int(255 * a),), anchor="lm"); x += tw
        d.rectangle((0, y0, 230, H), fill=RED + (int(255 * a),))
        d.text((115, y0 + 29), "SHAXMAT", font=F(30, "Black"), fill=(255, 255, 255, int(255 * a)), anchor="mm")
    # source label
    if sh.credit:
        f = F(20, "SemiBold"); tw = f.getlength(sh.credit)
        a = fade(t, sh.t0 + 0.2, sh.t1 - 0.05, 0.3)
        if W < H:
            parts = sh.credit.split("  |  ") if "  |  " in sh.credit else [sh.credit]
            for j, ptxt in enumerate(parts):
                yy = 40 if (len(parts) == 1 or j == 0) else H / 2 + 140
                ft = F(22, "SemiBold"); tw2 = ft.getlength(ptxt)
                d.rectangle((24, yy, 24 + tw2 + 28, yy + 36), fill=(0, 0, 0, int(160 * a)))
                d.text((38, yy + 18), ptxt, font=ft, fill=(255, 255, 255, int(240 * a)), anchor="lm")
        else:
            y = H - (58 + 46) if sh.ticker else H - 50
            d.rectangle((W - tw - 52, y, W - 20, y + 34), fill=(0, 0, 0, int(150 * a)))
            d.text((W - 36, y + 17), sh.credit, font=f, fill=(255, 255, 255, int(235 * a)), anchor="rm")

SHOTS = None
def frame(t):
    global SHOTS
    if SHOTS is None:
        SHOTS = build(); SHOTS_FOR_CREDITS.extend(SHOTS)
    idx = 0
    for i, s in enumerate(SHOTS):
        if s.t0 <= t < s.t1: idx = i; break
    else:
        idx = len(SHOTS) - 1
    sh = SHOTS[idx]
    base = sh.bg(t, sh).convert("RGB")
    # transition: crossfade from previous shot over 0.4s
    TD = 0.4
    if idx > 0 and sh.trans == "fade" and t - sh.t0 < TD:
        prev = SHOTS[idx - 1]
        pb = prev.bg(t, prev).convert("RGB")
        lay_p = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dp = ImageDraw.Draw(lay_p)
        for e in prev.els:
            if e.t0 <= t <= e.t1 + 0.5: e.fn(dp, min(t, e.t1 - 0.001))
        pb = Image.alpha_composite(pb.convert("RGBA"), lay_p).convert("RGB")
        base = Image.blend(pb, base, ease_io((t - sh.t0) / TD))
    arr = np.asarray(base).astype(np.float32) * vignette()
    if getattr(sh.bg, "key", None) and sh.bg.__qualname__.startswith("P."): arr *= botgrad()
    base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for e in sh.els:
        if e.t0 <= t <= e.t1:
            e.fn(d, t)
    draw_chrome(d, t, sh)
    return Image.alpha_composite(base, lay).convert("RGB")

def main():
    out = sys.argv[1]
    nf = int(round(TOTAL * FPS))
    a = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    b = int(sys.argv[3]) if len(sys.argv) > 3 else nf
    if out.endswith(".png"):
        frame(a / FPS).save(out); return
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-x264-params", "keyint=50", out], stdin=subprocess.PIPE)
    for i in range(a, b):
        p.stdin.write(frame(i / FPS).tobytes())
        if i % 250 == 0: print(out, i, b, flush=True)
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    main()
