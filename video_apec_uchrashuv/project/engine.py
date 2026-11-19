"""Frame engine: photo Ken Burns, video plates, maps, graphics, news overlays."""
import math, os, subprocess, functools, json, zipfile, io
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1920, 1080, 30
ROOT = os.path.dirname(os.path.abspath(__file__))
FD = "/usr/share/fonts/opentype/inter/"

NAVY = (11, 20, 38); NAVY2 = (19, 33, 61); RED = (200, 16, 46); WHITE = (255, 255, 255)
GOLD = (242, 183, 5); GREY = (170, 180, 195); DARK = (6, 10, 20)


@functools.lru_cache(None)
def font(name, size):
    return ImageFont.truetype(FD + name + ".otf", size)


def ease(x):  # easeInOutCubic
    x = min(max(x, 0.0), 1.0)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def eout(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- grading
_vig = None


def vignette():
    global _vig
    if _vig is None:
        y, x = np.mgrid[0:H, 0:W]
        d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
        _vig = np.clip(1 - 0.28 * np.clip(d - 0.55, 0, None) ** 1.6, 0.6, 1)[..., None].astype(np.float32)
    return _vig


def grade(img, contrast=1.06, sat=0.94, warm=0.0):
    a = np.asarray(img, dtype=np.float32)
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    a = lum[..., None] + (a - lum[..., None]) * sat
    a = (a - 128) * contrast + 128
    if warm:
        a[..., 0] += 6 * warm; a[..., 2] -= 6 * warm
    a *= vignette()
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ---------------------------------------------------------------- photo plate
@functools.lru_cache(16)
def load_photo(path):
    im = Image.open(path).convert("RGB")
    return im


def cover_size(iw, ih):
    s = max(W / iw, H / ih)
    return s


def kenburns(path, p, z0=1.0, z1=1.12, c0=(0.5, 0.5), c1=(0.5, 0.5), blurfill=False):
    """p in 0..1. zoom relative to cover. c = focus center as fraction of image."""
    im = load_photo(path)
    iw, ih = im.size
    if blurfill and iw / ih < 1.4:
        return portrait_fill(im, p, z0, z1)
    e = ease(p)
    z = lerp(z0, z1, e)
    cx = lerp(c0[0], c1[0], e) * iw; cy = lerp(c0[1], c1[1], e) * ih
    s = cover_size(iw, ih) * z
    vw, vh = W / s, H / s  # visible region in source px
    x0 = min(max(cx - vw / 2, 0), iw - vw); y0 = min(max(cy - vh / 2, 0), ih - vh)
    return im.transform((W, H), Image.AFFINE, (1 / s, 0, x0, 0, 1 / s, y0), resample=Image.BICUBIC)


def portrait_fill(im, p, z0, z1):
    bg = im.resize((W, int(W * im.size[1] / im.size[0])))
    bg = bg.crop((0, (bg.size[1] - H) // 2, W, (bg.size[1] - H) // 2 + H)).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", (W, H), DARK), 0.45)
    z = lerp(z0, z1, ease(p))
    h = int(H * z); w = int(im.size[0] * h / im.size[1])
    fg = im.resize((w, h), Image.BICUBIC)
    bg.paste(fg, ((W - w) // 2, (H - h) // 2))
    return bg


# ---------------------------------------------------------------- video plate
class VideoPlate:
    def __init__(self, path, start, dur, speed=1.0):
        vf = f"setpts=PTS/{speed},fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
        self.p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-ss", str(start), "-i", path,
                                   "-t", str(dur / speed + 1), "-an", "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                  stdout=subprocess.PIPE)
        self.last = Image.new("RGB", (W, H), DARK)

    def frame(self):
        b = self.p.stdout.read(W * H * 3)
        if len(b) == W * H * 3:
            self.last = Image.frombytes("RGB", (W, H), b)
        return self.last

    def close(self):
        self.p.kill()


# ---------------------------------------------------------------- maps
@functools.lru_cache(1)
def countries():
    import shapefile
    z = zipfile.ZipFile(os.path.join(ROOT, "geo/ne50.zip"))
    names = z.namelist()
    shp = [n for n in names if n.endswith(".shp")][0][:-4]
    r = shapefile.Reader(shp=io.BytesIO(z.read(shp + ".shp")), dbf=io.BytesIO(z.read(shp + ".dbf")), shx=io.BytesIO(z.read(shp + ".shx")))
    flds = [f[0] for f in r.fields[1:]]
    out = []
    for sr in r.iterShapeRecords():
        rec = dict(zip(flds, sr.record))
        pts = sr.shape.points; parts = list(sr.shape.parts) + [len(pts)]
        rings = [np.array(pts[parts[i]:parts[i + 1]], np.float64) for i in range(len(parts) - 1)]
        out.append((rec.get("ADM0_A3"), rec.get("NAME"), rings, sr.shape.bbox))
    return out


def merc_y(lat):
    lat = np.clip(lat, -85, 85)
    return np.degrees(np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)))


def draw_map(view, highlight=None, dim=None, ss=2, land=(38, 52, 80), sea=(8, 16, 32), border=(70, 88, 120)):
    """view=(lon_c, lat_c, width_deg). highlight={A3:(r,g,b)}"""
    highlight = highlight or {}
    lon_c, lat_c, wd = view
    sw, sh = W * ss, H * ss
    sc = sw / wd
    ymc = merc_y(lat_c)
    img = Image.new("RGB", (sw, sh), sea)
    d = ImageDraw.Draw(img)
    x0, x1 = lon_c - wd / 2, lon_c + wd / 2
    hy = sh / sc / 2
    for a3, nm, rings, bb in countries():
        for shift in (0, 360, -360):
            if bb[2] + shift < x0 or bb[0] + shift > x1:
                continue
            if merc_y(bb[3]) < ymc - hy - 2 or merc_y(bb[1]) > ymc + hy + 2:
                continue
            col = highlight.get(a3, land)
            for ring in rings:
                xs = (ring[:, 0] + shift - x0) * sc
                ys = sh / 2 - (merc_y(ring[:, 1]) - ymc) * sc
                if len(xs) < 3:
                    continue
                d.polygon(list(zip(xs.tolist(), ys.tolist())), fill=col, outline=border)
    img = img.resize((W, H), Image.LANCZOS)
    return img


def geo_to_px(view, lon, lat):
    lon_c, lat_c, wd = view
    sc = W / wd
    return ((lon - (lon_c - wd / 2)) * sc, H / 2 - (merc_y(lat) - merc_y(lat_c)) * sc)


def view_lerp(v0, v1, t):
    e = ease(t)
    return (lerp(v0[0], v1[0], e), lerp(v0[1], v1[1], e), math.exp(lerp(math.log(v0[2]), math.log(v1[2]), e)))


def pin(img, view, lon, lat, label, t=1.0, color=RED, size=34, side="r"):
    d = ImageDraw.Draw(img, "RGBA")
    x, y = geo_to_px(view, lon, lat)
    a = eout(t)
    r = 10 + 4 * math.sin(t * 6)
    pr = 18 + 40 * ((t * 1.2) % 1)
    d.ellipse([x - pr, y - pr, x + pr, y + pr], outline=color + (int(200 * (1 - (t * 1.2) % 1)),), width=3)
    d.ellipse([x - r, y - r, x + r, y + r], fill=color + (255,), outline=WHITE + (255,), width=3)
    if label:
        f = font("Inter-Bold", size)
        tw = d.textlength(label, font=f)
        lx = x + 24 if side == "r" else x - 24 - tw - 24
        d.rounded_rectangle([lx, y - size * 0.8, lx + (tw + 24) * a, y + size * 0.8], 6, fill=(0, 0, 0, 190))
        if a > 0.6:
            d.text((lx + 12, y - size * 0.62), label, font=f, fill=WHITE)


def arc(img, view, p0, p1, t, color=GOLD, width=5, plane=True):
    d = ImageDraw.Draw(img, "RGBA")
    a = geo_to_px(view, *p0); b = geo_to_px(view, *p1)
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - abs(b[0] - a[0]) * 0.35 - 40
    n = 60; k = int(n * eout(t))
    pts = []
    for i in range(k + 1):
        u = i / n
        pts.append(((1 - u) ** 2 * a[0] + 2 * (1 - u) * u * mx + u * u * b[0], (1 - u) ** 2 * a[1] + 2 * (1 - u) * u * my + u * u * b[1]))
    if len(pts) > 1:
        d.line(pts, fill=color + (255,), width=width, joint="curve")
        if plane:
            x, y = pts[-1]; d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=WHITE)


# ---------------------------------------------------------------- graphic backgrounds
_bgcache = {}


def news_bg(t=0.0, tint=NAVY):
    key = tint
    if key not in _bgcache:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        g = np.clip(1 - np.sqrt(((x - W * 0.3) / W) ** 2 + ((y - H * 0.35) / H) ** 2) * 1.2, 0, 1)
        a = np.zeros((H, W, 3), np.float32)
        for i in range(3):
            a[..., i] = DARK[i] + (tint[i] * 1.6 - DARK[i]) * g
        # subtle grid
        a[(x.astype(int) % 80 == 0) | (y.astype(int) % 80 == 0)] += 7
        _bgcache[key] = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    img = _bgcache[key].copy()
    d = ImageDraw.Draw(img, "RGBA")
    # moving light streaks
    for i in range(3):
        xx = (t * 90 + i * 700) % (W + 600) - 300
        d.polygon([(xx, 0), (xx + 60, 0), (xx - 340, H), (xx - 400, H)], fill=(255, 255, 255, 6))
    return img


def blurred(img, r=18, dark=0.5):
    b = img.filter(ImageFilter.GaussianBlur(r))
    return Image.blend(b, Image.new("RGB", (W, H), DARK), dark)


# ---------------------------------------------------------------- text helpers
def text_box(d, xy, s, f, fill=WHITE, anchor="la"):
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def wrap(d, s, f, maxw):
    words = s.split(); lines = []; cur = ""
    for w_ in words:
        tr = (cur + " " + w_).strip()
        if d.textlength(tr, font=f) <= maxw:
            cur = tr
        else:
            lines.append(cur); cur = w_
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- overlays
TICKER = ("APEC-2026 · SHENCHJEN: Tramp, Si Szinpin va Putin ilk bor uch tomonlama formatda uchrashdi   •   "
          "Uchrashuv taxminan 90 daqiqa davom etdi (CCTV)   •   Yakunda umumiy bayonot eʼlon qilinmadi   •   "
          "Xitoy davlat OAV: tomonlar barqaror energiya oqimi boʻyicha kelishdi, matn eʼlon qilinmagan   •   "
          "New START shartnomasi muddati 5-fevral kuni tugagan   •   Dekabr: G20 sammiti — Florida   •   ")


def ticker(img, gt):
    d = ImageDraw.Draw(img, "RGBA")
    y0 = H - 58
    d.rectangle([0, y0, W, H], fill=NAVY + (245,))
    f = font("Inter-SemiBold", 27)
    tw = d.textlength(TICKER, font=f)
    off = (gt * 110) % tw
    x = 250 - off
    while x < W:
        d.text((x, y0 + 14), TICKER, font=f, fill=WHITE)
        x += tw
    d.rectangle([0, y0, 230, H], fill=RED + (255,))
    d.text((115, y0 + 29), "YANGILIK", font=font("InterDisplay-Black", 28), fill=WHITE, anchor="mm")
    d.rectangle([0, y0 - 4, W, y0], fill=RED + (255,))


def bug(img, gt):
    d = ImageDraw.Draw(img, "RGBA")
    f = font("Inter-Bold", 24)
    s = "SHENCHJEN · 19.11.2026"
    tw = d.textlength(s, font=f)
    d.rounded_rectangle([48, 42, 48 + tw + 66, 86], 6, fill=(0, 0, 0, 150))
    on = (gt % 1.4) < 0.9
    d.ellipse([62, 56, 78, 72], fill=RED if on else (120, 20, 30))
    d.text((90, 64), s, font=f, fill=WHITE, anchor="lm")


def credit(img, s, has_ticker=True):
    if not s:
        return
    d = ImageDraw.Draw(img, "RGBA")
    f = font("Inter-SemiBold", 21)
    tw = d.textlength(s, font=f)
    y = H - 58 - 46 if has_ticker else H - 60
    d.rectangle([48, y, 48 + tw + 24, y + 34], fill=(0, 0, 0, 165))
    d.text((60, y + 17), s, font=f, fill=(235, 235, 235), anchor="lm")


def lower_third(img, title, sub, lt, ldur, y=760):
    """lt local time since appear; ldur visible duration."""
    if lt < 0 or lt > ldur:
        return
    d = ImageDraw.Draw(img, "RGBA")
    a = eout(lt / 0.45) * (1 - eout((lt - ldur + 0.35) / 0.35))
    f1 = font("InterDisplay-ExtraBold", 50); f2 = font("Inter-Medium", 31)
    w1 = d.textlength(title, font=f1) + 60; w2 = d.textlength(sub, font=f2) + 60 if sub else 0
    x = 48 - (1 - a) * (max(w1, w2) + 80)
    d.rectangle([x, y, x + 12, y + 76 + (52 if sub else 0)], fill=RED)
    d.rectangle([x + 12, y, x + 12 + w1, y + 76], fill=WHITE + (245,))
    d.text((x + 42, y + 38), title, font=f1, fill=NAVY, anchor="lm")
    if sub:
        d.rectangle([x + 12, y + 76, x + 12 + w2, y + 128], fill=NAVY + (240,))
        d.text((x + 42, y + 102), sub, font=f2, fill=WHITE, anchor="lm")


def headline(img, s, lt, ldur, pos="bl", size=66, color=WHITE, box=True, maxw=1500, sub=None, accent=RED):
    if lt < 0 or lt > ldur:
        return
    d = ImageDraw.Draw(img, "RGBA")
    f = font("InterDisplay-Black", size)
    lines = wrap(d, s, f, maxw)
    a = eout(lt / 0.4) * (1 - eout((lt - ldur + 0.3) / 0.3))
    lh = int(size * 1.18)
    th = lh * len(lines) + (int(size * 0.75) if sub else 0)
    tw = max(d.textlength(l, font=f) for l in lines)
    if pos == "bl":
        x, y = 64, H - 58 - 110 - th
    elif pos == "c":
        x, y = (W - tw) / 2, (H - th) / 2 - 20
    else:
        x, y = 64, 140
    yo = (1 - a) * 40
    if box:
        d.rectangle([x - 24, y - 18 + yo, x + tw + 30, y + th + 14 + yo], fill=(0, 0, 0, int(170 * a)))
        d.rectangle([x - 24, y - 18 + yo, x - 14, y + th + 14 + yo], fill=accent + (int(255 * a),))
    for i, l in enumerate(lines):
        d.text((x, y + i * lh + yo), l, font=f, fill=color + (int(255 * a),))
    if sub:
        d.text((x, y + len(lines) * lh + yo + 4), sub, font=font("Inter-SemiBold", int(size * 0.5)), fill=GOLD + (int(255 * a),))


def quote_card(img, q, who, lt, ldur, side="r"):
    if lt < 0:
        return
    d = ImageDraw.Draw(img, "RGBA")
    a = eout(lt / 0.5) * (1 - eout((lt - ldur + 0.3) / 0.3))
    pw = 860
    x = W - pw - 70 if side == "r" else 70
    x += (1 - a) * (80 if side == "r" else -80)
    f = font("InterDisplay-Bold", 50)
    lines = wrap(d, q, f, pw - 110)
    h = 110 + len(lines) * 62 + 70
    y = (H - 58 - h) / 2
    d.rounded_rectangle([x, y, x + pw, y + h], 10, fill=(8, 14, 28, int(225 * a)))
    d.rectangle([x, y, x + 10, y + h], fill=RED + (int(255 * a),))
    d.text((x + 50, y + 10), "“", font=font("InterDisplay-Black", 120), fill=RED + (int(255 * a),))
    # typewriter reveal
    nchar = int(sum(len(l) for l in lines) * min(1, lt / max(0.6, ldur * 0.45)))
    c = 0
    for i, l in enumerate(lines):
        s = l[:max(0, nchar - c)]; c += len(l)
        d.text((x + 55, y + 100 + i * 62), s, font=f, fill=WHITE + (int(255 * a),))
    d.text((x + 55, y + h - 52), "— " + who, font=font("Inter-SemiBold", 30), fill=GOLD + (int(255 * a),))


def bumper(img, title, sub, lt, ldur, num=None):
    d = ImageDraw.Draw(img, "RGBA")
    a = eout(lt / 0.35)
    # red diagonal band sweeping
    bx = lerp(-W, 0, eout(lt / 0.5))
    d.polygon([(bx, 380), (bx + W + 200, 380), (bx + W + 120, 700), (bx - 80, 700)], fill=RED + (235,))
    f = font("InterDisplay-Black", 112)
    sc = lerp(1.25, 1.0, eout(lt / 0.5))
    if num:
        d.text((W / 2, 300), num, font=font("InterDisplay-Black", 54), fill=GOLD + (int(255 * a),), anchor="mm")
    tf = font("InterDisplay-Black", int(112 * sc))
    d.text((W / 2, 540), title, font=tf, fill=WHITE + (int(255 * a),), anchor="mm")
    if sub:
        d.text((W / 2, 760), sub, font=font("Inter-SemiBold", 40), fill=(220, 225, 235, int(255 * a)), anchor="mm")


def flash(img, lt, dur=0.18):
    if lt < dur:
        return Image.blend(img, Image.new("RGB", (W, H), WHITE), 1 - lt / dur)
    return img


def fade_in(img, lt, dur=0.3):
    if lt < dur:
        return Image.blend(Image.new("RGB", (W, H), DARK), img, lt / dur)
    return img


def whip(img, lt, dur=0.2):
    if lt >= dur:
        return img
    k = 1 - lt / dur
    sh = int(260 * k)
    im = ImageChops.offset(img, -sh, 0)
    return im.filter(ImageFilter.BoxBlur(int(1 + 22 * k)))
