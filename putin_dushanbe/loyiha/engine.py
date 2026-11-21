"""News-documentary render engine: sources, transitions, overlays, maps.
Frames are composed with PIL / pycairo and piped into ffmpeg.
"""
import os, math, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cairo

W, H, FPS = 1920, 1080, 25
ROOT = os.environ.get('VROOT', '/tmp/claude-0/-home-user-Ummon/b5bf3b47-88eb-5ba2-839d-fed5a6ab73f0/scratchpad')
FD = '/usr/share/fonts/opentype/inter/'

RED = (214, 32, 45); NAVY = (10, 20, 32); WHITE = (255, 255, 255); GREY = (170, 182, 196)
AMBER = (242, 169, 0); BLUE = (40, 140, 230); TEAL = (0, 170, 160)


@functools.lru_cache(None)
def font(weight, size):
    return ImageFont.truetype(f'{FD}Inter-{weight}.otf', size)


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def eo(x):  # ease out cubic
    x = clamp(x); return 1 - (1 - x) ** 3


def eio(x):
    x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def fade_alpha(t, s, e, fin=.3, fout=.3):
    return clamp((t - s) / fin) * clamp((e - t) / fout) if fin and fout else 1.0


# ----------------------------------------------------------------- sources
class ImgSrc:
    def __init__(self, path, z0=1.03, z1=1.13, fx=.5, fy=.5, dx=0.0, dy=0.0):
        self.path, self.z0, self.z1, self.fx, self.fy, self.dx, self.dy = path, z0, z1, fx, fy, dx, dy
        self.img = None
        self.s = self.e = 0

    def bind(self, s, e):
        self.s, self.e = s, e; return self

    def frame(self, t):
        if self.img is None:
            self.img = Image.open(self.path).convert('RGB')
        iw, ih = self.img.size
        p = eio((t - self.s) / max(.01, self.e - self.s + .4))
        z = self.z0 + (self.z1 - self.z0) * p
        sc = max(W / iw, H / ih) * z
        vw, vh = W / sc, H / sc
        cx = self.fx * iw + self.dx * iw * (p - .5)
        cy = self.fy * ih + self.dy * ih * (p - .5)
        x0 = min(max(cx - vw / 2, 0), iw - vw); y0 = min(max(cy - vh / 2, 0), ih - vh)
        k = 1 / sc
        return self.img.transform((W, H), Image.AFFINE, (k, 0, x0, 0, k, y0), resample=Image.BILINEAR)


class VidSrc:
    def __init__(self, path, offset=0.0, speed=1.0, zoom=1.0):
        self.path, self.offset, self.speed, self.zoom = path, offset, speed, zoom
        self.proc = None; self.t0 = None; self.idx = -1; self.last = None
        self.s = self.e = 0

    def bind(self, s, e):
        self.s, self.e = s, e; return self

    def _start(self, t):
        self.t0 = t
        src_t = self.offset + (t - self.s) * self.speed
        vf = f'setpts=PTS/{self.speed},fps={FPS},' if self.speed != 1 else f'fps={FPS},'
        zw, zh = int(W * self.zoom), int(H * self.zoom)
        vf += f'scale={zw}:{zh}:force_original_aspect_ratio=increase,crop={W}:{H}'
        cmd = ['ffmpeg', '-nostdin', '-loglevel', 'error', '-ss', f'{max(0, src_t):.3f}', '-i', self.path,
               '-an', '-vf', vf, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 3 * 2)
        self.idx = -1

    def frame(self, t):
        if self.proc is None:
            self._start(t)
        target = int(round((t - self.t0) * FPS))
        while self.idx < target:
            buf = self.proc.stdout.read(W * H * 3)
            if len(buf) < W * H * 3:
                break
            self.last = buf; self.idx += 1
        if self.last is None:
            return Image.new('RGB', (W, H), NAVY)
        return Image.frombuffer('RGB', (W, H), self.last, 'raw', 'RGB', 0, 1)


@functools.lru_cache(None)
def _grad_bg():
    y = np.linspace(0, 1, H)[:, None]; x = np.linspace(0, 1, W)[None, :]
    r = np.sqrt((x - .5) ** 2 * 1.6 + (y - .45) ** 2)
    base = np.array([16, 28, 44])[None, None, :] * (1 - .55 * r[..., None]) + np.array([4, 8, 14]) * r[..., None]
    rng = np.random.default_rng(3)
    base += rng.normal(0, 2.2, (H, W, 1))
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


class CardSrc:
    """Dark studio background with slow moving light sweep and grid."""
    def __init__(self, accent=RED):
        self.accent = accent; self.s = self.e = 0

    def bind(self, s, e):
        self.s, self.e = s, e; return self

    def frame(self, t):
        im = _grad_bg().copy()
        d = ImageDraw.Draw(im, 'RGBA')
        off = (t * 18) % 80
        for gx in range(-80, W + 80, 80):
            d.line([(gx + off, 0), (gx + off, H)], fill=(255, 255, 255, 9))
        for gy in range(0, H, 80):
            d.line([(0, gy), (W, gy)], fill=(255, 255, 255, 9))
        sx = (t * 260) % (W + 1200) - 600
        d.polygon([(sx, 0), (sx + 220, 0), (sx - 180, H), (sx - 400, H)], fill=(255, 255, 255, 7))
        d.rectangle([0, H - 10, W, H], fill=self.accent + (255,))
        return im


