"""News-documentary renderer: draws every frame with PIL and pipes raw RGB to ffmpeg.
Usage: python3 render.py OUT.mp4 [start_frame end_frame]
"""
import sys, os, json, math, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

BASE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.dirname(BASE)
IMG = os.path.join(SCR, "img")
W, H, FPS = 1920, 1080, 25
AUDIO_END = 328.17
TOTAL = AUDIO_END + 8.0  # + end credits

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
CREDITS = {
    "om_cc0": "FOTO: Yodgor Sharipov / Wikimedia Commons · CC0",
    "om_dm1": "FOTO: Davide Mauro / Wikimedia Commons · CC BY-SA 4.0",
    "om_dm2": "FOTO: Davide Mauro / Wikimedia Commons · CC BY-SA 4.0",
    "om_dm3": "FOTO: Davide Mauro / Wikimedia Commons · CC BY-SA 4.0",
    "om_bob": "FOTO: Bobyrr / Wikimedia Commons · CC BY-SA 4.0",
    "lc_round": "ARXIV, 22.10.2026 · FOTO: OSCE Parliamentary Assembly / Wikimedia Commons · CC BY-SA 4.0",
    "senate": "FOTO: Enric / Wikimedia Commons · CC BY 4.0",
    "fergana_line": "FARG‘ONA, ARXIV · FOTO: Adam Jones / Wikimedia Commons · CC BY-SA 2.0",
    "school235": "TOSHKENT, 235-MAKTAB, 2023 · FOTO: Umarxon III / Wikimedia Commons · CC BY 4.0",
    "school10": "TOSHKENT, 10-MAKTAB · FOTO: Janob Mirzaolim / Wikimedia Commons · CC BY-SA 4.0",
    "school103": "TOSHKENT, 103-MAKTAB · FOTO: Bettyrose.pl / Wikimedia Commons · CC BY-SA 4.0",
    "samar_girls1": "SAMARQAND, 2011 · FOTO: Arian Zwegers / Wikimedia Commons · CC BY 2.0",
    "samar_girls2": "SAMARQAND, 2011 · FOTO: Arian Zwegers / Wikimedia Commons · CC BY 2.0",
    "kg37": "37-SON BOLALAR BOG‘CHASI · FOTO: Hasan Tohirov / Wikimedia Commons · CC BY-SA 4.0",
    "kg37b": "37-SON BOLALAR BOG‘CHASI · FOTO: Hasan Tohirov / Wikimedia Commons · CC BY-SA 4.0",
    "village_kids": "O‘ZBEKISTON QISHLOG‘I · FOTO: Sinchalak Musulmon / Wikimedia Commons · CC BY-SA 4.0",
    "village_spring": "O‘ZBEKISTON QISHLOG‘I · FOTO: Sinchalak Musulmon / Wikimedia Commons · CC BY-SA 4.0",
    "family": "FOTO: Sinchalak Musulmon / Wikimedia Commons · CC BY-SA 4.0",
    "khiva_students": "XIVA, PREZIDENT MAKTABI · FOTO: Kamol Azzam / Wikimedia Commons · CC BY-SA 4.0",
    "khiva_school": "XIVA, PREZIDENT MAKTABI · FOTO: Kamol Azzam / Wikimedia Commons · CC BY-SA 4.0",
    "dis_hall": "TOSHKENT, XUSUSIY MAKTAB (DIS) · FOTO: AAkhmedova (WMF) / Wikimedia Commons · CC BY 4.0",
    "dehibolo": "DEHIBOLO MAKTABI, 2021 · FOTO: PJakopin / Wikimedia Commons · CC BY 4.0",
    "library": "RESPUBLIKA BOLALAR KUTUBXONASI · FOTO: MinaUktamova / Wikimedia Commons · CC BY 4.0",
    "gulistan": "GULISTON, PREZIDENT MAKTABI · FOTO: Zilolaa Bahromovna / Wikimedia Commons · CC BY-SA 4.0",
    "flag": "FOTO: Mrshaxas / Wikimedia Commons · CC0",
    "speakout": "TOSHKENT · FOTO: Chris Schuepp / Wikimedia Commons · CC BY 2.0",
    "uzbgym": "FOTO: Nataev / Wikimedia Commons · CC BY-SA 4.0",
}

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

