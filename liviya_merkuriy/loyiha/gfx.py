# Graphics toolkit: fonts, palette, easing, overlay components, maps.
import math, json, os
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from shapely.geometry import shape, box
from shapely.ops import unary_union

W, H, FPS = 1920, 1080, 30
ROOT = os.path.dirname(os.path.abspath(__file__))
FD = '/usr/share/fonts/opentype/inter/'

# Palette (own identity: deep navy + amber, not any broadcaster's look)
NAVY = (9, 16, 30)
NAVY2 = (18, 30, 52)
PANEL = (12, 20, 36, 225)
AMBER = (255, 178, 36)
RED = (226, 64, 52)
BLUE = (70, 140, 230)
WHITE = (255, 255, 255)
GREY = (170, 182, 200)
OCEAN = (10, 22, 40)
LAND = (32, 44, 62)
LAND_HI = (44, 58, 80)
BORDER = (78, 96, 120)


@lru_cache(None)
def F(name, size):
    return ImageFont.truetype(FD + name + '.otf', size)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def fade(t, dur, fin=0.35, fout=0.35):
    """alpha 0..1 for an element visible from 0..dur"""
    if t < 0 or t > dur:
        return 0.0
    a = clamp(t / fin) if fin > 0 else 1
    b = clamp((dur - t) / fout) if fout > 0 else 1
    return min(ease(a), ease(b))


def text_w(font, s):
    return font.getlength(s)


def wrap(font, s, maxw):
    words, lines, cur = s.split(), [], ''
    for w in words:
        nxt = (cur + ' ' + w).strip()
        if text_w(font, nxt) <= maxw or not cur:
            cur = nxt
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def layer():
    return Image.new('RGBA', (W, H), (0, 0, 0, 0))


def with_alpha(c, a):
    if len(c) == 4:
        return (c[0], c[1], c[2], int(c[3] * a))
    return (c[0], c[1], c[2], int(255 * a))


def paste_alpha(base, over, a):
    if a <= 0:
        return
    if a < 1:
        r, g, b, al = over.split()
        al = al.point(lambda v: int(v * a))
        over = Image.merge('RGBA', (r, g, b, al))
    base.alpha_composite(over)


# ---------------------------------------------------------------- components
def credit(img, text, t, dur):
    """Source credit, bottom-right, small but legible."""
    a = fade(t, dur, 0.4, 0.3)
    if a <= 0 or not text:
        return
    f = F('Inter-SemiBold', 22)
    tw = text_w(f, text)
    L = layer()
    d = ImageDraw.Draw(L)
    x1, y1 = W - 48, H - 40
    x0, y0 = x1 - tw - 28, y1 - 38
    d.rounded_rectangle((x0, y0, x1, y1), 6, fill=(0, 0, 0, 165))
    d.text((x0 + 14, y0 + 7), text, font=f, fill=(235, 238, 245, 255))
    paste_alpha(img, L, a)


def loc_tag(img, text, t, dur):
    """Top-left dateline tag."""
    a = fade(t, dur, 0.4, 0.3)
    if a <= 0 or not text:
        return
    f = F('Inter-Bold', 26)
    L = layer()
    d = ImageDraw.Draw(L)
    tw = text_w(f, text)
    k = ease(t / 0.5)
    x0, y0 = 60, 54
    d.rectangle((x0, y0, x0 + 10, y0 + 44), fill=AMBER + (255,))
    w = (tw + 36) * k
    d.rectangle((x0 + 10, y0, x0 + 10 + w, y0 + 44), fill=(9, 16, 30, 215))
    if k > 0.6:
        d.text((x0 + 28, y0 + 7), text, font=f, fill=WHITE + (255,))
    paste_alpha(img, L, a)