class SplitSrc:
    def __init__(self, a, b, la=None, lb=None):
        self.a, self.b, self.la, self.lb = a, b, la, lb; self.s = self.e = 0

    def bind(self, s, e):
        self.s, self.e = s, e; self.a.bind(s, e); self.b.bind(s, e); return self

    def frame(self, t):
        p = eo((t - self.s) / .6)
        A = self.a.frame(t).crop((W // 4, 0, W // 4 + W // 2, H))
        B = self.b.frame(t).crop((W // 4, 0, W // 4 + W // 2, H))
        im = Image.new('RGB', (W, H), NAVY)
        im.paste(A, (int(-W // 2 * (1 - p)), 0)); im.paste(B, (W // 2 + int(W // 2 * (1 - p)), 0))
        d = ImageDraw.Draw(im, 'RGBA')
        d.rectangle([W // 2 - 4, 0, W // 2 + 4, H], fill=WHITE + (255,))
        for lab, x0, col in ((self.la, 0, RED), (self.lb, W // 2, BLUE)):
            if lab:
                f = font('Bold', 40); tw = d.textlength(lab, font=f)
                x = x0 + (W // 2 - tw) / 2
                d.rectangle([x - 26, 92, x + tw + 26, 160], fill=col + (235,))
                d.text((x, 100), lab, font=f, fill=WHITE)
        return im


# ----------------------------------------------------------------- overlays
class Ov:
    def __init__(self, s, e):
        self.s, self.e = s, e

    def active(self, t):
        return self.s <= t < self.e


def text_img(txt, f, fill=WHITE, shadow=True, spacing=0):
    bb = f.getbbox(txt)
    w = int(bb[2] + 12 + spacing * len(txt)); h = int(bb[3] + 14)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if spacing:
        x = 4
        for ch in txt:
            if shadow: d.text((x + 2, 5), ch, font=f, fill=(0, 0, 0, 160))
            d.text((x, 3), ch, font=f, fill=fill); x += d.textlength(ch, font=f) + spacing
    else:
        if shadow: d.text((6, 5), txt, font=f, fill=(0, 0, 0, 160))
        d.text((4, 3), txt, font=f, fill=fill)
    return im


def paste_alpha(canvas, im, xy, a):
    if a <= 0: return
    if a < 1:
        im = im.copy(); al = im.getchannel('A').point(lambda v: int(v * a)); im.putalpha(al)
    x, y = int(xy[0]), int(xy[1])
    # clip to canvas
    if x >= W or y >= H or x + im.width <= 0 or y + im.height <= 0: return
    cx0, cy0 = max(0, -x), max(0, -y)
    im = im.crop((cx0, cy0, min(im.width, W - x), min(im.height, H - y)))
    canvas.alpha_composite(im, (x + cx0, y + cy0))


def wrap(txt, f, maxw, d=None):
    d = d or ImageDraw.Draw(Image.new('L', (1, 1)))
    words, lines, cur = txt.split(), [], ''
    for w_ in words:
        test = (cur + ' ' + w_).strip()
        if d.textlength(test, font=f) <= maxw: cur = test
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines


class Dim(Ov):
    def __init__(self, s, e, a=.5):
        super().__init__(s, e); self.a = a

    def draw(self, c, t):
        a = self.a * fade_alpha(t, self.s, self.e, .35, .35)
        c.alpha_composite(Image.new('RGBA', (W, H), (5, 10, 18, int(255 * a))))


class Vignette(Ov):
    def __init__(self, s, e):
        super().__init__(s, e)
        y = np.linspace(-1, 1, H)[:, None]; x = np.linspace(-1, 1, W)[None, :]
        r = np.clip((np.sqrt(x ** 2 * .9 + y ** 2) - .55) / .9, 0, 1) ** 1.6
        self.im = Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8), (r * 150).astype(np.uint8)]), 'RGBA')

    def draw(self, c, t):
        c.alpha_composite(self.im)


class Credit(Ov):
    def __init__(self, s, e, text):
        super().__init__(s, e); self.im = text_img(text, font('SemiBold', 22), (255, 255, 255, 225), spacing=1)

    def draw(self, c, t):
        a = fade_alpha(t, self.s, self.e, .25, .2)
        paste_alpha(c, self.im, (W - self.im.width - 52, H - 62), a)


class LocTag(Ov):
    def __init__(self, s, e, text):
        super().__init__(s, e); self.text = text

    def draw(self, c, t):
        a = fade_alpha(t, self.s, self.e, .3, .3)
        p = eo((t - self.s) / .45)
        f = font('Bold', 30)
        d = ImageDraw.Draw(c, 'RGBA')
        tw = d.textlength(self.text, font=f)
        x, y = 70 - 40 * (1 - p), 64
        d.rectangle([x, y, x + tw + 74, y + 54], fill=(8, 14, 22, int(200 * a)))
        d.rectangle([x, y, x + 8, y + 54], fill=RED + (int(255 * a),))
        pulse = .5 + .5 * math.sin(t * 6)
        d.ellipse([x + 26, y + 20, x + 40, y + 34], fill=RED + (int(255 * a * (.5 + .5 * pulse)),))
        d.text((x + 54, y + 9), self.text, font=f, fill=(255, 255, 255, int(255 * a)))


class Chapter(Ov):
    def __init__(self, s, e, num, text):
        super().__init__(s, e); self.num, self.text = num, text

    def draw(self, c, t):
        a = fade_alpha(t, self.s, self.e, .5, .5)
        d = ImageDraw.Draw(c, 'RGBA')
        f1, f2 = font('Black', 24), font('SemiBold', 24)
        tw = d.textlength(self.text, font=f2)
        x1 = W - 64; x0 = x1 - tw - 80; y = 66
        d.rectangle([x0, y, x0 + 48, y + 44], fill=RED + (int(240 * a),))
        d.text((x0 + 14, y + 7), self.num, font=f1, fill=(255, 255, 255, int(255 * a)))
        d.rectangle([x0 + 48, y, x1, y + 44], fill=(8, 14, 22, int(190 * a)))
        d.text((x0 + 64, y + 8), self.text, font=f2, fill=(255, 255, 255, int(255 * a)))


class LowerThird(Ov):
    def __init__(self, s, e, title, sub=None, tag=None):
        super().__init__(s, e); self.title, self.sub, self.tag = title, sub, tag

    def draw(self, c, t):
        a = fade_alpha(t, self.s, self.e, .01, .3)
        p = eo((t - self.s) / .55); p2 = eo((t - self.s - .2) / .55)
        d = ImageDraw.Draw(c, 'RGBA')
        f1, f2, f3 = font('Bold', 44), font('Medium', 30), font('Black', 26)
        x, y = 96, 812
        tw = d.textlength(self.title, font=f1)
        bw = (tw + 60) * p
        if self.tag:
            gw = d.textlength(self.tag, font=f3) + 36
            d.rectangle([x, y - 46, x + gw * p, y], fill=RED + (int(255 * a),))
            if p > .6: d.text((x + 18, y - 40), self.tag, font=f3, fill=(255, 255, 255, int(255 * a)))
        d.rectangle([x, y, x + bw, y + 70], fill=(255, 255, 255, int(245 * a)))
        d.rectangle([x, y, x + 10, y + 70], fill=RED + (int(255 * a),))
        if p > .5:
            d.text((x + 34, y + 9), self.title, font=f1, fill=(12, 18, 28, int(255 * a * clamp((p - .5) * 2))))
        if self.sub:
            sw = d.textlength(self.sub, font=f2)
            d.rectangle([x, y + 70, x + (sw + 60) * p2, y + 122], fill=(10, 18, 30, int(225 * a)))
            if p2 > .5:
                d.text((x + 34, y + 78), self.sub, font=f2, fill=(255, 255, 255, int(255 * a * clamp((p2 - .5) * 2))))


class Kinetic(Ov):
    """Big centered headline, words pop in sequentially."""
    def __init__(self, s, e, lines, size=124, weight='Black', color=WHITE, accent_word=None, sub=None, dim=.55,
                 y=None, stagger=.09, bar=True):
        super().__init__(s, e)
        self.lines, self.size, self.weight, self.color, self.accent_word, self.sub, self.dim, self.y = \
            lines, size, weight, color, accent_word, sub, dim, y
        self.stagger, self.bar = stagger, bar

    def draw(self, c, t):
        a = fade_alpha(t, self.s, self.e, .15, .3)
        if self.dim:
            c.alpha_composite(Image.new('RGBA', (W, H), (4, 8, 14, int(255 * self.dim * a))))
        f = font(self.weight, self.size)
        d = ImageDraw.Draw(c, 'RGBA')
        lh = self.size * 1.15
        total = lh * len(self.lines) + (70 if self.sub else 0)
        y = (self.y if self.y is not None else (H - total) / 2)
        k = 0
        for ln in self.lines:
            words = ln.split(' ')
            widths = [d.textlength(w_, font=f) for w_ in words]
            sp = d.textlength(' ', font=f)
            x = (W - (sum(widths) + sp * (len(words) - 1))) / 2
            for w_, ww in zip(words, widths):
                p = eo((t - self.s - k * self.stagger) / .35)
                col = RED if (self.accent_word and w_.strip('?.,!').upper() == self.accent_word.upper()) else self.color
                if p > 0:
                    im = text_img(w_, f, col)
                    sc = .7 + .3 * p
                    if sc < .999:
                        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BILINEAR)
                    paste_alpha(c, im, (x + (ww - im.width) / 2, y + (lh - im.height) / 2 + 20 * (1 - p)), a * p)
                x += ww + sp; k += 1
            y += lh
        if self.bar:
            p = eo((t - self.s - .2) / .5)
            bw = 180 * p
            d.rectangle([W / 2 - bw / 2, y + 26, W / 2 + bw / 2, y + 34], fill=RED + (int(255 * a),))
        if self.sub:
            p = eo((t - self.s - .35) / .4)
            fs = font('Medium', 40)
            sw = d.textlength(self.sub, font=fs)
            d.text(((W - sw) / 2, y + 56 + 10 * (1 - p)), self.sub, font=fs, fill=(220, 228, 238, int(255 * a * p)))


class Quote(Ov):
    def __init__(self, s, e, text, author, role=None, side='left', size=48):
        super().__init__(s, e); self.text, self.author, self.role, self.side, self.size = text, author, role, side, size

    def draw(self, c, t):
        a = fade_alpha(t, self.s, self.e, .01, .35)
        p = eo((t - self.s) / .6)
        pw = 860
        x0 = (-pw * (1 - p)) if self.side == 'left' else (W - pw * p)
        panel = Image.new('RGBA', (pw, H), (6, 12, 20, int(222 * a)))
        d = ImageDraw.Draw(panel, 'RGBA')
        d.rectangle([0 if self.side == 'left' else pw - 10, 0, 10 if self.side == 'left' else pw, H],
                    fill=RED + (int(255 * a),))
        fq = font('Black', 200); d.text((70, 130), '“', font=fq, fill=RED + (int(255 * a),))
        f = font('SemiBold', self.size)
        lines = wrap(self.text, f, pw - 170, d)
        y = 360
        for i, ln in enumerate(lines):
            pl = eo((t - self.s - .25 - i * .12) / .4)
            d.text((80, y + 12 * (1 - pl)), ln, font=f, fill=(255, 255, 255, int(255 * a * pl)))
            y += self.size * 1.3
        pa = eo((t - self.s - .6) / .4)
        d.rectangle([80, y + 30, 80 + 90 * pa, y + 36], fill=RED + (int(255 * a),))
        d.text((80, y + 56), self.author, font=font('Bold', 36), fill=(255, 255, 255, int(255 * a * pa)))
        if self.role:
            d.text((80, y + 102), self.role, font=font('Medium', 28), fill=GREY + (int(255 * a * pa),))
        c.alpha_composite(panel, (int(x0), 0)) if 0 <= int(x0) <= W - pw else paste_alpha(c, panel, (x0, 0), 1)


class FactBox(Ov):
    """Compact box with headline + lines, placed left or right."""
    def __init__(self, s, e, head, lines=(), pos='left', y=300, width=760, accent=RED, size=40):
        super().__init__(s, e); self.head, self.lines, self.pos, self.y, self.width, self.accent, self.size = \
            head, list(lines), pos, y, width, accent, size

    def draw(self, c, t):
        a = fade_alpha(t, self.s, self.e, .01, .3)
        p = eo((t - self.s) / .5)
        d0 = ImageDraw.Draw(c)
        fh, fl = font('Black', 54), font('Medium', self.size)
        lines = []
        for ln in self.lines: lines += wrap(ln, fl, self.width - 80, d0)
        hlines = wrap(self.head, fh, self.width - 80, d0)
        h = 50 + len(hlines) * 64 + 20 + len(lines) * self.size * 1.35 + 40
        x = 96 if self.pos == 'left' else W - 96 - self.width
        x += (-60 if self.pos == 'left' else 60) * (1 - p)
        box = Image.new('RGBA', (self.width, int(h)), (6, 12, 20, 225))
        d = ImageDraw.Draw(box)
        d.rectangle([0, 0, 10, h], fill=self.accent + (255,))
        y = 40
        for hl in hlines:
            d.text((44, y), hl, font=fh, fill=WHITE); y += 64
        y += 20
        for ln in lines:
            d.text((44, y), ln, font=fl, fill=(225, 232, 240)); y += self.size * 1.35
        paste_alpha(c, box, (x, self.y), a * p)


class Counter(Ov):
    def __init__(self, s, e, v0, v1, fmt, label, dur=1.6, pos=(W / 2, 430), size=190, color=WHITE, dim=0):
        super().__init__(s, e); self.v0, self.v1, self.fmt, self.label, self.dur, self.pos, self.size, self.color, self.dim = \
            v0, v1, fmt, label, dur, pos, size, color, dim

    def draw(self, c, t):
        a = fade_alpha(t, self.s, self.e, .2, .3)
        if self.dim: c.alpha_composite(Image.new('RGBA', (W, H), (4, 8, 14, int(255 * self.dim * a))))
        v = self.v0 + (self.v1 - self.v0) * eo((t - self.s) / self.dur)
        txt = self.fmt(v)
        im = text_img(txt, font('Black', self.size), self.color)
        paste_alpha(c, im, (self.pos[0] - im.width / 2, self.pos[1] - im.height / 2), a)
        if self.label:
            fl = font('Bold', 44)
            li = text_img(self.label, fl, (230, 236, 244), spacing=2)
            p = eo((t - self.s - .3) / .4)
            paste_alpha(c, li, (self.pos[0] - li.width / 2, self.pos[1] + self.size * .62), a * p)


class Bars(Ov):
    def __init__(self, s, e, title, items, source):
        super().__init__(s, e); self.title, self.items, self.source = title, items, source

    def draw(self, c, t):
        a = fade_alpha(t, self.s, self.e, .3, .3)
        c.alpha_composite(Image.new('RGBA', (W, H), (6, 12, 20, int(215 * a))))
        d = ImageDraw.Draw(c, 'RGBA')
        ft = font('Black', 60)
        d.text((180, 150), self.title, font=ft, fill=(255, 255, 255, int(255 * a)))
        d.rectangle([180, 236, 180 + 160 * eo((t - self.s) / .5), 244], fill=RED + (int(255 * a),))
        base_y = 860; maxh = 470; vmax = max(v for _, v, _, _ in self.items) * 1.1
        n = len(self.items); bw = 300; gap = 260
        x = (W - (n * bw + (n - 1) * gap)) / 2
        for i, (lab, v, vt, st) in enumerate(self.items):
            p = eo((t - self.s - st) / 1.0)
            h = maxh * v / vmax * p
            col = RED if i == n - 1 else (90, 110, 135)
            d.rectangle([x, base_y - h, x + bw, base_y], fill=col + (int(255 * a),))
            if p > .05:
                fv = font('Black', 84); tw = d.textlength(vt, font=fv)
                d.text((x + (bw - tw) / 2, base_y - h - 108), vt, font=fv, fill=(255, 255, 255, int(255 * a * p)))
            fl = font('SemiBold', 34)
            for j, ll in enumerate(lab.split('\n')):
                tw = d.textlength(ll, font=fl)
                d.text((x + (bw - tw) / 2, base_y + 24 + j * 44), ll, font=fl, fill=(220, 228, 238, int(255 * a)))
            x += bw + gap
        d.line([(160, base_y), (W - 160, base_y)], fill=(255, 255, 255, int(120 * a)), width=2)
        d.text((180, 1000), self.source, font=font('Medium', 24), fill=GREY + (int(255 * a),))


class Timeline(Ov):
    def __init__(self, s, e, items, y=880):
        super().__init__(s, e); self.items, self.y = items, y

    def draw(self, c, t):
        a = fade_alpha(t, self.s, self.e, .4, .4)
        d = ImageDraw.Draw(c, 'RGBA')
        y = self.y
        d.rectangle([0, y - 120, W, y + 140], fill=(6, 12, 20, int(190 * a)))
        n = len(self.items); x0, x1 = 200, W - 200
        shown = [it for it in self.items if t >= it[0]]
        prog = 0
        if shown:
            k = len(shown) - 1
            prog = (k + eo((t - shown[-1][0]) / .6)) / max(1, n - 1) if n > 1 else 1
        d.line([(x0, y), (x1, y)], fill=(255, 255, 255, int(70 * a)), width=4)
        d.line([(x0, y), (x0 + (x1 - x0) * min(1, prog), y)], fill=RED + (int(255 * a),), width=6)
        for i, (ts, year, lab) in enumerate(self.items):
            x = x0 + (x1 - x0) * i / max(1, n - 1)
            p = eo((t - ts) / .4)
            r = 14 * p
            d.ellipse([x - 18, y - 18, x + 18, y + 18], fill=(30, 40, 52, int(255 * a)))
            if p > 0:
                d.ellipse([x - r, y - r, x + r, y + r], fill=RED + (int(255 * a),))
                fy, fl = font('Black', 46), font('Medium', 28)
                tw = d.textlength(year, font=fy)
                d.text((x - tw / 2, y - 92 + 10 * (1 - p)), year, font=fy, fill=(255, 255, 255, int(255 * a * p)))
                for j, ll in enumerate(lab.split('\n')):
                    lw = d.textlength(ll, font=fl)
                    d.text((x - lw / 2, y + 34 + j * 34), ll, font=fl, fill=(215, 224, 234, int(255 * a * p)))


class Compare(Ov):
    def __init__(self, s, e, left, right):
        super().__init__(s, e); self.left, self.right = left, right

    def draw(self, c, t):
        a = fade_alpha(t, self.s, self.e, .3, .3)
        c.alpha_composite(Image.new('RGBA', (W, H), (6, 12, 20, int(200 * a))))
        d = ImageDraw.Draw(c, 'RGBA')
        for k, (title, lines, col, st) in enumerate((self.left, self.right)):
            p = eo((t - self.s - st) / .6)
            x = 140 + k * (W // 2) ; y = 230
            pw = W // 2 - 240
            d.rectangle([x, y, x + pw, y + 640], fill=(14, 24, 36, int(235 * a * p)))
            d.rectangle([x, y, x + pw, y + 14], fill=col + (int(255 * a * p),))
            d.text((x + 48, y + 52), title, font=font('Black', 62), fill=(255, 255, 255, int(255 * a * p)))
            yy = y + 170
            for i, ln in enumerate(lines):
                pl = eo((t - self.s - st - .3 - i * .25) / .4)
                fl = font('SemiBold', 38)
                for j, wl in enumerate(wrap(ln, fl, pw - 130, d)):
                    if j == 0:
                        d.rectangle([x + 50, yy + 18, x + 66, yy + 34], fill=col + (int(255 * a * pl),))
                    d.text((x + 90, yy), wl, font=fl, fill=(235, 240, 246, int(255 * a * pl))); yy += 50
                yy += 34


class Flash(Ov):
    def __init__(self, s, dur=.22):
        super().__init__(s, s + dur); self.dur = dur

    def draw(self, c, t):
        a = 1 - (t - self.s) / self.dur
        c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(200 * clamp(a)))))


class EndCard(Ov):
    def __init__(self, s, e, lines, y=760):
        super().__init__(s, e); self.lines, self.y = lines, y

    def draw(self, c, t):
        a = fade_alpha(t, self.s, self.e, .5, .8)
        d = ImageDraw.Draw(c, 'RGBA')
        y = self.y
        for i, (txt, f, col) in enumerate(self.lines):
            p = eo((t - self.s - i * .15) / .5)
            tw = d.textlength(txt, font=f)
            d.text(((W - tw) / 2, y), txt, font=f, fill=col + (int(255 * a * p),)); y += f.size * 1.5


# ----------------------------------------------------------------- maps
GEO = os.path.join(ROOT, 'assets/geo')


def _simplify(pts, tol):
    out = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - out[-1][0]) + abs(p[1] - out[-1][1]) >= tol: out.append(p)
    if len(out) < 3: return pts
    return out


@functools.lru_cache(None)
def geodata():
    import shapefile
    from scipy.spatial import cKDTree
    box = (25, 5, 130, 62)
    r = shapefile.Reader(os.path.join(GEO, 'ne_10m_admin_0_countries.shp'))
    fl = [f[0] for f in r.fields[1:]]; ia = fl.index('ADM0_A3')
    countries = {}
    for rec, sh in zip(r.records(), r.shapes()):
        b = sh.bbox
        if b[2] < box[0] or b[0] > box[2] or b[3] < box[1] or b[1] > box[3]: continue
        pts = sh.points; parts = list(sh.parts) + [len(pts)]
        rings = []
        for i in range(len(parts) - 1):
            ring = pts[parts[i]:parts[i + 1]]
            if len(ring) < 4: continue
            rings.append(np.array(_simplify(ring, .012)))
        countries[rec[ia]] = rings
    r = shapefile.Reader(os.path.join(GEO, 'ne_10m_admin_1_states_provinces.shp'))
    fl = [f[0] for f in r.fields[1:]]
    admin = {}
    for rec, sh in zip(r.records(), r.shapes()):
        dct = dict(zip(fl, rec))
        if dct['adm0_a3'] in ('TJK',) and dct['name'] in ('Khatlon',):
            pts = sh.points; parts = list(sh.parts) + [len(pts)]
            admin[dct['name']] = [np.array(_simplify(pts[parts[i]:parts[i + 1]], .01)) for i in range(len(parts) - 1)]
    r = shapefile.Reader(os.path.join(GEO, 'ne_10m_rivers_lake_centerlines.shp'))
    fl = [f[0] for f in r.fields[1:]]; inn = fl.index('name')
    rivers = {}
    for rec, sh in zip(r.records(), r.shapes()):
        if rec[inn] in ('Panj', 'Amu Darya', 'Syr Darya', 'Vakhsh', 'Zarafshon'):
            pts = sh.points; parts = list(sh.parts) + [len(pts)]
            for i in range(len(parts) - 1):
                rivers.setdefault(rec[inn], []).append(np.array(pts[parts[i]:parts[i + 1]]))
    # shared borders
    def shared(a, b, tol=.03):
        A = max(countries[a], key=len); Bpts = np.vstack(countries[b])
        tree = cKDTree(Bpts); dist, _ = tree.query(A)
        m = dist < tol
        runs, cur = [], []
        for p, ok in zip(A, m):
            if ok: cur.append(p)
            elif cur: runs.append(cur); cur = []
        if cur: runs.append(cur)
        if len(runs) > 1 and m[0] and m[-1]:  # wrap-around
            runs[0] = runs[-1] + runs[0]; runs.pop()
        return np.array(max(runs, key=len))
    borders = {'TJK-AFG': shared('TJK', 'AFG'), 'UZB-AFG': shared('UZB', 'AFG')}
    return countries, admin, rivers, borders


def path_len(pts):
    return np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]


class MapSrc:
    """cam: list of (t, lon, lat, width_deg).  Elements are dicts with timing."""
    NAMES = {'TJK': 'TOJIKISTON', 'UZB': 'OʻZBEKISTON', 'AFG': 'AFGʻONISTON', 'KGZ': 'QIRGʻIZISTON',
             'KAZ': 'QOZOGʻISTON', 'TKM': 'TURKMANISTON', 'CHN': 'XITOY', 'RUS': 'ROSSIYA', 'PAK': 'POKISTON',
             'IRN': 'ERON', 'IND': 'HINDISTON', 'MNG': 'MOʻGʻULISTON'}
    LABEL_POS = {'TJK': (72.6, 38.75), 'UZB': (63.6, 41.6), 'AFG': (66.5, 34.6), 'KGZ': (74.8, 41.5), 'KAZ': (67, 47.5),
                 'TKM': (59.2, 39.2), 'CHN': (100, 33), 'RUS': (75, 57), 'PAK': (69.5, 29.5), 'IRN': (56, 32),
                 'IND': (79, 22), 'MNG': (103, 46.5)}

    def __init__(self, cam, phi0=38, hi=(), admin_hi=(), labels=None, cities=(), borders=(), rivers=(), arcs=(),
                 country_labels=('TJK', 'UZB', 'AFG', 'KGZ', 'KAZ', 'TKM', 'CHN', 'PAK', 'IRN'), label_t=0.3):
        self.cam, self.phi0, self.hi, self.admin_hi, self.cities = cam, phi0, hi, admin_hi, cities
        self.borders, self.rivers, self.arcs, self.country_labels, self.label_t = borders, rivers, arcs, country_labels, label_t
        self.labels = labels or []
        self.s = self.e = 0

    def bind(self, s, e):
        self.s, self.e = s, e; return self

    def camera(self, t):
        rt = t - self.s
        ks = self.cam
        if rt <= ks[0][0]: return ks[0][1:]
        for a, b in zip(ks, ks[1:]):
            if rt <= b[0]:
                p = eio((rt - a[0]) / (b[0] - a[0]))
                lw0, lw1 = math.log(a[3]), math.log(b[3])
                return (a[1] + (b[1] - a[1]) * p, a[2] + (b[2] - a[2]) * p, math.exp(lw0 + (lw1 - lw0) * p))
        return ks[-1][1:]

    def frame(self, t):
        countries, admin, rivers, borders = geodata()
        rt = t - self.s
        clon, clat, wd = self.camera(t)
        cphi = math.cos(math.radians(self.phi0))
        s = W / (wd * cphi)
        def P(lon, lat):
            return (W / 2 + (lon - clon) * cphi * s, H / 2 - (lat - clat) * s)
        def PA(arr):
            return np.c_[W / 2 + (arr[:, 0] - clon) * cphi * s, H / 2 - (arr[:, 1] - clat) * s]
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
        cr = cairo.Context(surf)
        g = cairo.RadialGradient(W / 2, H / 2, 100, W / 2, H / 2, W * .8)
        g.add_color_stop_rgb(0, 12 / 255, 30 / 255, 50 / 255); g.add_color_stop_rgb(1, 3 / 255, 9 / 255, 17 / 255)
        cr.set_source(g); cr.paint()
        # graticule
        cr.set_line_width(1); cr.set_source_rgba(1, 1, 1, .05)
        lon0 = int((clon - wd) // 5 * 5)
        for lo in range(lon0, int(clon + wd) + 5, 5):
            x, _ = P(lo, 0); cr.move_to(x, 0); cr.line_to(x, H)
        for la in range(-10, 80, 5):
            _, y = P(0, la); cr.move_to(0, y); cr.line_to(W, y)
        cr.stroke()
        vx0, vx1 = clon - wd * .7, clon + wd * .7
        def ring_path(ring):
            q = PA(ring)
            cr.move_to(*q[0])
            for x, y in q[1:]: cr.line_to(x, y)
            cr.close_path()
        for code, rings in countries.items():
            for ring in rings:
                if ring[:, 0].max() < vx0 or ring[:, 0].min() > vx1: continue
                ring_path(ring)
            cr.set_source_rgb(27 / 255, 41 / 255, 57 / 255); cr.fill_preserve()
            cr.set_source_rgba(110 / 255, 140 / 255, 170 / 255, .55); cr.set_line_width(1.3); cr.stroke()
        for code, col, t0, t1 in self.hi:
            al = clamp((rt - t0) / .6) * clamp((t1 - rt) / .5)
            if al <= 0: continue
            pul = .75 + .25 * math.sin(rt * 4)
            for ring in countries[code]: ring_path(ring)
            cr.set_source_rgba(col[0] / 255, col[1] / 255, col[2] / 255, .55 * al * pul); cr.fill_preserve()
            cr.set_source_rgba(col[0] / 255, col[1] / 255, col[2] / 255, .95 * al); cr.set_line_width(3); cr.stroke()
        for name, col, t0, t1 in self.admin_hi:
            al = clamp((rt - t0) / .6) * clamp((t1 - rt) / .5)
            if al <= 0: continue
            for ring in admin[name]: ring_path(ring)
            cr.set_source_rgba(col[0] / 255, col[1] / 255, col[2] / 255, .6 * al); cr.fill_preserve()
            cr.set_source_rgba(1, 1, 1, .9 * al); cr.set_line_width(2.5); cr.set_dash([8, 6]); cr.stroke(); cr.set_dash([])
        for name, t0 in self.rivers:
            al = clamp((rt - t0) / .6)
            if al <= 0: continue
            for line in rivers.get(name, []):
                q = PA(line); cr.move_to(*q[0])
                for x, y in q[1:]: cr.line_to(x, y)
            cr.set_source_rgba(70 / 255, 160 / 255, 240 / 255, .9 * al); cr.set_line_width(3.2); cr.stroke()
        for key, col, t0, dur in self.borders:
            p = eio((rt - t0) / dur)
            if p <= 0: continue
            pts = PA(borders[key]); L = path_len(pts); cut = L[-1] * p
            n = int(np.searchsorted(L, cut))
            sub = pts[:max(2, n)]
            for w_, a_ in ((16, .18), (9, .35), (4.5, 1)):
                cr.move_to(*sub[0])
                for x, y in sub[1:]: cr.line_to(x, y)
                cr.set_source_rgba(col[0] / 255, col[1] / 255, col[2] / 255, a_); cr.set_line_width(w_)
                cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke()
            if p < 1:
                x, y = sub[-1]; cr.new_path(); cr.arc(x, y, 9, 0, 2 * math.pi); cr.set_source_rgb(1, 1, 1); cr.fill()
        for (a_, b_, t0, dur, col) in self.arcs:
            p = eio((rt - t0) / dur)
            if p <= 0: continue
            (x0, y0), (x1, y1) = P(*a_), P(*b_)
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2 - math.hypot(x1 - x0, y1 - y0) * .28
            ts = np.linspace(0, p, 80)
            xs = (1 - ts) ** 2 * x0 + 2 * (1 - ts) * ts * mx + ts ** 2 * x1
            ys = (1 - ts) ** 2 * y0 + 2 * (1 - ts) * ts * my + ts ** 2 * y1
            cr.set_dash([14, 10])
            cr.move_to(xs[0], ys[0])
            for x, y in zip(xs[1:], ys[1:]): cr.line_to(x, y)
            cr.set_source_rgba(col[0] / 255, col[1] / 255, col[2] / 255, 1); cr.set_line_width(5); cr.stroke(); cr.set_dash([])
            # plane marker
            if p < 1:
                ang = math.atan2(ys[-1] - ys[-2], xs[-1] - xs[-2])
                cr.save(); cr.translate(xs[-1], ys[-1]); cr.rotate(ang)
                cr.move_to(18, 0); cr.line_to(-12, -11); cr.line_to(-6, 0); cr.line_to(-12, 11); cr.close_path()
                cr.set_source_rgb(1, 1, 1); cr.fill(); cr.restore()
        # country labels
        cr.select_font_face('Inter', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        for code in self.country_labels:
            lon, lat = self.LABEL_POS[code]
            x, y = P(lon, lat)
            if not (-200 < x < W + 200 and -100 < y < H + 100): continue
            al = clamp((rt - self.label_t) / .6)
            hi = any(h[0] == code and h[2] <= rt < h[3] for h in self.hi)
            size = 34 if hi else 24
            cr.set_font_size(size)
            txt = self.NAMES[code]
            ext = cr.text_extents(txt)
            cr.move_to(x - ext.width / 2 - 1, y + 2); cr.set_source_rgba(0, 0, 0, .6 * al); cr.show_text(txt)
            cr.move_to(x - ext.width / 2, y)
            cr.set_source_rgba(1, 1, 1, (.95 if hi else .55) * al); cr.show_text(txt)
        # cities
        for name, lon, lat, t0, kind in self.cities:
            al = clamp((rt - t0) / .4)
            if al <= 0: continue
            x, y = P(lon, lat)
            pp = (rt * 1.2) % 1
            cr.new_path()
            if kind in ('star', 'pulse'):
                cr.arc(x, y, 10 + 40 * pp, 0, 2 * math.pi); cr.set_source_rgba(1, .2, .25, (1 - pp) * .8 * al)
                cr.set_line_width(3); cr.stroke()
            cr.new_path(); cr.arc(x, y, 9 if kind != 'small' else 6, 0, 2 * math.pi)
            cr.set_source_rgba(1, 1, 1, al); cr.fill_preserve()
            cr.set_source_rgba(*(np.array(RED) / 255), al); cr.set_line_width(3.5); cr.stroke()
            cr.select_font_face('Inter', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(30 if kind != 'small' else 24)
            ext = cr.text_extents(name)
            bx, by = x + 18, y - 22
            cr.rectangle(bx - 8, by - 4, ext.width + 22, 42 if kind != 'small' else 36)
            cr.set_source_rgba(6 / 255, 12 / 255, 20 / 255, .82 * al); cr.fill()
            cr.move_to(bx + 3, by + (29 if kind != 'small' else 25)); cr.set_source_rgba(1, 1, 1, al); cr.show_text(name)
        for txt, lon, lat, t0, size, col in self.labels:
            al = clamp((rt - t0) / .5)
            if al <= 0: continue
            x, y = P(lon, lat)
            cr.select_font_face('Inter', cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(size)
            ext = cr.text_extents(txt)
            cr.move_to(x - ext.width / 2 + 2, y + 2); cr.set_source_rgba(0, 0, 0, .7 * al); cr.show_text(txt)
            cr.move_to(x - ext.width / 2, y); cr.set_source_rgba(col[0] / 255, col[1] / 255, col[2] / 255, al)
            cr.show_text(txt)
        surf.flush()
        buf = np.frombuffer(surf.get_data(), np.uint8).reshape(H, surf.get_stride() // 4, 4)[:, :W, :3][:, :, ::-1]
        return Image.fromarray(np.ascontiguousarray(buf))


# ----------------------------------------------------------------- compositor
class Timeline_:
    def __init__(self, shots, overlays, total):
        self.shots, self.overlays, self.total = shots, overlays, total
        for sh in shots: sh['src'].bind(sh['s'], sh['e'])

    def shot_at(self, t):
        for i, sh in enumerate(self.shots):
            if sh['s'] <= t < sh['e']: return i
        return len(self.shots) - 1

    def frame(self, t):
        i = self.shot_at(t); sh = self.shots[i]
        img = sh['src'].frame(t)
        tr = sh.get('tr', 'fade'); d = sh.get('trd', .4 if tr == 'fade' else .3)
        if i > 0 and t < sh['s'] + d and tr in ('fade', 'whip'):
            prev = self.shots[i - 1]['src'].frame(t)
            p = (t - sh['s']) / d
            if tr == 'fade':
                img = Image.blend(prev, img, eio(p))
            else:
                q = eio(p); off = int(W * q)
                comp = Image.new('RGB', (W, H)); comp.paste(prev, (-off, 0)); comp.paste(img, (W - off, 0))
                img = comp.filter(ImageFilter.BoxBlur(int(28 * math.sin(math.pi * p)))) if 0 < p < 1 else comp
        c = img.convert('RGBA')
        for ov in self.overlays:
            if ov.active(t): ov.draw(c, t)
        if i > 0 and tr == 'flash' and t < sh['s'] + .25:
            a = 1 - (t - sh['s']) / .25
            c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(230 * a))))
        return c.convert('RGB')


def render_range(tl, f0, f1, out):
    cmd = ['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p',
           '-g', '50', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(tl.frame(f / FPS).tobytes())
    p.stdin.close(); p.wait()