def build():
    S = []
    def add(t0, t1, bg, els=(), credit=None, trans="fade", ticker=True):
        S.append(Shot(t0, t1, bg, credit if credit is not None else cred(bg), els, trans, ticker))

    kid1 = pick("family", "village_kids", "village_spring")
    sch1 = pick("school10", "khiva_school", "school103", "uzbgym", "gulistan", "school235")
    sch2 = pick("school235", "school103", "school10", "gulistan", "khiva_school")
    cls1 = pick("samar_girls1")
    kg = pick("kg37", "kg37b")
    fam = pick("family", "village_kids", "village_spring")
    priv = pick("dis_hall")
    hist = pick("fergana_line", "samar_girls1", "samar_girls2", "om_bob")
    grads = pick("khiva_students", "speakout", "samar_girls2")
    def hy(k, y_photo=860, y_none=470): return y_photo if k else y_none

    # --- HOOK 0-14
    add(0.0, 3.4, P("om_cc0", 1.25, 1.0, (0.5, 0.42), (0.5, 0.5), dark=0.35), [
        El(lambda d, t: (draw_text(d, (W / 2 - 260, H / 2 - 40), "11", 300, weight="Black", anchor="mm", alpha=fade(t, 0.9, None, 0.2)),
                         d.line((W / 2 - 400, H / 2 + 40, W / 2 - 120, H / 2 - 120), fill=RED + (int(255 * prog(t, wt(0, 5) - 0.1, 0.25)),), width=22)
                         if t > wt(0, 5) - 0.1 else None), 0.9, 3.4),
        El(lambda d, t: draw_text(d, (W / 2 + 260, H / 2 - 40), "12", int(lerp(520, 300, prog(t, wt(0, 5), 0.25))), fill=GOLD, weight="Black",
                                  anchor="mm", alpha=clamp((t - wt(0, 5)) / 0.12)), wt(0, 5), 3.4),
        El(lambda d, t: d.rectangle((0, H / 2 + 130, W, H / 2 + 250), fill=(9, 22, 44, int(200 * fade(t, 2.4)))), 2.4, 3.4),
        El(lambda d, t: draw_text(d, (W / 2, H / 2 + 190), "YILLIK MAKTAB TA’LIMI", 56, weight="ExtraBold", anchor="mm", alpha=fade(t, 2.4)), 2.4, 3.4),
    ], trans="cut", ticker=False)
    add(3.4, 6.5, P("om_dm3", 1.0, 1.15, (0.5, 0.45), (0.5, 0.4)), [
        headline("QONUNCHILIK PALATASI QONUNNI QABUL QILDI", 3.6, 6.5, y=140, size=60, tag="OLIY MAJLIS"),
    ], ticker=False)
    add(6.5, 12.0, G(sch1, 0.6, 4), [
        El(lambda d, t: draw_text(d, (W / 2, H / 2 - 40), "12-SINF?", int(lerp(160, 200, prog(t, 6.6, 5))), weight="Black", anchor="mm", alpha=fade(t, 6.7, 12.0)), 6.6, 12.0),
        El(lambda d, t: draw_text(d, (W / 2, H / 2 + 110), "“Farzandim endi 12-sinfgacha o‘qiydi”mi?", 46, fill=OFF, weight="SemiBold", anchor="mm", alpha=fade(t, 8.0, 12.0)), 8.0, 12.0),
    ], ticker=False)
    add(12.0, 14.1, G(), [
        El(lambda d, t: draw_text(d, (W / 2, H / 2), "ASLIDA — BOSHQACHA", 120, fill=GOLD, weight="Black", anchor="mm", alpha=fade(t, 12.05, 14.1, 0.15)), 12.0, 14.1),
    ], trans="cut", ticker=False)
    add(14.1, 17.6, G(), [
        headline("Qo‘shilayotgan yil — maktab OXIRIDA emas, BOSHIDA", 14.2, 17.6, y=200, size=54),
        years_blocks(14.2, 17.6, "intro"),
    ])
    add(17.6, 22.4, P(kid1, 1.0, 1.12, (0.5, 0.5), (0.55, 0.5)), [
        headline("Olti yoshli har bir bola — yuz minglab oila", 17.8, 22.4, y=hy(kid1), size=50 if kid1 else 64),
    ] + ([] if kid1 else [stamp("6", 17.7, 22.4, None, color=GOLD)]))
    # --- agenda
    add(22.4, 27.6, G(sch2, 0.72, 8), [
        checklist([("Aniq nima o‘zgaryapti?", "?", 22.9), ("Kimga qanday ta’sir qiladi?", "?", 24.0), ("Hali nimalar noma’lum?", "?", 25.6)], 22.5, 27.6, x=300, y=330),
    ], credit=None)
    add(27.6, 31.3, G(), [bumper("ASOSIY FAKTLAR", 29.9, 31.3), headline("Hammasini tartib bilan ko‘rib chiqamiz", 27.7, 29.9, y=500, size=58)])
    # --- facts 31-39
    add(31.3, 39.1, P("om_dm1", 1.0, 1.15, (0.45, 0.55), (0.55, 0.5), dark=0.35), [
        card(110, 220, 760, "24-NOYABR 2026", "Oliy Majlis Qonunchilik palatasi", 31.4, 39.1, accent=RED, title_size=64, body_size=36),
        chip("3-o‘qish — yakuniy", 110, 520, 35.4, 39.1, color=BLUE, size=40),
        chip("→ Senatga yuborildi", 110, 620, 38.1, 39.1, color=GREEN, size=40),
    ])
    add(39.1, 51.4, G("om_dm2"), [
        quote("Bir yillik maktabga tayyorlov — majburiy umumiy o‘rta ta’limning BIRINCHI BOSQICHI", "Qonun mazmuni bo‘yicha · manbalar: Kun.uz, Gazeta.uz, 25.11.2026", 39.2, 44.5),
        headline("Olti yoshli bolaning tayyorlov yili = maktab ta’limining rasmiy qismi", 44.6, 51.4, y=380, size=60, tag="SODDA QILIB AYTGANDA", tagcol=BLUE),
    ])
    add(51.4, 55.3, G(), [
        El(lambda d, t: draw_text(d, (W / 2, H / 2 - 30), f"{11 if t < wt(14, 7) else 12}", int(330 if t < wt(14, 7) else lerp(420, 330, prog(t, wt(14, 7), 0.25))),
                                  fill=WHITE if t < wt(14, 7) else GOLD, weight="Black", anchor="mm", alpha=fade(t, 51.5, 55.3)), 51.4, 55.3),
        El(lambda d, t: draw_text(d, (W / 2, H / 2 + 190), "YILLIK UMUMIY TA’LIM", 54, weight="ExtraBold", anchor="mm", alpha=fade(t, 51.8, 55.3)), 51.4, 55.3),
    ])
    # --- where 55-77
    add(55.3, 61.8, G(), [
        headline("Tayyorlov qayerda o‘tadi?", 55.4, 61.8, y=170, size=64),
        card(260, 400, 640, "Bog‘chada", "bog‘chaga boradigan bola", wt(16, 2), 61.8, accent=GREEN, title_size=60, body_size=36),
        card(1020, 400, 640, "Maktabda", "bog‘chaga bormaydigan bola", 60.0, 61.8, accent=BLUE, title_size=60, body_size=36),
    ])
    rural = pick("village_spring", "village_kids")
    add(61.8, 65.9, P(rural, 1.0, 1.1, (0.5, 0.5), (0.55, 0.45), dark=0.15), [
        card(110, 640, 1000, "Uzoq hududlarda", "ijtimoiy muassasalarda ham tashkil qilinishi mumkin", 61.9, 65.9, accent=GOLD, title_size=52),
        uz_map(62.0, 65.9, cx=1560, cy=300, scale=24, box=True),
    ])
    add(65.9, 70.6, P(priv, 1.0, 1.12), [card(110, 700 if priv else 400, 900 if priv else 1700, "Xususiy bog‘cha va maktablar", "o‘z dasturi asosida tayyorlov guruhlari ochishi mumkin", 66.1, 70.6, accent=GREEN)])
    add(70.6, 77.3, G(), [
        headline("O‘ZGARTIRISHLAR KIRITILMOQDA", 70.7, 77.3, y=170, size=60, tag="QONUNLAR"),
        card(200, 380, 720, "«Ta’lim to‘g‘risida»gi Qonun", None, 70.8, 77.3, accent=BLUE, title_size=46),
        card(1000, 380, 720, "«Maktabgacha ta’lim va tarbiya to‘g‘risida»gi Qonun", None, 72.6, 77.3, accent=GREEN, title_size=46),
    ])
    # --- background 77-98
    add(77.3, 90.8, G(), [
        headline("Islohot bir kunda paydo bo‘lmagan", 77.4, 79.3, y=200, size=58),
        flow(79.3, 90.8, [("Sentyabr 2025", "Prezident raisligida yig‘ilish", GOLD),
                          ("12 yillik tizimga o‘tish e’lon qilindi", None, BLUE),
                          ("17.11.2026", "1-o‘qish", GREY), ("24.11.2026", "3-o‘qish → Senat", RED)],
             y=400, marks=[79.4, 84.4, 87.2, 88.2]),
        lower_third("Sardor Rajabov", "Maktabgacha va maktab ta’limi vaziri o‘rinbosari (2025)", 84.4, 90.6),
    ])
    add(90.8, 97.0, G(), [structure_bar(90.8, 97.0, [wt(26, 0), wt(26, 3), wt(26, 6), wt(26, 10)])])
    add(97.0, 101.6, P(hist, 1.0, 1.12, dark=0.25), [headline("O‘zbekiston 12 yillik ta’limni ilgari ham sinab ko‘rgan", 98.6, 101.6, y=860, size=50, tag="TARIX", tagcol=GOLD)])
    add(101.6, 114.4, G(), [history(101.7, 114.4, wt(30, 1), 109.9), El(lambda d, t: draw_text(d, (W / 2, 1000 - 60), "…lekin butunlay boshqa shaklda", 40, fill=GOLD, weight="Bold", anchor="mm", alpha=fade(t, 112.5, 114.4)), 112.5, 114.4)])
    # --- readiness 114-164
    add(114.4, 116.8, G(), [bumper("DAVLAT TAYYORMI?", 114.45, 116.8, color=BLUE)], trans="cut")
    add(116.8, 121.7, P("lc_round", 1.0, 1.1, (0.4, 0.5), (0.55, 0.45), dark=0.4), [
        headline("Parlament muhokamasida aniq raqamlar keltirildi", 116.9, 121.7, y=130, size=52),
        lower_third("Sayyora Imomova", "Oliy Majlis Qonunchilik palatasi deputati", 119.5, 121.6),
    ], credit=CREDITS["lc_round"])
    add(121.7, 130.0, G(), [
        stat_ring(640, 500, 78, "bolalar maktabgacha ta’lim bilan qamrab olingan", 122.6, 130.0, color=BLUE),
        stat_ring(1280, 500, 98, "olti yoshli bolalar orasida qamrov", 128.5, 130.0, color=GREEN),
        El(lambda d, t: draw_text(d, (W / 2, 140), "Deputat Sayyora Imomova keltirgan raqamlar", 36, fill=GREY, weight="SemiBold", anchor="mm", alpha=fade(t, 121.8, 130)), 121.7, 130.0),
    ])
    add(130.0, 133.9, G(), [stamp("2018", 131.6, 133.9, "yildan beri bir yillik tayyorlov mavjud", color=GOLD)])
    add(133.9, 144.3, G(sch2, 0.75), [
        counter(560, 470, 4000, "dan ortiq maktabning bo‘sh xonalarida tayyorlov guruhlari", 134.9, 144.3, suffix="+", size=150),
        counter(1220, 400, 191, "ta maktabda", 139.3, 144.3, size=110, color=GOLD),
        counter(1600, 400, 246, "ta guruh — rejada", 141.1, 144.3, size=110, color=GOLD),
    ])
    add(144.3, 149.8, G(), [stat_ring(W / 2, 470, 100, "2027-yilda olti yoshli bolalarni 100% qamrab olish — maqsad", 144.6, 149.8, color=GOLD, r=190, size=110)])
    add(149.8, 154.9, G(), [
        counter(620, 470, 800, "ga yaqin yangi guruh", 150.6, 154.9, prefix="~", size=150),
        counter(1300, 470, 20000, "ga yaqin yangi o‘rin", 151.8, 154.9, prefix="~", size=150, color=GOLD),
    ])
    add(154.9, 158.8, G(), [card(W / 2 - 520, 380, 1040, "Xarajatlar", "2027-yilgi davlat budjetida hisobga olinishi aytildi", 155.0, 158.8, accent=GOLD, title_size=60, body_size=40)])
    add(158.8, 164.1, G(), [stamp("BEPUL", 161.4, 164.1, "davlat muassasalarida tayyorlov", color=GREEN),
        headline("Ota-onalar uchun eng muhimi", 158.9, 161.3, y=420, size=60)])
    # --- why 164-200
    add(164.1, 166.2, G(), [bumper("NEGA MUHIM?", 164.15, 166.2)], trans="cut")
    add(166.2, 172.5, G(), [world_map(166.2, 172.5), headline("Asosiy dalil — xalqaro standartlar", 166.4, 172.5, y=150, size=60),
        headline("Ko‘plab davlatlarda maktab ta’limi 12 yil davom etadi", 168.9, 172.5, y=820, size=48)])
    add(172.5, 184.2, G(), [flow(172.6, 184.2, [("11 yillik attestat", None, BLUE), ("Foundation", "1 yillik tayyorlov kursi", GOLD), ("Xorijiy universitet", None, GREEN)],
                                  y=380, marks=[172.6, 179.2, 174.4], title="Xorijda o‘qishni istaganlar uchun"),
        chip("+ vaqt", 700, 760, 182.9, 184.2, color=RED, size=44), chip("+ pul", 1000, 760, 183.4, 184.2, color=RED, size=44)])
    add(184.2, 191.1, G(), [flow(184.3, 191.1, [("12 yillik attestat", None, GOLD), ("Xorijiy universitet", "osonroq kirish", GREEN)], y=380,
                                  title="Islohot mualliflari fikricha"),
        El(lambda d, t: draw_text(d, (W / 2, 800), "to‘siq kamayadi", 48, fill=GOLD, weight="ExtraBold", anchor="mm", alpha=fade(t, 186.3, 191.1)), 186.3, 191.1)])
    add(191.1, 196.9, P(kg, 1.0, 1.12, dark=0.0 if kg else 0), [headline("Ikkinchi jihat — bolaning maktabga tayyorgarligi", 191.2, 196.9, y=hy(kg, 860, 200), size=48 if kg else 58)]
        + ([] if kg else [flow(194.1, 196.9, [("Bog‘cha", "tayyorlov yili", GOLD), ("Maktab", "1-sinf", BLUE)], y=430, marks=[194.2, 195.2])]))
    add(196.9, 200.9, P(cls1, 1.0, 1.1), [chip("Bog‘cha va maktab bog‘liqligi kuchaysa — moslashish osonroq", W / 2, hy(cls1, 880, 500), 197.0, 200.9, color=BLUE, size=40, anchor="c")]
        + ([] if cls1 else [headline("1-sinfga kirgan bola", 197.0, 200.9, y=360, size=64)]))
    # --- debate 200-235
    add(200.9, 205.9, P("lc_round", 1.12, 1.0, (0.55, 0.45), (0.5, 0.5), dark=0.45), [bumper("MUHOKAMA OSON KECHMADI", 201.1, 205.9, color=RED)], credit=CREDITS["lc_round"])
    add(205.9, 216.9, G(), [
        lower_third("Saydullo Azimov", "Deputat, O‘zLiDeP fraksiyasi", 205.95, 208.6),
        card(240, 220, 1440, "Olti yoshli bola kim hisoblanadi?", None, 208.6, 216.9, accent=RED, title_size=56),
        card(240, 420, 1440, "Maktab o‘quvchisimi yoki bog‘cha tarbiyalanuvchisi?", None, 210.6, 216.9, accent=GOLD, title_size=50),
        card(240, 610, 1440, "Tarbiyachilar maktab dasturiga o‘tishga tayyormi?", None, 213.7, 216.9, accent=BLUE, title_size=50),
    ])
    add(216.9, 224.7, G(), [
        lower_third("Erkin Murodov", "Vazirlik vakili", 216.95, 224.6),
        counter(W / 2, 430, 600000, "ga yaqin ota-ona uchun qiyinchilik — maktabgacha yosh chegarasi o‘zgarsa", 220.6, 224.7, prefix="~", size=170, color=GOLD),
    ])
    add(224.7, 235.2, G("lc_round", 0.8), [
        headline("Ta’lim tili masalasi", 224.8, 235.2, y=220, size=72, tag="1-O‘QISH"),
        card(320, 470, 1280, "Xavotir", "Ijtimoiy muassasalarda tayyorlov ona tilidagi ta’limga zarar yetkazishi mumkin", 228.0, 235.2, accent=RED, title_size=48, body_size=38),
    ], credit=CREDITS["lc_round"])
    # --- what next 235-277
    add(235.2, 241.9, G(), [flow(235.3, 241.9, [("Qonunchilik palatasi", "qabul qildi · 24.11", GREEN), ("Senat", "ma’qullashi kerak", GOLD), ("Prezident", "imzolashi kerak", BLUE)],
                                  y=420, marks=[236.9, 239.3, 240.4], title="Qonun hali kuchga kirmagan", done=[True, False, False])])
    add(241.9, 250.6, P("senate", 1.0, 1.15, (0.5, 0.5), (0.5, 0.4)), [
        card(110, 700, 1000, "Senat", "Qonun aynan qaysi majlisda ko‘rilishi haqida rasmiy ma’lumot hozircha yo‘q", 245.4, 250.6, accent=GOLD),
    ])
    add(250.6, 264.1, G(), [checklist([("Qonun qachondan kuchga kiradi?", "?", 252.4), ("Qaysi yilgi bolalar birinchi bo‘lib o‘qiydi?", "?", 255.2),
                                        ("Tayyorgarlik uchun kamida 6 oy kerak — deputatlar", "!", 259.6)], 250.7, 264.1, title="Eng katta noaniqlik — muddatlar")])
    add(264.1, 270.9, G(), [stamp("2027", 266.2, 270.9, "olti yoshli bolalarni to‘liq qamrab olish rejasi", color=GOLD),
        headline("Ma’lum bo‘lgan yagona aniq sana", 264.2, 266.2, y=420, size=60)])
    add(270.9, 277.6, P("om_bob", 1.12, 1.0, (0.5, 0.45), (0.5, 0.5), dark=0.35), [
        card(110, 260, 960, "Ota-onalar uchun to‘g‘ri yo‘l", "Mish-mishlar emas — Senat qarori va rasmiy e’lonlar", 271.0, 277.6, accent=GREEN, title_size=50, body_size=40)])
    add(277.6, 285.8, G(), [checklist([("20 ming yangi o‘rin o‘z vaqtida yaratiladimi?", "?", 279.4), ("Bog‘chadagi tayyorlov sifati maktabdagidan qolishmaydimi?", "?", 282.1)],
                                       277.7, 285.8, title="Ochiq qolayotgan ikki savol")])
    add(285.8, 290.6, P(sch1, 1.0, 1.1, dark=0.35), [headline("Javobni qog‘ozdagi qonun emas — amaliyot beradi", 285.9, 290.6, y=860, size=48)])
    # --- conclusion 290-328
    add(290.6, 295.1, G(), [bumper("XULOSA", 290.65, 292.2, color=BLUE),
        El(lambda d, t: (draw_text(d, (W / 2, H / 2), "12-SINF", 200, fill=GREY, weight="Black", anchor="mm", alpha=fade(t, 292.3, 295.1)),
                         d.line((W / 2 - 460, H / 2 + 60, W / 2 + 460, H / 2 - 60), fill=RED + (int(255 * prog(t, 294.6, 0.25) * fade(t, 292.3, 295.1)),), width=26)), 292.3, 295.1)])
    add(295.1, 301.1, G(), [headline("Tayyorlov yili — ta’lim tizimining rasmiy boshlanishi", 295.2, 301.1, y=200, size=54), years_blocks(295.1, 301.1, "final")])
    add(301.1, 307.4, P(grads, 1.0, 1.12, dark=0.45), [
        card(110, 250, 1000, "Bolalar maktabga tayyorroq kelsin", None, 301.8, 307.4, accent=GREEN, title_size=48),
        card(110, 430, 1000, "Attestat dunyoda tan olinsin", None, 304.5, 307.4, accent=GOLD, title_size=48)])
    add(307.4, 313.2, P(cls1, 1.0, 1.12), [headline("Har qanday islohot sinfxonada sinovdan o‘tadi", 307.5, 313.2, y=hy(cls1), size=48 if cls1 else 64),
        chip("tarbiyachi va o‘qituvchi mehnatida", W / 2, hy(cls1, 760, 640), 309.0, 313.2, color=GOLD, size=36, anchor="c")])
    add(313.2, AUDIO_END, G(), [
        headline("Siz qanday o‘ylaysiz?", 313.3, AUDIO_END, y=150, size=72),
        card(300, 360, 600, "A · Bog‘chada", "tayyorlov yili bog‘chada o‘tgani yaxshi", 316.9, AUDIO_END, accent=GREEN, title_size=52),
        card(1020, 360, 600, "B · Maktabda", "tayyorlov yili maktabda o‘tgani yaxshi", 318.6, AUDIO_END, accent=BLUE, title_size=52),
        chip("Fikringizni izohlarda yozing", W / 2, 760, 319.4, AUDIO_END, color=RED, size=44, anchor="c"),
    ])
    add(AUDIO_END, TOTAL, G(), [credits_roll(AUDIO_END, TOTAL)], credit="", ticker=False)
    S = sorted([s for s in S if s is not None and s.t1 > s.t0], key=lambda s: s.t0)
    for a_, b_ in zip(S, S[1:]):
        assert abs(a_.t1 - b_.t0) < 1e-6, (a_.t0, a_.t1, b_.t0)
    return S