def lower_third(img, title, sub, t, dur, y=840):
    a = fade(t, dur, 0.01, 0.35)
    if a <= 0:
        return
    ft = F('InterDisplay-ExtraBold', 54)
    fs = F('Inter-SemiBold', 30)
    tw = max(text_w(ft, title), text_w(fs, sub) if sub else 0)
    L = layer()
    d = ImageDraw.Draw(L)
    k1 = ease(t / 0.45)
    k2 = ease((t - 0.15) / 0.5)
    x0 = 90
    bw = (tw + 70) * k2
    d.rectangle((x0, y, x0 + 12, y + (128 if sub else 84) * k1), fill=AMBER + (255,))
    d.rectangle((x0 + 12, y, x0 + 12 + bw, y + 84), fill=(9, 16, 30, 230))
    if sub:
        d.rectangle((x0 + 12, y + 84, x0 + 12 + bw * 0.98, y + 128), fill=(255, 178, 36, 240))
    if k2 > 0.5:
        ta = ease((t - 0.35) / 0.3)
        d.text((x0 + 42, y + 10), title, font=ft, fill=(255, 255, 255, int(255 * ta)))
        if sub:
            d.text((x0 + 42, y + 88), sub, font=fs, fill=(9, 16, 30, int(255 * ta)))
    paste_alpha(img, L, a)


def caption(img, text, t, dur, y=None, size=50, maxw=1500, accent_words=(), box_=True):
    """Kinetic headline text, word-by-word reveal, centered near bottom."""
    a = fade(t, dur, 0.01, 0.3)
    if a <= 0:
        return
    f = F('InterDisplay-ExtraBold', size)
    lines = wrap(f, text, maxw)
    lh = int(size * 1.22)
    total_h = lh * len(lines)
    if y is None:
        y = H - 150 - total_h
    L = layer()
    d = ImageDraw.Draw(L)
    if box_:
        mw = max(text_w(f, l) for l in lines)
        d.rectangle((W / 2 - mw / 2 - 34, y - 22, W / 2 + mw / 2 + 34, y + total_h + 16), fill=(9, 16, 30, 200))
        d.rectangle((W / 2 - mw / 2 - 34, y - 22, W / 2 - mw / 2 - 26, y + total_h + 16), fill=AMBER + (255,))
    wi = 0
    for li, line in enumerate(lines):
        lw = text_w(f, line)
        x = W / 2 - lw / 2
        for w in line.split():
            k = ease((t - 0.06 * wi) / 0.25)
            col = AMBER if w.strip('.,«»!?:') in accent_words else WHITE
            d.text((x, y + li * lh + (1 - k) * 18), w, font=f, fill=col + (int(255 * k),))
            x += text_w(f, w + ' ')
            wi += 1
    paste_alpha(img, L, a)


