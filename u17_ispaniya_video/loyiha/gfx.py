"""Animated news graphics overlay renderer. Writes raw RGBA frames to stdout (1920x1080 @25fps)."""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edl import SCENES, SRC, TOTAL, FPS

W, H = 1920, 1080
FD = "/usr/share/fonts/opentype/inter/"
def F(size, w="Bold", disp=True):
    return ImageFont.truetype(FD + ("InterDisplay-" if disp else "Inter-") + w + ".otf", size)

NAVY = (9, 20, 38)
NAVY2 = (18, 36, 64)
ACC = (0, 166, 222)     # O'zbekiston bayrog'i ko'ki
GREEN = (30, 181, 58)
RED = (226, 35, 52)
GOLD = (246, 196, 0)
WHITE = (255, 255, 255)
GREY = (178, 188, 204)

A = "‘"  # o‘ g‘ uchun

# ---------------------------------------------------------------- flags
def flag(code, w=96, h=64):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if code == "UZB":
        d.rectangle([0, 0, w, h * 0.32], fill=(0, 153, 181))
        d.rectangle([0, h * 0.32, w, h * 0.68], fill=WHITE)
        d.rectangle([0, h * 0.68, w, h], fill=(30, 181, 58))
        d.rectangle([0, h * 0.32, w, h * 0.34], fill=(206, 17, 38))
        d.rectangle([0, h * 0.66, w, h * 0.68], fill=(206, 17, 38))
        r = h * 0.11; cx, cy = w * 0.16, h * 0.16
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE)
        d.ellipse([cx - r + r * 0.45, cy - r, cx + r + r * 0.45, cy + r], fill=(0, 153, 181))
        for i in range(3):
            for j in range(3 - (1 if i == 0 else 0)):
                x = w * 0.30 + j * w * 0.07 + (w * 0.07 if i == 0 else 0); y = h * 0.07 + i * h * 0.08
                d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=WHITE)
    elif code == "ESP":
        d.rectangle([0, 0, w, h], fill=(170, 21, 27))
        d.rectangle([0, h * 0.25, w, h * 0.75], fill=(241, 191, 0))
    elif code == "ITA":
        for i, c in enumerate([(0, 146, 70), WHITE, (206, 43, 55)]):
            d.rectangle([w * i / 3, 0, w * (i + 1) / 3, h], fill=c)
    elif code == "CIV":
        for i, c in enumerate([(247, 127, 0), WHITE, (0, 158, 96)]):
            d.rectangle([w * i / 3, 0, w * (i + 1) / 3, h], fill=c)
    elif code == "FRA":
        for i, c in enumerate([(0, 85, 164), WHITE, (239, 65, 53)]):
            d.rectangle([w * i / 3, 0, w * (i + 1) / 3, h], fill=c)
    elif code == "ROU":
        for i, c in enumerate([(0, 43, 127), (252, 209, 22), (206, 17, 38)]):
            d.rectangle([w * i / 3, 0, w * (i + 1) / 3, h], fill=c)
    elif code == "CMR":
        for i, c in enumerate([(0, 122, 94), (206, 17, 38), (252, 209, 22)]):
            d.rectangle([w * i / 3, 0, w * (i + 1) / 3, h], fill=c)
        star(d, w / 2, h / 2, h * 0.16, (252, 209, 22))
    elif code == "JAM":
        d.rectangle([0, 0, w, h], fill=(0, 155, 58))
        d.polygon([(0, 0), (w / 2, h / 2), (0, h)], fill=(0, 0, 0))
        d.polygon([(w, 0), (w / 2, h / 2), (w, h)], fill=(0, 0, 0))
        d.line([(0, 0), (w, h)], fill=(254, 209, 0), width=int(h * 0.16))
        d.line([(0, h), (w, 0)], fill=(254, 209, 0), width=int(h * 0.16))
    elif code == "CHN":
        d.rectangle([0, 0, w, h], fill=(222, 41, 16))
        star(d, w * 0.17, h * 0.27, h * 0.15, (255, 222, 0))
    elif code == "MAR":
        d.rectangle([0, 0, w, h], fill=(193, 39, 45))
        star(d, w / 2, h / 2, h * 0.22, (0, 98, 51), outline=True)
    elif code == "FIJ":
        d.rectangle([0, 0, w, h], fill=(104, 191, 229))
        d.rectangle([0, 0, w * 0.5, h * 0.5], fill=(1, 33, 105))
        d.line([(0, 0), (w * 0.5, h * 0.5)], fill=WHITE, width=5); d.line([(0, h * 0.5), (w * 0.5, 0)], fill=WHITE, width=5)
        d.rectangle([w * 0.22, 0, w * 0.28, h * 0.5], fill=(200, 16, 46)); d.rectangle([0, h * 0.22, w * 0.5, h * 0.28], fill=(200, 16, 46))
    elif code == "ENG":
        d.rectangle([0, 0, w, h], fill=WHITE)
        d.rectangle([w * 0.43, 0, w * 0.57, h], fill=(206, 17, 36)); d.rectangle([0, h * 0.4, w, h * 0.6], fill=(206, 17, 36))
    elif code == "CRO":
        for i, c in enumerate([(255, 0, 0), WHITE, (23, 23, 150)]):
            d.rectangle([0, h * i / 3, w, h * (i + 1) / 3], fill=c)
        s = h * 0.36
        for r in range(3):
            for c in range(3):
                col = (255, 0, 0) if (r + c) % 2 == 0 else WHITE
                d.rectangle([w / 2 - s / 2 + c * s / 3, h / 2 - s / 2 + r * s / 3, w / 2 - s / 2 + (c + 1) * s / 3, h / 2 - s / 2 + (r + 1) * s / 3], fill=col)
    elif code == "JPN":
        d.rectangle([0, 0, w, h], fill=WHITE)
        r = h * 0.3; d.ellipse([w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r], fill=(188, 0, 45))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=max(3, h // 10), fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0)); out.paste(im, (0, 0), mask)
    ImageDraw.Draw(out).rounded_rectangle([0, 0, w - 1, h - 1], radius=max(3, h // 10), outline=(255, 255, 255, 90), width=2)
    return out

def star(d, cx, cy, r, col, outline=False):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.4
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    if outline:
        d.polygon(pts, outline=col, width=3)
    else:
        d.polygon(pts, fill=col)

# ---------------------------------------------------------------- primitives
def canvas(w, h):
    return Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))

def tsize(font, text):
    b = font.getbbox(text)
    return b[2] - b[0], b[3] - b[1], b[0], b[1]

def text_img(text, font, fill=WHITE, shadow=True, stroke=0):
    tw, th, ox, oy = tsize(font, text)
    pad = 20
    im = canvas(tw + pad * 2, th + pad * 2)
    d = ImageDraw.Draw(im)
    if shadow:
        sh = canvas(*im.size)
        ImageDraw.Draw(sh).text((pad - ox + 3, pad - oy + 5), text, font=font, fill=(0, 0, 0, 170))
        sh = sh.filter(ImageFilter.GaussianBlur(6))
        im = Image.alpha_composite(im, sh); d = ImageDraw.Draw(im)
    d.text((pad - ox, pad - oy), text, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
    return im, pad

def panel(w, h, col=NAVY, alpha=230, radius=6):
    im = canvas(w, h)
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=col + (alpha,))
    return im

def drop(im, blur=14, off=8, a=140):
    w, h = im.size
    out = canvas(w + 60, h + 60)
    sh = canvas(w + 60, h + 60)
    alpha = im.split()[3].point(lambda v: v * a // 255)
    blk = Image.new("RGBA", im.size, (0, 0, 0, 255)); blk.putalpha(alpha)
    sh.paste(blk, (30, 30 + off), blk)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    out = Image.alpha_composite(out, sh)
    out.alpha_composite(im, (30, 30))
    return out, 30

# ---------------------------------------------------------------- element builders
# each returns (image, x, y) for full-state placement
def el_kinetic(text, size=120, col=WHITE, y=None, box=None, sub=None, subcol=GREY, weight="Black"):
    f = F(size, weight)
    t, pad = text_img(text, f, col)
    parts = [t]
    if sub:
        fs_ = F(max(34, int(size * 0.34)), "Bold")
        st, spad = text_img(sub, fs_, subcol, shadow=False)
        s = canvas(st.size[0], st.size[1])
        ImageDraw.Draw(s).rounded_rectangle([spad - 18, spad - 12, st.size[0] - spad + 18, st.size[1] - spad + 12], radius=8, fill=NAVY + (215,))
        s.alpha_composite(st)
        parts.append(s)
    w = max(p.size[0] for p in parts)
    h = sum(p.size[1] for p in parts) - (pad if sub else 0)
    im = canvas(w + 60, h + 40)
    yy = 20
    if box:
        bw = parts[0].size[0] - pad * 2 + 60
        bh = parts[0].size[1] - pad * 2 + 36
        ImageDraw.Draw(im).rectangle([(im.size[0] - bw) // 2, yy + pad - 18, (im.size[0] + bw) // 2, yy + pad - 18 + bh], fill=box + (235,))
    for p in parts:
        im.alpha_composite(p, ((im.size[0] - p.size[0]) // 2, yy))
        yy += p.size[1] - pad
    x = (W - im.size[0]) // 2
    if y is None:
        y = (H - im.size[1]) // 2
    return im, x, y

def el_lower_third(title, sub=None, accent=ACC, x=110, y=830):
    ft = F(54, "ExtraBold"); fs = F(32, "Medium", disp=False)
    tw, th, ox, oy = tsize(ft, title)
    sw = tsize(fs, sub)[0] if sub else 0
    w = max(tw, sw) + 90
    h1 = 84; h2 = 56 if sub else 0
    im = canvas(w + 14, h1 + h2)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 12, h1 + h2 - 1], fill=accent + (255,))
    d.rectangle([14, 0, w + 13, h1 - 1], fill=WHITE + (245,))
    d.text((44 - ox, (h1 - th) // 2 - oy), title, font=ft, fill=NAVY)
    if sub:
        d.rectangle([14, h1, w + 13, h1 + h2 - 1], fill=NAVY + (235,))
        sx, sy = tsize(fs, sub)[2:]
        d.text((44 - sx, h1 + (h2 - tsize(fs, sub)[1]) // 2 - sy), sub, font=fs, fill=WHITE)
    im, p = drop(im)
    return im, x - p, y - p

def el_tag(text, col=RED, x=70, y=60, icon=None):
    f = F(30, "Bold")
    tw, th, ox, oy = tsize(f, text)
    extra = 34 if icon else 0
    im = canvas(tw + 44 + extra, 52)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, im.size[0] - 1, 51], fill=col + (240,))
    if icon == "pin":
        d.ellipse([16, 10, 36, 30], fill=WHITE); d.polygon([(18, 25), (34, 25), (26, 42)], fill=WHITE)
        d.ellipse([22, 16, 30, 24], fill=col)
    if icon == "dot":
        d.ellipse([16, 18, 32, 34], fill=WHITE)
    d.text((22 + extra - ox, (52 - th) // 2 - oy), text, font=f, fill=WHITE)
    return im, x, y

def el_credit(text):
    f = F(22, "SemiBold", disp=False)
    tw, th, ox, oy = tsize(f, text)
    im = canvas(tw + 28, 38)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, im.size[0] - 1, 37], fill=(0, 0, 0, 150))
    d.rectangle([0, 0, 3, 37], fill=ACC + (255,))
    d.text((16 - ox, (38 - th) // 2 - oy), text, font=f, fill=(235, 240, 248))
    return im, W - im.size[0] - 48, H - 38 - 44

def el_section(num, title, sub=None):
    im = canvas(W, H)
    d = ImageDraw.Draw(im)
    fn = F(260, "Black"); ft = F(96, "Black"); fs = F(38, "SemiBold", disp=False)
    nw, nh, nox, noy = tsize(fn, num)
    d.text((150 - nox, 300 - noy), num, font=fn, fill=ACC + (255,))
    d.rectangle([150, 300 + nh + 40, 150 + 140, 300 + nh + 50], fill=GOLD + (255,))
    tw, th, tox, toy = tsize(ft, title)
    d.text((150 - tox, 300 + nh + 80 - toy), title, font=ft, fill=WHITE)
    if sub:
        d.text((154, 300 + nh + 80 + th + 30), sub, font=fs, fill=GREY)
    return im, 0, 0

def el_scorebox(ta, fa, sa, sb, tb, fb, sub=None, y=70, big=False):
    s = 1.35 if big else 1.0
    ft = F(int(40 * s), "ExtraBold"); fsc = F(int(64 * s), "Black"); fsub = F(int(26 * s), "SemiBold", disp=False)
    taw = tsize(ft, ta)[0]; tbw = tsize(ft, tb)[0]
    side = max(taw, tbw) + int(140 * s)
    mid = int(200 * s)
    w = side * 2 + mid; h = int(96 * s)
    hs = int(48 * s) if sub else 0
    im = canvas(w, h + hs)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, side - 1, h - 1], fill=NAVY + (240,))
    d.rectangle([side + mid, 0, w - 1, h - 1], fill=NAVY + (240,))
    d.rectangle([side, 0, side + mid - 1, h - 1], fill=WHITE + (250,))
    fA = flag(fa, int(66 * s), int(44 * s)); fB = flag(fb, int(66 * s), int(44 * s))
    im.alpha_composite(fA, (int(24 * s), (h - fA.size[1]) // 2))
    im.alpha_composite(fB, (w - int(24 * s) - fB.size[0], (h - fB.size[1]) // 2))
    for txt, cx in ((ta, int(24 * s) + fA.size[0] + int(20 * s)), (tb, None)):
        tw, th, ox, oy = tsize(ft, txt)
        if cx is None:
            cx = w - int(24 * s) - fB.size[0] - int(20 * s) - tw
        d.text((cx - ox, (h - th) // 2 - oy), txt, font=ft, fill=WHITE)
    sc = f"{sa} : {sb}"
    tw, th, ox, oy = tsize(fsc, sc)
    d.text((side + (mid - tw) // 2 - ox, (h - th) // 2 - oy), sc, font=fsc, fill=NAVY)
    if sub:
        d.rectangle([0, h, w - 1, h + hs - 1], fill=ACC + (240,))
        tw, th, ox, oy = tsize(fsub, sub)
        d.text(((w - tw) // 2 - ox, h + (hs - th) // 2 - oy), sub, font=fsub, fill=WHITE)
    im, p = drop(im)
    return im, (W - im.size[0]) // 2, y - p

def el_panel_title(title, x, y, w, col=ACC):
    f = F(44, "Black")
    im = canvas(w, 76)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, 75], fill=col + (245,))
    tw, th, ox, oy = tsize(f, title)
    d.text((28 - ox, (76 - th) // 2 - oy), title, font=f, fill=WHITE)
    return im, x, y

def el_row(text, x, y, w, num=None, fl=None, right=None, hl=False, col=NAVY, icon=None, fsize=38):
    f = F(fsize, "Bold"); fr = F(fsize, "Black")
    h = int(fsize * 1.9)
    im = canvas(w, h)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=(ACC if hl else col) + (232,))
    d.line([(0, h - 1), (w, h - 1)], fill=(255, 255, 255, 40), width=1)
    cx = 26
    if num is not None:
        nw, nh, ox, oy = tsize(fr, str(num))
        d.text((cx - ox, (h - nh) // 2 - oy), str(num), font=fr, fill=GOLD if not hl else WHITE)
        cx += 64
    if fl:
        fi = flag(fl, int(h * 0.75), int(h * 0.5)); im.alpha_composite(fi, (cx, (h - fi.size[1]) // 2)); cx += fi.size[0] + 22
    tw, th, ox, oy = tsize(f, text)
    d.text((cx - ox, (h - th) // 2 - oy), text, font=f, fill=WHITE)
    if right is not None:
        rw, rh, ox, oy = tsize(fr, right)
        d.text((w - 30 - rw - ox, (h - rh) // 2 - oy), right, font=fr, fill=WHITE)
    if icon == "ok":
        d.line([(w - 70, h // 2), (w - 58, h // 2 + 12), (w - 36, h // 2 - 14)], fill=GREEN, width=7)
    if icon == "x":
        d.line([(w - 66, h // 2 - 12), (w - 42, h // 2 + 12)], fill=RED, width=7)
        d.line([(w - 66, h // 2 + 12), (w - 42, h // 2 - 12)], fill=RED, width=7)
    return im, x, y

def el_quote(text, x=None, y=640, w=1300):
    f = F(52, "Bold"); fq = F(150, "Black")
    words = text.split(); lines = []; cur = ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if tsize(f, t)[0] > w - 200 and cur:
            lines.append(cur); cur = wd
        else:
            cur = t
    lines.append(cur)
    lh = 70
    h = 80 + lh * len(lines)
    im = canvas(w, h)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=14, fill=WHITE + (245,))
    d.rectangle([0, 0, 14, h - 1], fill=ACC + (255,))
    d.text((40, -40), "“", font=fq, fill=ACC)
    for i, ln in enumerate(lines):
        d.text((140, 40 + i * lh), ln, font=f, fill=NAVY)
    im, p = drop(im)
    return im, ((W - w) // 2 if x is None else x) - p, y - p

def el_bug():
    f = F(24, "Bold", disp=False)
    t = "U-17 JAHON CHEMPIONATI  ·  QATAR 2026"
    tw, th, ox, oy = tsize(f, t)
    im = canvas(tw + 70, 42)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 40, 41], fill=ACC + (240,))
    d.rectangle([40, 0, im.size[0] - 1, 41], fill=NAVY + (200,))
    d.polygon([(12, 10), (30, 21), (12, 32)], fill=WHITE)
    d.text((54 - ox, (42 - th) // 2 - oy), t, font=f, fill=WHITE)
    return im, 48, H - 42 - 30

def el_brand():
    f = F(26, "Black")
    t = "SADO STUDIO"
    im, p = text_img(t, f, (255, 255, 255, 200), shadow=True)
    return im, W - im.size[0] - 30, 30

def el_letterbox():
    im = canvas(W, H)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 118], fill=(0, 0, 0, 255)); d.rectangle([0, H - 118, W, H], fill=(0, 0, 0, 255))
    return im, 0, 0

def el_full(col, a=255):
    return Image.new("RGBA", (W, H), col + (a,)), 0, 0

def el_matchday():
    im = canvas(W, H)
    d = ImageDraw.Draw(im)
    fh = F(46, "Bold", disp=False); fT = F(84, "Black"); fv = F(70, "Black"); fd = F(64, "Black"); fs = F(36, "SemiBold", disp=False)
    def ctext(t, f, y, col=WHITE):
        tw, th, ox, oy = tsize(f, t); d.text(((W - tw) // 2 - ox, y - oy), t, font=f, fill=col); return th
    d.rectangle([(W - 420) // 2, 150, (W + 420) // 2, 222], fill=GOLD + (255,))
    ctext("1/16 FINAL", F(44, "Black"), 166, NAVY)
    fu = flag("UZB", 270, 180); fe = flag("ESP", 270, 180)
    im.alpha_composite(fu, (360, 300)); im.alpha_composite(fe, (W - 360 - 270, 300))
    tw = tsize(fT, "O" + A + "ZBEKISTON")[0]
    d.text((360 + 135 - tw // 2, 510), "O" + A + "ZBEKISTON", font=fT, fill=WHITE)
    tw = tsize(fT, "ISPANIYA")[0]
    d.text((W - 360 - 135 - tw // 2, 510), "ISPANIYA", font=fT, fill=WHITE)
    ctext("VS", fv, 350, ACC)
    d.rectangle([(W - 900) // 2, 690, (W + 900) // 2, 692], fill=(255, 255, 255, 120))
    ctext("30-NOYABR  ·  20:30", fd, 730)
    ctext("Toshkent vaqti bilan  ·  Doha, Qatar", fs, 830, GREY)
    return im, 0, 0

def el_timeline():
    im = canvas(W, H)
    return im, 0, 0

# ---------------------------------------------------------------- animation + timeline
class E:
    def __init__(self, t0, t1, built, anim="fade", fin=0.35, fout=0.25, dx=0, dy=0):
        self.t0, self.t1 = t0, t1
        self.im, self.x, self.y = built
        self.anim, self.fin, self.fout = anim, fin, fout
        self.arr = None

def ease(u):
    u = max(0.0, min(1.0, u)); return 1 - (1 - u) ** 3

ELS = []
def add(t0, t1, built, anim="fade", **kw):
    ELS.append(E(t0, t1, built, anim, **kw))

def O(s):  # Uzbek o‘/g‘ helper: write O' -> O‘
    return s.replace("'", A)

# --- persistent / structural
add(0.0, 13.30, el_letterbox(), "none", fin=0, fout=0.3)
add(13.6, 307.8, el_bug(), "slide", fin=0.5)
add(13.6, 307.8, el_brand(), "fade", fin=0.6)

# --- source credits per scene
for (t0, t1, src, sin, look, note) in SCENES:
    if src is None:
        continue
    name = SRC[src][2]
    txt = f"VIDEO: {name} / YouTube"
    if look == "a" or (src == "JTP"):
        txt = f"ARXIV 2023  ·  VIDEO: {name} / YouTube"
    add(t0 + 0.05, t1 - 0.02, el_credit(O(txt)), "fade", fin=0.2, fout=0.15)

# --- flashes (white dips) at hard section changes
for t in (0.0, 8.40, 13.30, 34.0, 116.6, 151.8, 208.7, 282.3):
    add(t, t + 0.22, el_full(WHITE, 255), "flash", fin=0, fout=0.22)

# HOOK
add(0.25, 1.68, el_kinetic("22 GOL", 210, GOLD), "pop")
add(1.80, 3.58, el_kinetic("0 TA O'TKAZILGAN".replace("'", A), 150, WHITE), "pop")
add(3.95, 8.35, el_kinetic("30-NOYABR", 120, WHITE, y=780, sub="1/16 FINAL  ·  QATAR 2026", subcol=GOLD), "slideup")
add(8.42, 9.24, el_kinetic("ISPANIYA", 230, WHITE, box=RED), "pop")
add(9.28, 10.28, el_kinetic("SAVOL BITTA:", 130, WHITE), "fade", fin=0.15)
add(10.36, 11.53, el_kinetic(O("MO'JIZAMI?"), 170, GOLD), "pop")
add(11.62, 13.28, el_kinetic("...YOKI TUZOQMI?", 150, WHITE, box=RED), "pop")

add(13.6, 17.6, el_lower_third(O("O'ZBEKISTON U-17"), "FIFA U-17 Jahon chempionati  ·  Qatar 2026"), "slide")
# agenda
add(17.9, 26.6, el_panel_title("BUGUN", 110, 300, 760), "slide")
add(18.0, 26.6, el_row(O("Pley-offga qanday chiqdik"), 110, 376, 760, num=1), "slide")
add(21.5, 26.6, el_row(O("Ispaniya nega qo'rqinchli"), 110, 448, 760, num=2), "slide")
add(24.1, 26.6, el_row("Nega baribir umid bor", 110, 520, 760, num=3, hl=True), "slide")
add(27.0, 33.8, el_tag("ARXIV  ·  2023", RED, icon="dot"), "slide")
add(28.3, 33.8, el_lower_third(O("O'ZBEKISTON — ISPANIYA"), "3 yil oldin ham uchrashgan"), "slide")
# section 01
add(34.0, 35.55, el_section("01", O("PLEY-OFFGA YO'L")), "wipe", fin=0.3, fout=0.2)
add(35.8, 40.5, el_tag("DOHA  ·  QATAR", ACC, icon="pin", y=110), "slide")
COUNTER = [(38.35, 40.5, 48, "JAMOA", 0.9)]
add(40.7, 49.2, el_panel_title("TURNIR FORMATI", 110, 250, 900), "slide")
add(40.9, 49.2, el_row("48 jamoa  ·  12 guruh", 110, 326, 900), "slide")
add(41.6, 49.2, el_row(O("1- va 2-o'rin  →  1/16 final"), 110, 398, 900, icon="ok"), "slide")
add(45.0, 49.2, el_row(O("3-o'rin: eng yaxshi 8 tasi  →  1/16 final"), 110, 470, 900, hl=True), "slide")
add(47.0, 49.2, el_row("Jami pley-offda: 32 jamoa", 110, 542, 900), "slide")
# group E
GX = 1080
add(49.5, 55.5, el_panel_title("E GURUH", GX, 300, 720), "slide")
add(50.3, 55.5, el_row(O("O'zbekiston"), GX, 376, 720, fl="UZB", hl=True), "slide")
add(53.2, 55.5, el_row(O("Kot-d'Ivuar"), GX, 448, 720, fl="CIV"), "slide")
add(53.9, 55.5, el_row("Yamayka", GX, 520, 720, fl="JAM"), "slide")
add(54.5, 55.5, el_row("Italiya", GX, 592, 720, fl="ITA"), "slide")
# match 1
add(55.8, 59.2, el_lower_third("1-TUR  ·  20-NOYABR", O("Kot-d'Ivuar — O'zbekiston")), "slide")
add(59.5, 64.1, el_scorebox(O("KOT-D'IVUAR"), "CIV", 2, 1, O("O'ZBEKISTON"), "UZB", sub="Yakuniy hisob  ·  1-tur, E guruh"), "drop")
add(64.4, 69.3, el_lower_third("2-TUR  ·  23-NOYABR", O("O'zbekiston — Yamayka")), "slide")
add(69.6, 73.1, el_scorebox(O("O'ZBEKISTON"), "UZB", 6, 2, "YAMAYKA", "JAM", sub="Yakuniy hisob  ·  2-tur, E guruh"), "drop")
add(73.4, 76.0, el_lower_third("SUXROB SADIRJONOV", "Xet-trik  ·  Yamaykaga qarshi 3 gol", accent=GOLD), "slide")
add(76.2, 80.6, el_panel_title(O("GOLLAR: O'ZBEKISTON 6:2 YAMAYKA"), 110, 330, 860, col=GREEN), "slide")
add(76.3, 80.6, el_row("Suxrob Sadirjonov", 110, 406, 860, right="×3"), "slide")
add(77.4, 80.6, el_row("Laziz Abduraimov", 110, 478, 860, right="×1"), "slide")
add(78.6, 80.6, el_row("Amirxon Erkinov", 110, 550, 860, right="×1"), "slide")
add(79.6, 80.6, el_row("Axror Ravshanbekov", 110, 622, 860, right="×1"), "slide")
add(80.8, 82.5, el_kinetic("HAL QILUVCHI O'YIN".replace("'", A), 110, WHITE, y=760), "slideup")
add(82.8, 87.2, el_lower_third("3-TUR  ·  26-NOYABR", O("O'zbekiston — Italiya")), "slide")
add(85.1, 87.2, el_tag("ITALIYA: 3 O'YIN  ·  9 OCHKO".replace("'", A), (0, 120, 70), y=110), "slide")
add(87.35, 89.5, el_scorebox(O("O'ZBEKISTON"), "UZB", 1, 3, "ITALIYA", "ITA", sub="Yakuniy hisob  ·  3-tur, E guruh"), "drop")
# table
TX = 510
add(89.7, 94.5, el_panel_title("E GURUH  ·  YAKUNIY JADVAL", TX, 250, 900), "slide")
add(89.9, 94.5, el_row("Italiya", TX, 326, 900, num=1, fl="ITA", right="9"), "slide")
add(90.2, 94.5, el_row(O("Kot-d'Ivuar"), TX, 398, 900, num=2, fl="CIV", right="6"), "slide")
add(90.5, 94.5, el_row(O("O'zbekiston   (8:7)"), TX, 470, 900, num=3, fl="UZB", right="3", hl=True), "slide")
add(90.8, 94.5, el_row("Yamayka", TX, 542, 900, num=4, fl="JAM", right="0"), "slide")
add(92.6, 94.5, el_kinetic(O("3-O'RIN"), 64, NAVY, y=630, box=GOLD), "pop")
add(95.0, 99.9, el_kinetic(O("HISOB-KITOB OXIRGI DAQIQAGACHA"), 76, WHITE, y=800), "slideup")
add(100.3, 102.9, el_lower_third(O("RUMINIYA — KAMERUN"), O("27-noyabr  ·  hal qiluvchi o'yin")), "slide")
add(103.1, 107.5, el_scorebox("RUMINIYA", "ROU", 3, 1, "KAMERUN", "CMR", sub=O("Kamerun goli — qo'shimcha vaqtda")), "drop")
add(105.2, 107.5, el_panel_title(O("ENG YAXSHI 3-O'RINLAR"), 560, 470, 800, col=NAVY2), "slide")
add(105.4, 107.5, el_row(O("O'zbekiston  —  3 ochko"), 560, 546, 800, num=8, fl="UZB", icon="ok", hl=True), "slide")
add(105.8, 107.5, el_row("Ruminiya  —  3 ochko", 560, 618, 800, fl="ROU", icon="x"), "slide")
add(108.0, 111.7, el_kinetic(O("OXIRGI YO'LLANMA"), 140, GOLD, sub=O("pley-offga — O'zbekiston")), "pop")
add(112.1, 116.4, el_quote(O("Yigitlarimiz eshik yopilayotgan paytda kirib oldi")), "slideup")
# section 02
add(116.6, 120.3, el_section("02", "RAQIB: ISPANIYA", O("Guruh bosqichi: 3 o'yin — 3 g'alaba")), "wipe", fin=0.3, fout=0.2)
RX = 560
add(120.6, 126.1, el_panel_title("ISPANIYA  ·  GURUH BOSQICHI", RX, 250, 800, col=RED), "slide")
add(120.8, 126.1, el_row("Ispaniya — Xitoy", RX, 326, 800, fl="ESP", right="5:0"), "slide")
add(121.4, 126.1, el_row("Ispaniya — Fiji", RX, 398, 800, fl="ESP", right="15:0"), "slide")
add(122.0, 126.1, el_row("Marokash — Ispaniya", RX, 470, 800, fl="MAR", right="0:2"), "slide")
add(123.3, 126.1, el_row(O("To'plar farqi"), RX, 542, 800, right="22 : 0", hl=True), "slide")
add(126.4, 129.5, el_kinetic("15 GOL", 190, WHITE, sub="faqat Fiji darvozasiga"), "pop")
add(129.8, 133.3, el_kinetic(O("...HECH NARSANI ISBOTLAMAYDI"), 80, WHITE, y=800), "slideup")
add(133.8, 137.5, el_kinetic("0", 300, GOLD, sub=O("3 o'yinda o'tkazilgan gol")), "pop")
add(137.8, 140.7, el_kinetic(O("JUDA YAXSHI TASHKIL ETILGAN"), 80, WHITE, y=800), "slideup")
add(141.0, 151.6, el_panel_title("ISPANIYA USLUBI", 110, 300, 760, col=RED), "slide")
add(142.4, 151.6, el_row(O("To'pni deyarli boy bermaydi"), 110, 376, 760, num=1), "slide")
add(144.5, 151.6, el_row("Raqibni yugurtirib charchatadi", 110, 448, 760, num=2), "slide")
add(146.3, 151.6, el_row("Bitta xatoni kutadi", 110, 520, 760, num=3), "slide")
add(149.9, 151.7, el_kinetic("SABR  ·  INTIZOM", 120, WHITE, y=780, box=ACC), "pop")
# section 03
add(151.8, 155.4, el_section("03", O("UNUTILGAN O'YIN"), "FIFA U-17 Jahon chempionati 2023  ·  Indoneziya"), "wipe", fin=0.3, fout=0.2)
add(155.7, 162.3, el_tag("ARXIV  ·  2023", RED, icon="dot"), "slide")
add(156.6, 162.3, el_lower_third("INDONEZIYA  ·  2023", O("B guruh  ·  16-noyabr  ·  O'zbekiston — Ispaniya")), "slide")
SCORE23 = (162.5, 171.1)
add(163.2, 171.1, el_row("10'  Igor Oyono".replace("'", "′"), 560, 520, 800, fl="ESP", right="0:1"), "slide")
add(164.0, 171.1, el_row("19'  Roberto Martin".replace("'", "′"), 560, 592, 800, fl="ESP", right="0:2"), "slide")
add(167.2, 171.1, el_row("45+4'  Behruz Shukurullayev".replace("'", "′"), 560, 664, 800, fl="UZB", right="1:2"), "slide")
add(168.6, 171.1, el_row("53'  Amirbek Saidov".replace("'", "′"), 560, 736, 800, fl="UZB", right="2:2", hl=True), "slide")
add(171.3, 178.9, el_tag("ARXIV  ·  2023", RED, icon="dot"), "slide")
add(173.5, 178.9, el_scorebox("ANGLIYA", "ENG", 1, 2, O("O'ZBEKISTON"), "UZB", sub="1/8 final  ·  2023"), "drop")
add(177.1, 178.9, el_kinetic("CHORAK FINAL!", 110, GOLD, y=760), "pop")
add(179.1, 184.5, el_scorebox("FRANSIYA", "FRA", 1, 0, O("O'ZBEKISTON"), "UZB", sub="Chorak final  ·  25-noyabr 2023", y=380, big=True), "drop")
add(180.9, 184.5, el_kinetic(O("Fransiya — turnirning bo'lajak finalchisi"), 46, WHITE, y=720, weight="Bold"), "slideup")
add(186.4, 191.2, el_kinetic(O("YEVROPA GIGANTLARI BILAN TENG"), 84, WHITE, y=790), "slideup")
add(191.6, 198.2, el_panel_title(O("O'ZBEKISTON U-17 — ENG YAXSHI NATIJALAR"), 460, 330, 1000), "slide")
add(192.6, 198.2, el_row("2011  ·  Meksika", 460, 406, 1000, right="CHORAK FINAL"), "slide")
add(194.7, 198.2, el_row("2023  ·  Indoneziya", 460, 478, 1000, right="CHORAK FINAL", hl=True), "slide")
add(198.4, 202.3, el_lower_third("QATAR 2025", O("O'tgan yilgi jahon chempionati")), "slide")
add(202.5, 206.5, el_scorebox("XORVATIYA", "CRO", 1, 1, O("O'ZBEKISTON"), "UZB", sub=O("Penaltilar seriyasi: 3:4  ·  O'zbekiston g'olib")), "drop")
add(206.7, 208.6, el_scorebox("ITALIYA", "ITA", 3, 2, O("O'ZBEKISTON"), "UZB", sub="1/8 final  ·  2025"), "drop")
# section 04
add(208.7, 212.2, el_section("04", "TAHLIL", O("Bu safargi jamoada nima bor?")), "wipe", fin=0.3, fout=0.2)
add(212.5, 216.3, el_kinetic("HUJUM", 150, WHITE, sub=O("3 o'yin  ·  8 gol"), subcol=GREEN), "pop")
add(216.6, 221.1, el_kinetic("IRODA", 150, WHITE, sub=O("1:2 mag'lubiyatdan keyin — 6:2 g'alaba"), subcol=GOLD), "pop")
add(221.3, 224.9, el_lower_third("SERGEY CHIGODAYEV", O("O'zbekiston U-17 bosh murabbiyi")), "slide")
add(225.2, 229.3, el_kinetic("MUAMMO: HIMOYA", 130, WHITE, box=RED), "pop")
add(229.5, 232.9, el_kinetic("7", 280, RED, sub=O("3 o'yinda o'tkazilgan gol")), "pop")
add(233.1, 237.2, el_kinetic(O("JARIMA MAYDONIDAGI HAR BIR XATO — QIMMAT"), 64, WHITE, y=800), "slideup")
add(237.6, 256.5, el_tag("MUXLISLAR FIKRI  ·  ijtimoiy tarmoqlardan umumlashtirildi", ACC, y=110), "slide")
add(240.6, 244.4, el_quote(O("Omad kulib boqdi — endi yo'qotadigan narsamiz yo'q.")), "slideup")
add(244.7, 250.5, el_quote(O("Ispaniya bizni katta hisobda yutadi.")), "slideup")
add(250.8, 256.4, el_quote(O("2023-yildagi 2:2 ni eslang — hech narsa oldindan hal bo'lmagan.")), "slideup")
add(257.0, 262.3, el_kinetic("SKAUTLAR NIGOHIDA", 120, WHITE, sub="U-17 JCh — katta klublar kuzatadigan turnir"), "pop")
add(262.6, 266.2, el_lower_third("SUXROB SADIRJONOV", "Turnirda 4 gol", accent=GOLD), "slide")
add(266.5, 271.9, el_kinetic("BUGUN — 17 YOSH", 110, WHITE, sub="ertaga — Yevropa klubi?", subcol=GOLD), "pop")
add(272.3, 276.2, el_lower_third("AFC U-17 OSIYO KUBOGI  ·  2026", O("Yarim final  ·  Yaponiya — O'zbekiston")), "slide")
add(276.5, 282.2, el_scorebox("YAPONIYA", "JPN", 1, 1, O("O'ZBEKISTON"), "UZB", sub=O("Penaltilarda Yaponiya g'olib")), "drop")
add(282.4, 288.2, el_matchday(), "fade", fin=0.4)
add(288.5, 290.2, el_kinetic(O("QOG'OZDA — ISPANIYA KUCHLI"), 96, WHITE, y=790), "slideup")
add(290.4, 292.4, el_kinetic(O("AMMO FUTBOL QOG'OZDA O'YNALMAYDI"), 84, GOLD, y=790), "slideup")
add(292.6, 295.6, el_kinetic("2023: 2:2", 200, WHITE, sub=O("bir marta isbotlangan")), "pop")
add(296.0, 301.9, el_kinetic(O("SIZNINGCHA, HISOB QANDAY BO'LADI?"), 84, WHITE, y=250), "slideup")
add(296.6, 301.9, el_scorebox(O("O'ZBEKISTON"), "UZB", "?", "?", "ISPANIYA", "ESP", sub="Bashoratingizni izohlarda yozing", y=480, big=True), "drop")
add(302.2, 308.2, el_kinetic(O("OBUNA BO'LING"), 110, WHITE, box=RED, sub=O("O'yin tahlilini o'tkazib yubormang")), "pop")
add(308.4, 310.51, el_kinetic("OMAD, YIGITLAR!", 170, GOLD), "pop", fout=0.01)
FADE_BLACK = (309.9, 310.51)

# ---------------------------------------------------------------- dynamic elements (counter, 2023 scoreboard)
_cache = {}
def counter_img(v, label):
    k = ("c", v, label)
    if k not in _cache:
        _cache[k] = el_kinetic(str(v), 240, WHITE, sub=label, subcol=GOLD)
    return _cache[k]

def score23_img(a, b):
    k = ("s23", a, b)
    if k not in _cache:
        _cache[k] = el_scorebox(O("O'ZBEKISTON"), "UZB", a, b, "ISPANIYA", "ESP", sub="FIFA U-17 JCh 2023  ·  B guruh", y=300, big=True)
    return _cache[k]

def score23(t):
    a, b = 0, 0
    if t >= 163.2: b = 1
    if t >= 164.0: b = 2
    if t >= 167.2: a = 1
    if t >= 168.6: a = 2
    return a, b

# ---------------------------------------------------------------- compositor
def place(frame, im, x, y, alpha=1.0):
    if alpha <= 0.003:
        return
    if alpha < 0.999:
        a = np.asarray(im).copy()
        a[..., 3] = (a[..., 3].astype(np.float32) * alpha).astype(np.uint8)
        im = Image.fromarray(a, "RGBA")
    frame.alpha_composite(im, (int(x), int(y))) if (x >= 0 and y >= 0 and x + im.size[0] <= W and y + im.size[1] <= H) \
        else _safe(frame, im, int(x), int(y))

def _safe(frame, im, x, y):
    l, t = max(0, -x), max(0, -y)
    r, b = min(im.size[0], W - x), min(im.size[1], H - y)
    if r <= l or b <= t:
        return
    frame.alpha_composite(im.crop((l, t, r, b)), (x + l, y + t))

def state(e, t):
    """returns (alpha, dx, dy, scale)"""
    if t < e.t0 or t >= e.t1:
        return 0, 0, 0
    ui = (t - e.t0) / e.fin if e.fin > 0 else 1.0
    uo = (e.t1 - t) / e.fout if e.fout > 0 else 1.0
    a = min(1.0, ui, uo)
    ein = ease(ui)
    if e.anim == "flash":
        return max(0.0, 1 - (t - e.t0) / max(e.fout, 1e-3)) * 0.85, 0, 0
    if e.anim == "slide":
        return a, -60 * (1 - ein), 0
    if e.anim == "slideup":
        return a, 0, 50 * (1 - ein)
    if e.anim == "drop":
        return a, 0, -40 * (1 - ein)
    if e.anim == "pop":
        return a, 0, 24 * (1 - ein)
    if e.anim == "wipe":
        return a, -120 * (1 - ein), 0
    if e.anim == "none":
        return (1.0 if uo >= 1 else max(0.0, uo)), 0, 0
    return a, 0, 0

def render(t):
    frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # section backdrop darken for section cards
    for e in ELS:
        a, dx, dy = state(e, t)
        if a > 0:
            place(frame, e.im, e.x + dx, e.y + dy, a)
    for (t0, t1, v, label, ramp) in COUNTER:
        if t0 <= t < t1:
            u = ease((t - t0) / ramp)
            im, x, y = counter_img(int(round(v * u)), label)
            a = min(1, (t - t0) / 0.2, (t1 - t) / 0.25)
            place(frame, im, x, y + 20, a)
    if SCORE23[0] <= t < SCORE23[1]:
        im, x, y = score23_img(*score23(t))
        a = min(1, (t - SCORE23[0]) / 0.3, (SCORE23[1] - t) / 0.25)
        place(frame, im, x, y - 120, a)
    if t >= FADE_BLACK[0]:
        u = min(1.0, (t - FADE_BLACK[0]) / (FADE_BLACK[1] - FADE_BLACK[0]))
        blk = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * u)))
        frame = Image.alpha_composite(frame, blk)
    return frame

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "still":
        for tt in sys.argv[2:]:
            render(float(tt)).save(f"build/ov_{float(tt):07.2f}.png")
        sys.exit()
    N = round(TOTAL * FPS)
    out = sys.stdout.buffer
    for i in range(N):
        out.write(render(i / FPS).tobytes())