def used_photo_credits():
    keys = []
    for sh in SHOTS_FOR_CREDITS:
        k = getattr(sh.bg, "key", None)
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
        lines = ["VIDEO MANBALARI / FOOTAGE SOURCES", "", "Fotosuratlar (Wikimedia Commons):"]
        row = ""
        for p in photos:
            if len(row) + len(p) > 95: lines.append(row); row = ""
            row = (row + "  ·  " + p) if row else p
        if row: lines.append(row)
        lines += ["", "Faktlar: Kun.uz · Gazeta.uz · Zamon.uz · Ta’lim xabarlari (24–25.11.2026)",
                  "Xarita: Natural Earth / world.geo.json  ·  Musiqa va ovoz effektlari: original",
                  "", "Barcha havolalar va litsenziyalar — video tavsifida"]
        a = fade(t, t0, t1, 0.6); y = 230
        for i, ln in enumerate(lines):
            draw_text(d, (W / 2, y + i * 54), ln, 46 if i == 0 else 30, fill=GOLD if i == 0 else OFF,
                      weight="ExtraBold" if i == 0 else "Medium", anchor="mm", alpha=a)
    return El(fn, t0, t1)

TICKER = "O‘ZBEKISTON · 12 YILLIK TA’LIM: QONUN SENATGA YUBORILDI  ·  BIR YILLIK MAKTABGA TAYYORLOV — MAJBURIY BOSQICH  ·  2027: OLTI YOSHLI BOLALARNI 100% QAMRAB OLISH MAQSADI  ·  "
def draw_chrome(d, t, sh):
    # ticker
    if sh.ticker:
        a = fade(t, 14.0, None, 0.5) if t < 15 else 1.0
        y0 = H - 58
        d.rectangle((0, y0, W, H), fill=(255, 255, 255, int(235 * a)))
        d.rectangle((0, y0, 230, H), fill=RED + (int(255 * a),))
        d.text((115, y0 + 29), "TA’LIM", font=F(30, "Black"), fill=(255, 255, 255, int(255 * a)), anchor="mm")
        f = F(28, "Bold"); tw = f.getlength(TICKER); x = 250 - (t * 110) % tw
        while x < W:
            d.text((x, y0 + 29), TICKER, font=f, fill=NAVY + (int(255 * a),), anchor="lm"); x += tw
        d.rectangle((0, y0, 230, H), fill=RED + (int(255 * a),))
        d.text((115, y0 + 29), "TA’LIM", font=F(30, "Black"), fill=(255, 255, 255, int(255 * a)), anchor="mm")
    # source label
    if sh.credit:
        f = F(20, "SemiBold"); tw = f.getlength(sh.credit)
        a = fade(t, sh.t0 + 0.2, sh.t1 - 0.05, 0.3)
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