def big_stat(img, num, label, sub, t, dur, cx=W // 2, cy=H // 2 - 40):
    a = fade(t, dur, 0.01, 0.3)
    if a <= 0:
        return
    L = layer()
    d = ImageDraw.Draw(L)
    k = ease(t / 0.5)
    fn = F('InterDisplay-Black', int(260 * (0.85 + 0.15 * k)))
    nw = text_w(fn, num)
    d.text((cx - nw / 2, cy - 200), num, font=fn, fill=AMBER + (int(255 * k),))
    fl = F('InterDisplay-ExtraBold', 64)
    k2 = ease((t - 0.3) / 0.4)
    lw = text_w(fl, label)
    d.text((cx - lw / 2, cy + 110 + (1 - k2) * 20), label, font=fl, fill=WHITE + (int(255 * k2),))
    if sub:
        fs = F('Inter-Medium', 34)
        k3 = ease((t - 0.6) / 0.4)
        sw = text_w(fs, sub)
        d.text((cx - sw / 2, cy + 200), sub, font=fs, fill=GREY + (int(255 * k3),))
    paste_alpha(img, L, a)


def section_num(img, n, title, t, dur):
    """Small persistent numbered section tag top-right."""
    a = fade(t, dur, 0.4, 0.3)
    if a <= 0:
        return
    L = layer()
    d = ImageDraw.Draw(L)
    fn = F('InterDisplay-Black', 40)
    ft = F('Inter-Bold', 26)
    tw = text_w(ft, title)
    x1 = W - 60
    x0 = x1 - tw - 110
    d.rectangle((x0, 54, x0 + 64, 108), fill=AMBER + (255,))
    d.text((x0 + 32 - text_w(fn, str(n)) / 2, 57), str(n), font=fn, fill=NAVY + (255,))
    d.rectangle((x0 + 64, 54, x1, 108), fill=(9, 16, 30, 215))
    d.text((x0 + 84, 66), title, font=ft, fill=WHITE + (255,))
    paste_alpha(img, L, a)


def dim(img, amount):
    img.alpha_composite(Image.new('RGBA', (W, H), (5, 10, 20, int(255 * amount))))


def vignette_layer():
    v = Image.new('L', (W // 4, H // 4), 0)
    d = ImageDraw.Draw(v)
    for i in range(60):
        k = i / 60
        d.ellipse((-W / 8 + i * 4, -H / 8 + i * 2.4, W / 4 + W / 8 - i * 4, H / 4 + H / 8 - i * 2.4), fill=int(170 * (1 - k)))
    v = v.filter(ImageFilter.GaussianBlur(20)).resize((W, H))
    inv = v.point(lambda p: 170 - p if p < 170 else 0)
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.putalpha(inv)
    return out


VIGNETTE = None


def vignette(img):
    global VIGNETTE
    if VIGNETTE is None:
        VIGNETTE = vignette_layer()
    img.alpha_composite(VIGNETTE)


# ------------------------------------------------------------ backgrounds
@lru_cache(None)
def _grid_bg():
    im = Image.new('RGBA', (W, H), NAVY + (255,))
    d = ImageDraw.Draw(im)
    for x in range(0, W, 64):
        d.line((x, 0, x, H), fill=(22, 34, 56, 255))
    for y in range(0, H, 64):
        d.line((0, y, W, y), fill=(22, 34, 56, 255))
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    gd.ellipse((W * 0.15, -H * 0.3, W * 0.85, H * 0.9), fill=(40, 70, 120, 90))
    g = g.filter(ImageFilter.GaussianBlur(160))
    im.alpha_composite(g)
    return im


def grid_bg(t):
    im = _grid_bg().copy()
    return im


@lru_cache(None)
def load_photo(path):
    return Image.open(path).convert('RGB')


def ken_burns(path, t, dur, z0=1.04, z1=1.14, fx0=0.5, fy0=0.5, fx1=0.5, fy1=0.45, blur=0, darken=0.0):
    src = load_photo(path)
    sw, sh = src.size
    k = ease_io(t / max(dur, 0.01))
    z = z0 + (z1 - z0) * k
    fx = fx0 + (fx1 - fx0) * k
    fy = fy0 + (fy1 - fy0) * k
    # cover-fit
    base = max(W / sw, H / sh) * z
    cw, ch = W / base, H / base
    cx = clamp(fx * sw, cw / 2, sw - cw / 2)
    cy = clamp(fy * sh, ch / 2, sh - ch / 2)
    im = src.resize((W, H), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    im = im.convert('RGBA')
    if darken:
        dim(im, darken)
    return im


@lru_cache(None)
def round_photo(path, size, fx=0.5, fy=0.35):
    src = load_photo(path)
    sw, sh = src.size
    s = min(sw, sh)
    cx = clamp(fx * sw, s / 2, sw - s / 2)
    cy = clamp(fy * sh, s / 2, sh - s / 2)
    im = src.crop((int(cx - s / 2), int(cy - s / 2), int(cx + s / 2), int(cy + s / 2))).resize((size, size), Image.LANCZOS)
    m = Image.new('L', (size * 4, size * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    im = im.convert('RGBA')
    im.putalpha(m)
    return im


# ------------------------------------------------------------------ maps
_GEO = None


def geo():
    global _GEO
    if _GEO is None:
        d = json.load(open(os.path.join(ROOT, 'geo/countries.geojson')))
        _GEO = []
        for f in d['features']:
            p = f['properties']
            _GEO.append((p.get('ADM0_A3') or p.get('ISO_A3'), p.get('NAME'), shape(f['geometry'])))
    return _GEO


class Cam:
    """Equirectangular-ish camera with cos(lat) correction. center lon/lat, span = degrees of longitude across W."""

    def __init__(self, lon, lat, span):
        self.lon, self.lat, self.span = lon, lat, span
        self.kx = W / span
        self.ky = self.kx / math.cos(math.radians(lat)) * math.cos(math.radians(lat)) ** 0  # placeholder
        # Mercator vertical scale
        self.ky = self.kx

    def merc(self, lat):
        lat = clamp(lat, -85, 85)
        return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))

    def xy(self, lon, lat):
        x = W / 2 + (lon - self.lon) * self.kx
        y = H / 2 - (self.merc(lat) - self.merc(self.lat)) * self.ky
        return x, y

    def bounds(self):
        lon0 = self.lon - self.span / 2 - 2
        lon1 = self.lon + self.span / 2 + 2
        hspan = self.span * H / W
        return lon0, lon1, self.lat - hspan * 1.2 - 2, self.lat + hspan * 1.2 + 2


def cam_lerp(c0, c1, k):
    k = ease_io(k)
    span = math.exp(math.log(c0[2]) + (math.log(c1[2]) - math.log(c0[2])) * k)
    return Cam(c0[0] + (c1[0] - c0[0]) * k, c0[1] + (c1[1] - c0[1]) * k, span)


_simpl_cache = {}


def _geoms_for(span):
    tol = 0.02 if span < 8 else 0.05 if span < 25 else 0.12
    if tol not in _simpl_cache:
        _simpl_cache[tol] = [(a3, n, g.simplify(tol, preserve_topology=True)) for a3, n, g in geo()]
    return _simpl_cache[tol]


def _polys(g):
    if g.geom_type == 'Polygon':
        yield g
    elif g.geom_type == 'MultiPolygon':
        yield from g.geoms


def draw_map(cam, highlight=None, ss=2, land=LAND, ocean=OCEAN):
    """highlight: dict a3 -> rgba fill"""
    highlight = highlight or {}
    S = ss
    im = Image.new('RGBA', (W * S, H * S), ocean + (255,))
    d = ImageDraw.Draw(im)
    lon0, lon1, lat0, lat1 = cam.bounds()
    view = box(lon0, lat0, lon1, lat1)
    items = []
    for a3, n, g in _geoms_for(cam.span):
        if not g.intersects(view):
            continue
        items.append((a3, g))
    # graticule
    step = 5 if cam.span < 30 else 10
    for lo in range(int(lon0 // step * step), int(lon1) + step, step):
        x, _ = cam.xy(lo, 0)
        d.line((x * S, 0, x * S, H * S), fill=(18, 32, 54, 255), width=S)
    for la in range(int(lat0 // step * step), int(lat1) + step, step):
        _, y = cam.xy(0, la)
        d.line((0, y * S, W * S, y * S), fill=(18, 32, 54, 255), width=S)
    for a3, g in items:
        fill = highlight.get(a3, land + (255,))
        for p in _polys(g):
            pts = [(cam.xy(x, y)[0] * S, cam.xy(x, y)[1] * S) for x, y in p.exterior.coords]
            if len(pts) > 2:
                d.polygon(pts, fill=fill)
    for a3, g in items:
        for p in _polys(g):
            pts = [(cam.xy(x, y)[0] * S, cam.xy(x, y)[1] * S) for x, y in p.exterior.coords]
            if len(pts) > 2:
                d.line(pts + [pts[0]], fill=BORDER + (255,), width=max(1, int(1.2 * S)))
    return im.resize((W, H), Image.LANCZOS)


def map_label(img, cam, lon, lat, text, t, size=30, dx=18, dy=-18, color=WHITE, dot=True, pulse=True, sub=None, anchor='l'):
    a = ease(t / 0.4)
    if a <= 0:
        return
    x, y = cam.xy(lon, lat)
    L = layer()
    d = ImageDraw.Draw(L)
    if dot:
        if pulse:
            r = 10 + 26 * ((t * 0.8) % 1)
            pa = int(160 * (1 - (t * 0.8) % 1) * a)
            d.ellipse((x - r, y - r, x + r, y + r), outline=AMBER + (pa,), width=3)
        d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=AMBER + (int(255 * a),), outline=(9, 16, 30, int(255 * a)), width=3)
    f = F('Inter-Bold', size)
    tw = text_w(f, text)
    if anchor == 'r':
        tx = x - dx - tw - 16
    elif anchor == 'c':
        tx = x - tw / 2 - 8
    else:
        tx = x + dx
    ty = y + dy - size / 2 - 6
    hh = size + 14 + (size * 0.9 if sub else 0)
    fs = F('Inter-Medium', int(size * 0.72))
    bw = max(tw, text_w(fs, sub) if sub else 0) + 16
    d.rectangle((tx - 8 + (bw if anchor == 'r' else 0) * 0, ty - 4, tx + bw, ty - 4 + hh), fill=(9, 16, 30, int(210 * a)))
    d.text((tx, ty), text, font=f, fill=color + (int(255 * a),))
    if sub:
        d.text((tx, ty + size + 6), sub, font=fs, fill=GREY + (int(255 * a),))
    img.alpha_composite(L)


def country_label(img, cam, lon, lat, text, t, size=34, color=(200, 210, 225), spacing=6):
    a = ease(t / 0.5)
    if a <= 0:
        return
    x, y = cam.xy(lon, lat)
    f = F('InterDisplay-Bold', size)
    L = layer()
    d = ImageDraw.Draw(L)
    s = ' '.join(text) if spacing else text
    tw = text_w(f, s)
    d.text((x - tw / 2, y - size / 2), s, font=f, fill=color + (int(230 * a),))
    img.alpha_composite(L)


def bezier(p0, p1, bend=0.25):
    (x0, y0), (x1, y1) = p0, p1
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    cx, cy = mx - dy * bend, my + dx * bend
    return lambda u: ((1 - u) ** 2 * x0 + 2 * (1 - u) * u * cx + u * u * x1, (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cy + u * u * y1)


def arc(img, cam, a, b, k, color=AMBER, width=5, bend=0.22, dashed=False, head=True, phase=0.0):
    if k <= 0:
        return
    p0, p1 = cam.xy(*a), cam.xy(*b)
    B = bezier(p0, p1, bend)
    n = 80
    pts = [B(k * i / n) for i in range(n + 1)]
    S = 2
    L = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    sp = [(x * S, y * S) for x, y in pts]
    if dashed:
        for i in range(n):
            if int(i / 3 + phase) % 2 == 0:
                d.line((sp[i], sp[i + 1]), fill=color + (255,), width=width * S)
    else:
        d.line(sp, fill=color + (255,), width=width * S, joint='curve')
    if head and k > 0.05:
        x, y = sp[-1]
        px, py = sp[-3]
        ang = math.atan2(y - py, x - px)
        s = 16 * S
        d.polygon([(x + math.cos(ang) * s, y + math.sin(ang) * s),
                   (x + math.cos(ang + 2.5) * s, y + math.sin(ang + 2.5) * s),
                   (x + math.cos(ang - 2.5) * s, y + math.sin(ang - 2.5) * s)], fill=color + (255,))
    img.alpha_composite(L.resize((W, H), Image.LANCZOS))
    return B


def panel_text(img, x, y, w, title, body, t, accent=AMBER, title_size=40, body_size=32, alpha_bg=225, delay=0.0):
    k = ease((t - delay) / 0.45)
    if k <= 0:
        return 0
    ft = F('InterDisplay-ExtraBold', title_size)
    fb = F('Inter-Medium', body_size)
    lines = wrap(fb, body, w - 60) if body else []
    tl = wrap(ft, title, w - 60) if title else []
    h = 34 + len(tl) * int(title_size * 1.2) + (12 if body and title else 0) + len(lines) * int(body_size * 1.35) + 26
    L = layer()
    d = ImageDraw.Draw(L)
    off = (1 - k) * 40
    d.rectangle((x + off, y, x + w + off, y + h), fill=(9, 16, 30, int(alpha_bg * k)))
    d.rectangle((x + off, y, x + 8 + off, y + h), fill=accent + (int(255 * k),))
    yy = y + 22
    for l in tl:
        d.text((x + 34 + off, yy), l, font=ft, fill=accent + (int(255 * k),))
        yy += int(title_size * 1.2)
    if body and title:
        yy += 12
    for l in lines:
        d.text((x + 34 + off, yy), l, font=fb, fill=WHITE + (int(255 * k),))
        yy += int(body_size * 1.35)
    img.alpha_composite(L)
    return h
