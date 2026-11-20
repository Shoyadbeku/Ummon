"""Overlay builders. Each returns an Overlay that can render itself into a frame at local time t."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from gfx import *


class Overlay:
    """Pre-rendered RGBA image + animation envelope."""
    def __init__(self, img, x, y, t0, t1, anim="fade", dur_in=0.35, dur_out=0.3, slide=0):
        self.img = np.asarray(img.convert("RGBA")) if isinstance(img, Image.Image) else img
        self.x, self.y, self.t0, self.t1 = x, y, t0, t1
        self.anim, self.di, self.do, self.slide = anim, dur_in, dur_out, slide
        self._wipe_cache = {}

    def draw(self, frame, t):
        if t < self.t0 or t > self.t1:
            return
        a_in = ease_out((t - self.t0) / self.di) if self.di > 0 else 1
        a_out = ease_out((self.t1 - t) / self.do) if self.do > 0 else 1
        a = min(a_in, a_out)
        x, y = self.x, self.y
        img = self.img
        if self.anim == "slide":
            x = self.x - (1 - a) * self.slide
        elif self.anim == "rise":
            y = self.y + (1 - a) * self.slide
        elif self.anim == "wipe":
            w = img.shape[1]
            vis = int(w * a)
            if vis <= 0:
                return
            img = img[:, :vis]
            a = 1 if a_in < 1 else a_out
        elif self.anim == "pop":
            s = 0.85 + 0.15 * ease_out_back(min(1, (t - self.t0) / max(0.01, self.di)))
            if abs(s - 1) > 0.004:
                key = round(s, 3)
                h0, w0 = self.img.shape[:2]
                im = Image.fromarray(self.img).resize((max(1, int(w0 * s)), max(1, int(h0 * s))), Image.BILINEAR)
                img = np.asarray(im)
                x = self.x + (w0 - img.shape[1]) / 2
                y = self.y + (h0 - img.shape[0]) / 2
        composite(frame, img, x, y, a)


def credit(ctx, text, t0=0.0, t1=999):
    """Small source credit, bottom-left, e.g. 'VIDEO: U.S. Central Command · Public domain'."""
    s = ctx.s
    f1 = font("semi", s(40))
    pad_x, pad_y = s(22), s(12)
    tw = f1.getlength(text)
    img = rgba_layer(tw + pad_x * 2 + s(10), s(40) + pad_y * 2 + s(6))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, img.size[0] - 1, img.size[1] - 1], radius=s(8), fill=(0, 0, 0, 150))
    d.rectangle([0, 0, s(6), img.size[1] - 1], fill=RED + (255,))
    d.text((pad_x + s(8), pad_y + s(2)), text, font=f1, fill=(255, 255, 255, 235))
    return Overlay(img, s(150), ctx.H - s(150) - img.size[1], t0, t1, "fade", 0.4, 0.3)


def lower_third(ctx, name, title, t0, t1, tag=None):
    s = ctx.s
    fn = font("xbold", s(84))
    ft = font("med", s(52))
    fg = font("bold", s(40))
    w = max(fn.getlength(name), ft.getlength(title)) + s(120)
    h = s(250)
    img = rgba_layer(w + s(20), h + s(80))
    d = ImageDraw.Draw(img)
    y0 = s(70) if tag else 0
    if tag:
        tw = fg.getlength(tag) + s(48)
        d.rectangle([0, 0, tw, s(64)], fill=RED + (255,))
        draw_text(d, (s(24), s(10)), tag, fg, WHITE, tracking=s(3))
    d.rectangle([0, y0, w, y0 + s(140)], fill=(255, 255, 255, 250))
    d.rectangle([0, y0, s(16), y0 + s(140)], fill=RED + (255,))
    d.text((s(52), y0 + s(22)), name, font=fn, fill=NAVY)
    d.rectangle([0, y0 + s(140), w * 0.92, y0 + s(222)], fill=NAVY + (235,))
    d.text((s(52), y0 + s(152)), title, font=ft, fill=OFF)
    img = img.crop((0, 0, int(w) + s(20), y0 + s(225)))
    return Overlay(img, s(190), ctx.H - s(330) - img.size[1], t0, t1, "wipe", 0.45, 0.35)


def bug(ctx, t0=0, t1=9999):
    """Top-left programme bug (own branding, no broadcaster marks)."""
    s = ctx.s
    f1 = font("black", s(46)); f2 = font("semi", s(40))
    a, b = "TAHLIL", "ERON • KO‘RFAZ • DUNYO"
    wa = f1.getlength(a) + s(4) * (len(a) - 1) + s(50)
    wb = f2.getlength(b) + s(50)
    img = rgba_layer(wa + wb, s(76))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, wa, s(76)], fill=RED + (240,))
    draw_text(d, (s(25), s(13)), a, f1, WHITE, tracking=s(4))
    d.rectangle([wa, 0, wa + wb, s(76)], fill=(8, 14, 28, 200))
    d.text((wa + s(25), s(17)), b, font=f2, fill=(235, 240, 248))
    return Overlay(img, s(150), s(120), t0, t1, "fade", 0.6, 0.6)


def kinetic(ctx, lines, t0, t1, x=None, y=None, size=220, kind="black", color=WHITE, accent=None,
            align="center", anim="rise", box=None, shadow=True, tracking=0, sub=None, sub_size=70):
    """Big kinetic headline text. lines: list[str]. accent: index of line in GOLD/RED box."""
    s = ctx.s
    f = font(kind, s(size))
    fs = font("semi", s(sub_size))
    lh = int(s(size) * 1.08)
    widths = [f.getlength(l) + max(0, len(l) - 1) * s(tracking) for l in lines]
    W = int(max(widths + ([fs.getlength(sub)] if sub else [0]))) + s(80)
    H = lh * len(lines) + (int(s(sub_size) * 1.6) if sub else 0) + s(40)
    img = rgba_layer(W, H)
    d = ImageDraw.Draw(img)
    if box is None: box = (align == "left")
    if box:
        d.rectangle([0, 0, W, H], fill=(6, 12, 26, 175))
        d.rectangle([0, 0, s(12), H], fill=RED + (255,))
    for i, l in enumerate(lines):
        lw = widths[i]
        lx = (W - lw) / 2 if align == "center" else s(40)
        ly = s(20) + i * lh
        col = color
        if accent is not None and i == accent:
            pad = s(26)
            bb = f.getbbox(l)
            d.rectangle([lx - pad, ly + bb[1] - pad * 0.6, lx + lw + pad, ly + bb[3] + pad * 0.6], fill=RED + (255,))
        draw_text(d, (lx, ly), l, f, col, tracking=s(tracking))
    if sub:
        sw = fs.getlength(sub)
        sx = (W - sw) / 2 if align == "center" else s(40)
        d.text((sx, s(20) + lh * len(lines) + s(18)), sub, font=fs, fill=(235, 238, 245))
    if shadow:
        img, pad = shadowed(img, s(18), 170)
    else:
        pad = 0
    if x is None:
        x = (ctx.W - img.size[0]) / 2
    else:
        x = x - pad
    if y is None:
        y = (ctx.H - img.size[1]) / 2
    else:
        y = y - pad
    return Overlay(img, x, y, t0, t1, anim, 0.4, 0.3, slide=s(60))


def quote_card(ctx, quote, who, t0, t1, x=None, y=None, maxw=2300, size=96):
    s = ctx.s
    fq = font("bold", s(size)); fw = font("semi", s(54)); fm = font("black", s(260))
    lines = wrap(quote, fq, s(maxw))
    lh = int(s(size) * 1.25)
    W = s(maxw) + s(200)
    H = lh * len(lines) + s(240)
    img = rgba_layer(W, H)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H], fill=(8, 14, 28, 215))
    d.rectangle([0, 0, s(14), H], fill=RED + (255,))
    d.text((s(60), s(-40)), "“", font=fm, fill=RED + (255,))
    for i, l in enumerate(lines):
        d.text((s(120), s(90) + i * lh), l, font=fq, fill=WHITE)
    d.text((s(120), s(90) + len(lines) * lh + s(30)), "— " + who, font=fw, fill=GOLD)
    if x is None: x = (ctx.W - W) / 2
    if y is None: y = (ctx.H - H) / 2
    return Overlay(img, x, y, t0, t1, "rise", 0.45, 0.35, slide=s(50))


def headline_card(ctx, source, text, t0, t1, x, y, w=2600):
    """Newspaper-style card: source name + paraphrased headline (no logos)."""
    s = ctx.s
    fs = font("black", s(54)); ft = font("bold", s(78))
    lines = wrap(text, ft, s(w) - s(120))
    lh = int(s(78) * 1.25)
    H = s(150) + lh * len(lines) + s(40)
    img = rgba_layer(s(w), H)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, s(w) - 1, H - 1], radius=s(14), fill=(250, 250, 248, 245))
    draw_text(d, (s(60), s(46)), source.upper(), fs, RED, tracking=s(3))
    d.line([s(60), s(122), s(w) - s(60), s(122)], fill=(200, 200, 200), width=s(4))
    for i, l in enumerate(lines):
        d.text((s(60), s(150) + i * lh), l, font=ft, fill=NAVY)
    img, pad = shadowed(img, s(24), 150, (0, s(10)))
    return Overlay(img, x - pad, y - pad, t0, t1, "rise", 0.45, 0.35, slide=s(80))


def stamp(ctx, text, t0, t1, color=RED, size=170, x=None, y=None, angle=-6):
    s = ctx.s
    f = font("black", s(size))
    tw = f.getlength(text)
    W, H = int(tw + s(140)), int(s(size) * 1.6)
    img = rgba_layer(W, H)
    d = ImageDraw.Draw(img)
    d.rectangle([s(10), s(10), W - s(10), H - s(10)], outline=color + (255,), width=s(16))
    d.text((s(70), (H - s(size)) / 2 - s(size) * 0.12), text, font=f, fill=color + (255,))
    img = img.rotate(angle, expand=True, resample=Image.BICUBIC)
    if x is None: x = (ctx.W - img.size[0]) / 2
    if y is None: y = (ctx.H - img.size[1]) / 2
    return Overlay(img, x, y, t0, t1, "pop", 0.35, 0.3)


def section_bumper(ctx, num, title, t0, t1):
    """Numbered section header, left aligned, slides in."""
    s = ctx.s
    fn = font("black", s(200)); ft = font("black", s(150))
    wn = fn.getlength(num) + s(100)
    wt = ft.getlength(title) + s(120)
    H = s(260)
    img = rgba_layer(wn + wt, H)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, wn, H], fill=RED + (255,))
    d.text((s(50), s(20)), num, font=fn, fill=WHITE)
    d.rectangle([wn, s(30), wn + wt, H - s(30)], fill=(255, 255, 255, 250))
    d.text((wn + s(60), s(52)), title, font=ft, fill=NAVY)
    img, pad = shadowed(img, s(20), 160)
    return Overlay(img, s(190) - pad, ctx.H * 0.40 - pad, t0, t1, "wipe", 0.5, 0.35)


def info_box(ctx, title, items, t0, t1, x, y, w=1500, size=66, stagger=0.45):
    """Box with title and bullet items appearing one by one. Returns list of overlays."""
    s = ctx.s
    ft = font("black", s(size + 6)); fi = font("semi", s(size))
    ovs = []
    head = rgba_layer(s(w), s(size * 1.9))
    d = ImageDraw.Draw(head)
    d.rectangle([0, 0, s(w), s(size * 1.9)], fill=RED + (250,))
    draw_text(d, (s(50), s(size * 0.42)), title.upper(), ft, WHITE, tracking=s(2))
    ovs.append(Overlay(head, x, y, t0, t1, "wipe", 0.4, 0.3))
    yy = y + s(size * 1.9)
    for i, it in enumerate(items):
        lines = wrap(it, fi, s(w) - s(170))
        hh = int(s(size) * 1.3 * len(lines) + s(size * 0.9))
        row = rgba_layer(s(w), hh)
        d = ImageDraw.Draw(row)
        d.rectangle([0, 0, s(w), hh], fill=(8, 14, 28, 225))
        d.ellipse([s(50), s(size * 0.62), s(50) + s(size * 0.42), s(size * 0.62) + s(size * 0.42)], fill=GOLD)
        for j, l in enumerate(lines):
            d.text((s(130), s(size * 0.42) + j * int(s(size) * 1.3)), l, font=fi, fill=WHITE)
        ovs.append(Overlay(row, x, yy, t0 + 0.3 + i * stagger, t1, "slide", 0.35, 0.3, slide=s(60)))
        yy += hh
    return ovs
