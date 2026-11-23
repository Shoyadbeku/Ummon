# -*- coding: utf-8 -*-
# News-documentary renderer: scenes -> raw frames -> ffmpeg (1920x1080, 25 fps)
import math, json, sys, os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = os.environ["SCR"]
W, H, FPS = 1920, 1080, 25
DUR = 383.25
IMG = S + "/assets/img/"
MAPS = S + "/assets/maps/"
FD = "/usr/share/fonts/opentype/inter/"
_fc = {}
def F(w, size):
    k = (w, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FD + {"black": "InterDisplay-Black.otf", "xb": "InterDisplay-ExtraBold.otf",
            "b": "Inter-Bold.otf", "sb": "Inter-SemiBold.otf", "m": "Inter-Medium.otf", "r": "Inter-Regular.otf"}[w], size)
    return _fc[k]

RED = (226, 54, 42); AMBER = (242, 177, 52); WHITE = (255, 255, 255); NAVY = (9, 16, 28)
GREY = (170, 182, 200); BLUE = (70, 140, 220); GREEN = (64, 190, 120)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 3 * x * x - 2 * x * x * x
def lerp(a, b, t): return a + (b - a) * t
def prog(t, a, b): return clamp((t - a) / max(1e-6, b - a))

# ---------------- image helpers ----------------
_ic = {}
def load(name, maxw=3200):
    if name not in _ic:
        im = Image.open(IMG + name).convert("RGB")
        if im.width > maxw: im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
        _ic[name] = im
    return _ic[name]

def kenburns(name, p, z0=1.0, z1=1.12, fx0=0.5, fy0=0.5, fx1=0.5, fy1=0.5, grade=True):
    im = load(name)
    iw, ih = im.size
    ar = W / H
    if iw / ih > ar: bw, bh = ih * ar, ih
    else: bw, bh = iw, iw / ar
    z = lerp(z0, z1, eio(p)); cw, ch = bw / z, bh / z
    fx, fy = lerp(fx0, fx1, eio(p)), lerp(fy0, fy1, eio(p))
    x0 = clamp(fx * iw - cw / 2, 0, iw - cw); y0 = clamp(fy * ih - ch / 2, 0, ih - ch)
    out = im.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR)
    if grade: out = colorgrade(out)
    return out

_vig = None
def colorgrade(im):
    global _vig
    if _vig is None:
        v = Image.radial_gradient("L").resize((W, H)).point(lambda x: int(clamp((x - 120) / 135) * 150))
        _vig = Image.merge("RGBA", [Image.new("L", (W, H), 4), Image.new("L", (W, H), 8), Image.new("L", (W, H), 16), v])
    im = Image.blend(im, Image.new("RGB", (W, H), (14, 26, 44)), 0.12)
    im = im.convert("RGBA"); im.alpha_composite(_vig)
    return im.convert("RGB")

def portrait(name, p):
    im = load(name)
    bg = kenburns(name, p, 1.0, 1.05).filter(ImageFilter.GaussianBlur(28))
    bg = Image.blend(bg, Image.new("RGB", (W, H), NAVY), 0.45)
    z = lerp(1.0, 1.06, eio(p)); fh = int(H * 0.92 * z); fw = int(im.width * fh / im.height)
    fg = im.resize((fw, fh), Image.BILINEAR)
    bg.paste(fg, ((W - fw) // 2, (H - fh) // 2))
    return bg

def dark(alpha=0.55, col=NAVY):
    return Image.new("RGBA", (W, H), col + (int(255 * alpha),))

def darken(im, a):
    return Image.blend(im, Image.new("RGB", (W, H), NAVY), a)

# ---------------- text / graphics helpers ----------------
def tw(d, s, f): b = d.textbbox((0, 0), s, font=f); return b[2] - b[0]
def text(d, xy, s, f, fill=WHITE, anchor="la", shadow=True, alpha=255):
    if alpha <= 0: return
    if shadow: d.text((xy[0] + 3, xy[1] + 3), s, font=f, fill=(0, 0, 0, int(alpha * 0.6)), anchor=anchor)
    d.text(xy, s, font=f, fill=fill[:3] + (alpha,), anchor=anchor)

def wrap(d, s, f, maxw):
    words = s.split(); lines = []; cur = ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if tw(d, t, f) <= maxw: cur = t
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines

def layer():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); return L, ImageDraw.Draw(L)

def comp(base, L):
    b = base.convert("RGBA"); b.alpha_composite(L); return b.convert("RGB")

def lower_third(d, t, tag, line, t0=0.0, sub=None):
    p = eo(prog(t, t0, t0 + 0.6))
    if p <= 0: return
    x = int(lerp(-900, 80, p)); y = 820
    ft = F("b", 26); fl = F("sb", 40)
    wt = tw(d, tag, ft) + 36
    d.rectangle([x, y, x + wt, y + 46], fill=RED + (255,))
    d.text((x + 18, y + 9), tag, font=ft, fill=WHITE)
    wl = tw(d, line, fl) + 48
    d.rectangle([x, y + 46, x + max(wl, wt), y + 116], fill=(255, 255, 255, 240))
    d.text((x + 24, y + 58), line, font=fl, fill=NAVY)
    if sub:
        fs = F("m", 26); ws = tw(d, sub, fs) + 48
        d.rectangle([x, y + 116, x + ws, y + 160], fill=(14, 26, 44, 230))
        d.text((x + 24, y + 123), sub, font=fs, fill=GREY)

def credit(d, s, alpha=255):
    f = F("m", 20); x, y = 1880, 1040
    w_ = tw(d, s, f)
    d.rectangle([x - w_ - 16, y - 6, x + 8, y + 26], fill=(0, 0, 0, int(alpha * 0.55)))
    d.text((x - w_ - 4, y - 1), s, font=f, fill=(225, 230, 238, alpha))

def bug(d):
    # persistent topic bug, top-left
    f1 = F("b", 22); f2 = F("m", 22)
    d.rectangle([60, 48, 72, 84], fill=RED)
    d.text((86, 50), "CHEGARADAGI TIRBANDLIK", font=f1, fill=WHITE)
    d.text((86 + tw(d, "CHEGARADAGI TIRBANDLIK", f1) + 18, 50), "23.11.2026", font=f2, fill=GREY)

def big_number(d, xy, val, t, a, b, fmt="{:,.0f}", f=None, fill=WHITE, anchor="mm", suffix=""):
    v = val * eo(prog(t, a, b))
    s = fmt.format(v).replace(",", " ") + suffix
    text(d, xy, s, f or F("black", 220), fill=fill, anchor=anchor)

def fadein_alpha(t, a, dur=0.4): return int(255 * eo(prog(t, a, a + dur)))

def title_card(base, t, kicker, title, sub=None):
    L, d = layer()
    L.alpha_composite(dark(0.6))
    a = fadein_alpha(t, 0.0, 0.5)
    p = eo(prog(t, 0, 0.6))
    d.rectangle([W // 2 - int(160 * p), 430, W // 2 + int(160 * p), 436], fill=RED)
    text(d, (W // 2, 400), kicker, F("b", 34), fill=AMBER, anchor="ms", alpha=a)
    text(d, (W // 2, 540), title, F("black", 110), anchor="mm", alpha=fadein_alpha(t, 0.15, 0.5))
    if sub: text(d, (W // 2, 640), sub, F("m", 40), fill=GREY, anchor="mm", alpha=fadein_alpha(t, 0.4, 0.5))
    return comp(base, L)

def quote_card(base, t, q, who, role, t0=0.0, size=64):
    base = darken(base.filter(ImageFilter.GaussianBlur(18)), 0.35)
    L, d = layer()
    L.alpha_composite(dark(0.45))
    a = fadein_alpha(t, t0, 0.5)
    text(d, (150, 270), "“", F("black", 300), fill=RED, alpha=a, shadow=False)
    lines = wrap(d, q, F("xb", size), 1450)
    y = 400
    for i, ln in enumerate(lines):
        text(d, (280, y), ln, F("xb", size), alpha=fadein_alpha(t, t0 + 0.15 + 0.12 * i, 0.5)); y += int(size * 1.3)
    a2 = fadein_alpha(t, t0 + 0.6, 0.5)
    d.rectangle([260, y + 30, 268, y + 110], fill=RED + (a2,))
    text(d, (290, y + 30), who, F("b", 38), alpha=a2)
    text(d, (290, y + 78), role, F("m", 28), fill=GREY, alpha=a2)
    return comp(base, L)

# ---------------- map ----------------
_maps = {}
def getmap(name):
    if name not in _maps:
        m = json.load(open(MAPS + name + ".json")); m["im"] = Image.open(MAPS + name + ".png").convert("RGB")
        m["hl"] = Image.open(MAPS + name + "_hl.png") if os.path.exists(MAPS + name + "_hl.png") else None
        _maps[name] = m
    return _maps[name]

def geo2base(m, lon, lat):
    lon0, lon1, lat0, lat1 = m["view"]; c = math.cos(math.radians((lat0 + lat1) / 2))
    k = m["W"] / ((lon1 - lon0) * c)
    return (lon - lon0) * c * k, (lat1 - lat) * k

def mapview(name, cam, hl_alpha=0.0):
    """cam=(lon, lat, width_deg). returns image and geo->screen fn"""
    m = getmap(name)
    lon0, lon1, lat0, lat1 = m["view"]; c = math.cos(math.radians((lat0 + lat1) / 2))
    k = m["W"] / ((lon1 - lon0) * c)
    cx, cy = geo2base(m, cam[0], cam[1])
    bw = cam[2] * c * k; bh = bw * H / W
    box = (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
    im = m["im"].transform((W, H), Image.EXTENT, box, Image.BILINEAR)
    if hl_alpha > 0 and m["hl"] is not None:
        mask = m["hl"].transform((W, H), Image.EXTENT, box, Image.BILINEAR).point(lambda v: int(v * 0.2 * hl_alpha))
        im.paste(Image.new("RGB", (W, H), RED), (0, 0), mask)
    sc = W / bw
    def g2s(lon, lat):
        x, y = geo2base(m, lon, lat); return ((x - box[0]) * sc, (y - box[1]) * sc)
    return im, g2s

def pin(d, xy, label, t, t0, col=RED, side="r", size=34, sub=None):
    a = fadein_alpha(t, t0, 0.4)
    if a <= 0: return
    x, y = xy; pulse = (t - t0) % 1.6 / 1.6
    r = 14 + 40 * pulse
    d.ellipse([x - r, y - r, x + r, y + r], outline=col + (int(a * (1 - pulse)),), width=3)
    d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=col + (a,), outline=WHITE + (a,), width=3)
    f = F("b", size)
    if side == "r": tx, an = x + 26, "lm"
    elif side == "l": tx, an = x - 26, "rm"
    w_ = tw(d, label, f)
    bx0 = tx - 10 if side == "r" else tx - w_ - 10
    d.rectangle([bx0, y - size * 0.8, bx0 + w_ + 20, y + size * 0.8], fill=(9, 16, 28, int(a * 0.8)))
    text(d, (tx, y), label, f, anchor=an, alpha=a, shadow=False)
    if sub:
        fs = F("m", 24)
        text(d, (tx, y + size * 0.8 + 18), sub, fs, fill=GREY, anchor=an, alpha=a)

def citylabel(d, xy, label, a=255, size=26):
    x, y = xy
    d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(230, 235, 245, a))
    text(d, (x + 12, y), label, F("m", size), fill=(220, 228, 240), anchor="lm", alpha=a)

def countrylabel(d, xy, label, a=255, size=40):
    text(d, xy, label, F("b", size), fill=(150, 175, 210), anchor="mm", alpha=a, shadow=False)

def arrow(d, pts, p, col=AMBER, width=8, a=255):
    """animated polyline arrow, pts in screen coords, p in 0..1"""
    if p <= 0: return
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    tot = sum(seg); goal = tot * p; acc = 0; out = [pts[0]]
    for i, s in enumerate(seg):
        if acc + s >= goal:
            r = (goal - acc) / s
            out.append((lerp(pts[i][0], pts[i + 1][0], r), lerp(pts[i][1], pts[i + 1][1], r))); break
        acc += s; out.append(pts[i + 1])
    d.line(out, fill=col + (a,), width=width, joint="curve")
    (x0, y0), (x1, y1) = out[-2], out[-1]
    ang = math.atan2(y1 - y0, x1 - x0); L_ = 30
    d.polygon([(x1 + math.cos(ang) * 8, y1 + math.sin(ang) * 8),
               (x1 - L_ * math.cos(ang - 0.45), y1 - L_ * math.sin(ang - 0.45)),
               (x1 - L_ * math.cos(ang + 0.45), y1 - L_ * math.sin(ang + 0.45))], fill=col + (a,))

def curve(p0, p1, bend=0.2, n=40):
    (x0, y0), (x1, y1) = p0, p1
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    nx, ny = -(y1 - y0), (x1 - x0)
    cx, cy = mx + nx * bend, my + ny * bend
    return [((1 - u) ** 2 * x0 + 2 * (1 - u) * u * cx + u * u * x1, (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cy + u * u * y1)
            for u in [i / n for i in range(n + 1)]]

# geo points
TASH = (69.279, 41.311); YALL = (68.74, 40.954); SHYM = (69.588, 42.315); SHAR = (67.97, 41.258)
GISHT = (69.15, 41.45)  # approximate
KHOR = (80.41, 44.2); ALMATY = (76.95, 43.24)
CN = (88.0, 42.5); RU = (60.0, 56.5); BY = (40.0, 55.0); IR = (56.0, 33.5); TM = (59.0, 38.8); TJ = (69.5, 38.6)

# ======================= SCENES =======================
JOD1 = "The_Journey_of_Discovery_-_From_Kazakhstan_to_Uzbekistan_(7032216873).jpg"
JOD2 = "The_Journey_of_Discovery_-_From_Kazakhstan_to_Uzbekistan_(6886118102).jpg"
QAP1 = "Qaplanbek_border_crossing_KAZ-UZB.jpg"; QAP2 = "Qaplanbek_border_crossing_KAZ-UZB_1.jpg"
ZZB = "Zhibek_Zholy_Border_Crossing.jpg"; ZZS = "Zhibek_Zholy_on_a_Snowy_Day.jpg"
KHN = "New_Khorgos_Port_of_Entry.jpg"; KHC = "Chinese-Kazakh_Khorgas_border.jpg"
CUS = "Bayroq_UZB_customs.jpg"
HOWO = "HOWO_truck,_UZ.jpg"; HOWOK = "HOWO,_Karakalpakstan.jpg"; HOWOT = "CNHTC_HOWO_A6._Toshkent._Taras_Shevchenko_k.jpg"
MAZ = "Ташкент,_Малая_кольцевая_у_вокзала,_МАЗ.jpg"
TSK = "Tashkent_skyline_2019.jpg"; TSN = "Tashkent_City_at_Night.jpg"
DAWN = "Dawn_on_the_Road_(5606945976).jpg"; ISS = "ISS024-E-8673_-_View_of_Kazakhstan.jpg"; STEP = "Степная_дорога_-_panoramio_(2).jpg"

CR = {
 JOD1: "FOTO: Land Rover MENA / Wikimedia Commons · CC BY 2.0 · ARXIV, 2012",
 JOD2: "FOTO: Land Rover MENA / Wikimedia Commons · CC BY 2.0 · ARXIV, 2012",
 QAP1: "FOTO: Nurken / Wikimedia Commons · CC BY-SA 4.0 · 2026",
 QAP2: "FOTO: Nurken / Wikimedia Commons · CC BY-SA 4.0 · 2026",
 ZZB: "FOTO: Fred Cherrygarden / Wikimedia Commons · CC BY-SA 4.0 · 2024",
 ZZS: "FOTO: Fred Cherrygarden / Wikimedia Commons · CC BY-SA 4.0 · 2024",
 KHN: "FOTO: Akira CA / Wikimedia Commons · CC BY-SA 4.0 · 2024",
 KHC: "FOTO: Purplepumpkins / Wikimedia Commons · CC BY-SA 3.0 · 2012",
 CUS: "FOTO: Ulugbek Shovazov / Wikimedia Commons · CC BY-SA 4.0",
 HOWO: "FOTO: Raf24 / Wikimedia Commons · CC BY 4.0 · 2025",
 HOWOK: "FOTO: Raf24 / Wikimedia Commons · CC BY 4.0 · 2025",
 HOWOT: "FOTO: Jamshid Nurkulov / Wikimedia Commons · CC BY 4.0 · 2025",
 MAZ: "FOTO: Nikolai Bulykin / Wikimedia Commons · CC BY-SA 4.0 · 2023",
 TSK: "FOTO: Guidecity / Wikimedia Commons · CC BY-SA 4.0",
 TSN: "FOTO: Drksll / Wikimedia Commons · CC BY-SA 4.0",
 DAWN: "FOTO: upyernoz / Wikimedia Commons · CC BY 2.0 · ARXIV, 2010",
 ISS: "FOTO: NASA / ISS Expedition 24 · Public domain",
 STEP: "FOTO: Nikolay Olkhovoy / Wikimedia Commons · CC BY 3.0",
}
MAPCR = "XARITA: Natural Earth (public domain) · grafika: tahririyat"

def have(n): return os.path.exists(IMG + n)
def photo(n, p, *a, **k):
    if have(n): return kenburns(n, p, *a, **k), CR[n]
    im, _ = mapview("wide", (64, 42, 30)); return darken(im.filter(ImageFilter.GaussianBlur(6)), 0.3), MAPCR

def with_credit(im, cr, t, extra=None):
    L, d = layer(); bug(d); credit(d, cr)
    if extra: extra(d)
    return comp(im, L)

# -- S1 HOOK 0-6.6
def s_hook(t, D):
    im, cr = photo(JOD1, t / D, 1.0, 1.45, 0.5, 0.6, 0.72, 0.78)
    L, d = layer()
    L.alpha_composite(dark(0.35))
    big_number(d, (W // 2, 470), 990, t, 0.1, 2.2, f=F("black", 260))
    text(d, (W // 2, 640), "TA YUK MASHINASI", F("xb", 64), anchor="mm", alpha=fadein_alpha(t, 1.0))
    a = fadein_alpha(t, 3.0)
    if a:
        d.rectangle([W // 2 - 230, 700, W // 2 + 230, 790], fill=RED + (a,))
        text(d, (W // 2, 745), "≈ 40 KM NAVBAT", F("black", 54), anchor="mm", alpha=a, shadow=False)
    bug(d); credit(d, cr + "  |  Arxiv surat: shu kungi voqea emas")
    return comp(im, L)

# -- S2 drivers 6.6-11.3
def s_drivers(t, D):
    im, cr = photo(HOWO, t / D, 1.05, 1.15, 0.5, 0.5, 0.45, 0.45)
    def ex(d):
        lower_third(d, t, "HAYDOVCHILAR", "Bir necha kun kabinada", 0.2, "Yukni tashlab keta olmaydi")
    return with_credit(im, cr, t, ex)

# -- S3 map Turkistan 11.3-20.2
def s_map1(t, D):
    p = eio(prog(t, 0, 4.5))
    cam = (lerp(66.5, 68.8, p), lerp(45.0, 41.6, p), lerp(30, 5.0, p))
    name = "wide" if cam[2] > 9 else "close"
    im, g = mapview(name, cam, hl_alpha=eo(prog(t, 4.0, 5.0)))
    L, d = layer()
    if t < 4.2:
        a = 255 - fadein_alpha(t, 3.4, 0.6)
        countrylabel(d, g(67.5, 48.0), "QOZOG‘ISTON", a, 56); countrylabel(d, g(63.5, 41.4), "O‘ZBEKISTON", a, 48)
    else:
        a = fadein_alpha(t, 4.4)
        countrylabel(d, g(67.2, 42.3), "QOZOG‘ISTON", a, 46); countrylabel(d, g(67.4, 40.75), "O‘ZBEKISTON", a, 42)
        text(d, g(68.8, 42.35), "Turkiston viloyati", F("b", 36), fill=AMBER, anchor="mm", alpha=fadein_alpha(t, 5.0))
        citylabel(d, g(*TASH), "Toshkent", fadein_alpha(t, 5.3)); citylabel(d, g(*SHYM), "Shimkent", fadein_alpha(t, 5.5))
        pin(d, g(*YALL), "Chegara posti", t, 5.8, side="l")
    lower_third(d, t, "IJTIMOIY TARMOQLARDA", "Tarqalgan video ko‘pchilikni hayratga soldi", 5.0) if t > 5.0 else None
    bug(d); credit(d, MAPCR)
    return comp(im, L)

# -- S4 customs normal 20.2-26.1
def s_customs(t, D):
    im, cr = photo(CUS, t / D, 1.0, 1.1)
    out = quote_card(im, t, "Vaziyat — «normal holat»", "O‘zbekiston Bojxona qo‘mitasi", "Rasmiy baho", 0.3, size=78)
    L, d = layer(); bug(d); credit(d, cr); return comp(out, L)

# -- S5 questions 26.1-36.4
def s_questions(t, D):
    im, cr = photo(MAZ, t / D, 1.1, 1.0)
    im = darken(im, 0.5)
    L, d = layer()
    qs = [("Kim haq?", 0.2), ("Chegarada aslida nima bo‘lyapti?", 1.6), ("Bozordagi narxlarga aloqasi bormi?", 3.3)]
    for i, (q, a0) in enumerate(qs):
        a = fadein_alpha(t, a0, 0.5); x = int(lerp(140, 160, eo(prog(t, a0, a0 + 0.6))))
        d.rectangle([x - 40, 330 + i * 150, x - 28, 410 + i * 150], fill=RED + (a,))
        text(d, (x, 335 + i * 150), q, F("black", 72), alpha=a)
    a = fadein_alpha(t, 7.5)
    text(d, (160, 820), "FAKTLARNI BIRMA-BIR KO‘RIB CHIQAMIZ", F("b", 36), fill=AMBER, alpha=a)
    bug(d); credit(d, cr); return comp(im, L)

# -- S6 map checkpoint 36.4-48.8
def s_map2(t, D):
    p = eio(prog(t, 0, 3.0))
    cam = (lerp(68.8, 68.9, p), lerp(41.6, 41.0, p), lerp(5.0, 2.4, p))
    im, g = mapview("close", cam, hl_alpha=0.6)
    L, d = layer()
    countrylabel(d, g(68.35, 41.3), "QOZOG‘ISTON", 200, 40); countrylabel(d, g(69.15, 40.8), "O‘ZBEKISTON", 200, 40)
    citylabel(d, g(*TASH), "Toshkent", 230)
    pin(d, g(*YALL), "«B. Konisbayev»", t, 2.6, side="l", sub="Qozog‘iston tomoni")
    a = fadein_alpha(t, 5.3)
    if a:
        x, y = g(*YALL); text(d, (x + 30, y + 70), "«Yallama»", F("b", 36), anchor="lm", alpha=a)
        text(d, (x + 30, y + 112), "O‘zbekiston tomoni", F("m", 24), fill=GREY, anchor="lm", alpha=a)
    lower_third(d, t, "YUK YO‘LAGI", "Ikki davlat o‘rtasidagi eng gavjum yo‘laklardan biri", 8.3)
    bug(d); credit(d, MAPCR + " · post joylashuvi taxminiy")
    return comp(im, L)

# -- S7 queue breakdown 48.8-71.6
def s_breakdown(t, D):
    im, cr = photo(DAWN, t / D, 1.0, 1.1)
    im = darken(im, 0.72)
    L, d = layer()
    text(d, (140, 200), "13-NOYABR, SOAT 08:00", F("b", 34), fill=AMBER, alpha=fadein_alpha(t, 0.3))
    text(d, (140, 250), "Navbatdagi yuk mashinalari — rasmiy hisob", F("xb", 56), alpha=fadein_alpha(t, 0.5))
    parts = [(100, "postning o‘zida", 12.1, RED), (170, "maxsus to‘xtash joyida", 13.9, AMBER),
             (350, "to‘xtash joyidan oldin", 16.8, BLUE), (370, "Shardara tomon yo‘l bo‘ylab", 19.6, GREY)]
    x0, y0, tot = 140, 420, 1640
    x = x0
    for v, lab, a0, col in parts:
        w_ = tot * v / 990; pw = w_ * eo(prog(t, a0, a0 + 0.8))
        d.rectangle([x, y0, x + pw, y0 + 120], fill=col + (255,))
        a = fadein_alpha(t, a0 + 0.3)
        text(d, (x + 18, y0 + 60), str(v), F("black", 60), anchor="lm", alpha=a, fill=NAVY if col in (AMBER, GREY) else WHITE, shadow=False)
        # labels alternate below
        ly = y0 + 160 + (0 if parts.index((v, lab, a0, col)) % 2 == 0 else 60)
        d.line([x + 20, y0 + 122, x + 20, ly], fill=col + (a,), width=3)
        text(d, (x + 30, ly), lab, F("sb", 30), alpha=a)
        x += w_
    a = fadein_alpha(t, 21.0)
    text(d, (x0 + tot, 330), "JAMI: 990", F("black", 64), anchor="rs", fill=WHITE, alpha=fadein_alpha(t, 1.0))
    text(d, (140, 920), "Manba: Qozog‘iston Davlat daromadlari qo‘mitasi (Turkiston viloyati) · Kazinform orqali",
         F("m", 26), fill=GREY, alpha=fadein_alpha(t, 1.0))
    bug(d); credit(d, cr); return comp(im, L)

# -- S8 40 km vs 990 71.6-78.3
def s_versus(t, D):
    im, cr = photo(JOD1, t / D, 1.05, 1.15, 0.4, 0.5, 0.55, 0.5)
    im = darken(im, 0.55)
    L, d = layer()
    for i, (big, lab, src, a0) in enumerate([("40 km", "navbat uzunligi", "HAYDOVCHILAR HISOBI", 0.2), ("990", "yuk mashinasi", "RASMIY TASDIQLANGAN", 2.6)]):
        cx = 520 + i * 880; a = fadein_alpha(t, a0)
        text(d, (cx, 470), big, F("black", 170), anchor="mm", alpha=a)
        text(d, (cx, 590), lab, F("sb", 40), fill=GREY, anchor="mm", alpha=a)
        col = AMBER if i == 0 else GREEN
        if a: d.rectangle([cx - 240, 650, cx + 240, 710], fill=col + (a,)); text(d, (cx, 680), src, F("b", 30), fill=NAVY, anchor="mm", alpha=a, shadow=False)
    d.line([W // 2, 360, W // 2, 720], fill=(255, 255, 255, 90), width=2)
    bug(d); credit(d, cr + "  |  Arxiv surat"); return comp(im, L)

# -- S9 timeline 3 Nov 78.3-95.0
def s_early(t, D):
    if t < 11.0:
        im, cr = photo(STEP, t / 11.0, 1.0, 1.12)
    else:
        im, cr = photo(DAWN, (t - 11) / (D - 11), 1.12, 1.0)
    im = darken(im, 0.35)
    L, d = layer()
    # timeline bar
    a = fadein_alpha(t, 0.2)
    d.line([140, 300, 1780, 300], fill=(255, 255, 255, int(a * 0.5)), width=4)
    marks = [(0.08, "3-noyabr", "≈25 km · 3 kungacha kutish", 2.4), (0.5, "13-noyabr", "990 fura · ≈40 km", 5.0), (0.92, "20-noyabr", "100 fura", 7.5)]
    for fx, dt, info, a0 in marks:
        x = 140 + 1640 * fx; aa = fadein_alpha(t, a0)
        d.ellipse([x - 14, 286, x + 14, 314], fill=(RED if dt == "3-noyabr" else WHITE) + (aa,))
        text(d, (x, 260), dt, F("b", 36), anchor="ms", alpha=aa)
        text(d, (x, 360), info, F("sb", 30), fill=GREY, anchor="mt", alpha=aa)
    if t > 11.0:
        lower_third(d, t, "QOZOG‘ISTON NASHRLARI", "Yo‘l bo‘yida hojatxona va oddiy sharoitlar yo‘q", 11.2, "Haydovchilar shikoyati · Kursiv / Kazinform")
    else:
        lower_third(d, t, "NOYABR BOSHI", "Haydovchilar: 25 km navbat", 1.0)
    bug(d); credit(d, cr); return comp(im, L)

# -- S10 why 95-100
def s_why(t, D):
    im, cr = photo(ISS, t / D, 1.0, 1.15)
    out = title_card(im, t, "ENG MUHIM SAVOL", "NEGA?", "Javob — raqamlarda")
    L, d = layer(); bug(d); credit(d, cr); return comp(out, L)

# -- S11 capacity 100-111
def s_capacity(t, D):
    im, cr = photo(QAP2, t / D, 1.0, 1.08)
    im = darken(im, 0.68)
    L, d = layer()
    text(d, (140, 220), "«KONISBAYEV» POSTI · KUNLIK QUVVAT", F("b", 36), fill=AMBER, alpha=fadein_alpha(t, 0.2))
    for i, (v, lab, a0, col) in enumerate([(1000, "Loyiha bo‘yicha", 0.6, BLUE), (1500, "Amalda (gacha)", 4.2, RED)]):
        y = 380 + i * 220; wmax = 1100 * v / 1500
        pw = wmax * eo(prog(t, a0, a0 + 1.2)); a = fadein_alpha(t, a0)
        text(d, (140, y - 50), lab, F("sb", 36), alpha=a)
        d.rectangle([140, y, 140 + pw, y + 110], fill=col + (a,))
        big_number(d, (160 + pw + 20, y + 55), v, t, a0, a0 + 1.2, f=F("black", 80), anchor="lm", suffix=" ta")
    a = fadein_alpha(t, 7.3)
    if a:
        d.rectangle([1380, 700, 1780, 860], fill=RED + (a,))
        text(d, (1580, 780), "+50%", F("black", 110), anchor="mm", alpha=a, shadow=False)
    text(d, (140, 930), "Manba: Qozog‘iston DDQ · Kazinform / Kursiv", F("m", 26), fill=GREY, alpha=fadein_alpha(t, 0.5))
    bug(d); credit(d, cr + " · Kaplanbek o‘tish joyi"); return comp(im, L)

# -- S12 growth 111-128
def s_growth(t, D):
    im, cr = photo(HOWOT, t / D, 1.0, 1.1)
    im = darken(im, 0.7)
    L, d = layer()
    text(d, (140, 200), "IKKI DAVLAT CHEGARASIDAN KUNIGA O‘TADIGAN YUK MASHINALARI", F("b", 34), fill=AMBER, alpha=fadein_alpha(t, 0.2))
    base = 880
    for i, (yr, v, a0) in enumerate([("2021", 1165, 3.5), ("2026, noyabr", 3130, 9.5)]):
        x = 420 + i * 560; hmax = 440 * v / 3130; ph = hmax * eo(prog(t, a0, a0 + 1.4)); a = fadein_alpha(t, a0)
        d.rectangle([x, base - ph, x + 300, base], fill=(BLUE if i == 0 else RED) + (a,))
        big_number(d, (x + 150, base - ph - 60), v, t, a0, a0 + 1.4, f=F("black", 76))
        text(d, (x + 150, base + 50), yr, F("b", 36), anchor="mm", alpha=a)
    a = fadein_alpha(t, 13.6)
    if a:
        d.rectangle([1440, 420, 1780, 600], fill=AMBER + (a,))
        text(d, (1610, 490), "×2,7", F("black", 110), fill=NAVY, anchor="mm", alpha=a, shadow=False)
        text(d, (1610, 570), "5 yilda", F("b", 34), fill=NAVY, anchor="mm", alpha=a, shadow=False)
    text(d, (140, 990), "Manba: O‘zbekiston Bojxona qo‘mitasi", F("m", 26), fill=GREY, alpha=fadein_alpha(t, 0.5))
    bug(d); credit(d, cr); return comp(im, L)

# -- S13 transit 128-134.6
def s_transit(t, D):
    im, cr = photo(HOWOK, t / D, 1.12, 1.0)
    def ex(d):
        lower_third(d, t, "TRANZIT", "Yuklarning katta qismi O‘zbekiston orqali boshqa davlatlarga", 0.3)
    return with_credit(im, cr, t, ex)

# -- S14 flows map 134.6-153
def s_flows(t, D):
    cam = (59, 46, 58)
    im, g = mapview("wide", cam)
    L, d = layer()
    countrylabel(d, g(67, 48), "QOZOG‘ISTON", 230, 40); countrylabel(d, g(63.5, 41.3), "O‘ZBEKISTON", 230, 30)
    tgt = g(68.8, 41.2)
    flows = [("XITOY", (84.0, 43.5), 1.4, 0.18), ("ROSSIYA", (37.6, 55.75), 3.8, -0.15), ("BELARUS", (31.5, 53.6), 4.6, -0.12)]
    for lab, src, a0, bend in flows:
        p = eio(prog(t, a0, a0 + 1.6)); s = g(*src)
        arrow(d, curve(s, tgt, bend), p, col=AMBER if lab == "XITOY" else BLUE, width=9)
        if lab == "XITOY": text(d, (s[0], s[1] - 40), lab, F("b", 34), anchor="mm", alpha=fadein_alpha(t, a0))
        else: text(d, (max(s[0], 20) + 20, s[1] + 40), lab, F("b", 34), anchor="lm", alpha=fadein_alpha(t, a0))
    pin(d, tgt, "Chegara", t, 1.0, side="r", size=28)
    reasons = [("Mavsumiy o‘sish", 8.5), ("To‘xtash joylari kunlik hajmga yetmaydi", 10.4), ("Elektron navbat oldindan band qilinmagan", 14.5)]
    for i, (r, a0) in enumerate(reasons):
        a = fadein_alpha(t, a0); y = 700 + i * 80
        if a:
            d.rectangle([80, y, 880, y + 64], fill=(9, 16, 28, int(a * 0.88)))
            d.rectangle([80, y, 90, y + 64], fill=RED + (a,))
            text(d, (110, y + 32), r, F("sb", 32), anchor="lm", alpha=a, shadow=False)
    text(d, (80, 650), "QOZOG‘ISTON TOMONI KELTIRGAN SABABLAR", F("b", 28), fill=AMBER, alpha=fadein_alpha(t, 8.0))
    bug(d); credit(d, MAPCR + " · yo‘nalishlar sxematik"); return comp(im, L)

# -- S15 Iran corridor 153-167.6
def s_iran(t, D):
    cam = (lerp(61, 62, eio(prog(t, 0, D))), 39.0, 32)
    im, g = mapview("wide", cam)
    L, d = layer()
    for lab, xy in [("ERON", (57.5, 35.6)), ("TURKMANISTON", (58.8, 39.4)), ("O‘ZBEKISTON", (63.6, 41.5)), ("QOZOG‘ISTON", (67, 44.6))]:
        countrylabel(d, g(*xy), lab, 230, 34)
    pts = [g(53.0, 34.5), g(58.3, 37.9), g(61.5, 40.0), g(65.5, 40.3), g(68.8, 41.2), g(69.6, 43.0)]
    arrow(d, pts, eio(prog(t, 2.2, 7.5)), col=RED, width=11)
    text(d, (140, 250), "JANUBIY YO‘LAK", F("black", 64), alpha=fadein_alpha(t, 2.0))
    text(d, (140, 320), "Eron yuklarining bir qismi yangi yo‘nalishda", F("sb", 36), fill=GREY, alpha=fadein_alpha(t, 2.4))
    if t < 6.5: lower_third(d, t, "KUN.UZ", "Qozog‘iston rasmiylari ma’lumotiga ko‘ra", 0.3)
    else: text(d, (140, 400), "Manba: Kun.uz — Qozog‘iston rasmiylari ma’lumotiga ko‘ra", F("m", 28), fill=GREY, alpha=fadein_alpha(t, 6.5))
    bug(d); credit(d, MAPCR + " · yo‘nalish sxematik"); return comp(im, L)

# -- S16 Khorgos 167.6-178.4
def s_khorgos(t, D):
    im, cr = photo(KHN, t / D, 1.0, 1.12, 0.5, 0.55, 0.5, 0.5)
    def ex(d):
        lower_third(d, t, "XORGOS · XITOY–QOZOG‘ISTON", "Post kecha-kunduz ishlay boshlagan", 0.4, "O‘zbekiston Bojxona qo‘mitasi ma’lumoti")
        a = fadein_alpha(t, 3.5)
        if a:
            d.rectangle([1560, 140, 1840, 270], fill=RED + (a,))
            text(d, (1700, 205), "24/7", F("black", 90), anchor="mm", alpha=a, shadow=False)
    return with_credit(im, cr, t, ex)

# -- S17 20 Nov & quote 178.4-199.3
def s_nov20(t, D):
    im, cr = photo(CUS, t / D, 1.1, 1.0)
    if t < 8.3:
        im = darken(im.filter(ImageFilter.GaussianBlur(18)), 0.6)
        L, d = layer()
        text(d, (W // 2, 330), "20-NOYABR, SOAT 09:00", F("b", 40), fill=AMBER, anchor="mm", alpha=fadein_alpha(t, 2.6))
        big_number(d, (W // 2, 520), 100, t, 3.0, 4.6, f=F("black", 240))
        text(d, (W // 2, 680), "ta yuk mashinasi navbatda", F("sb", 48), anchor="mm", alpha=fadein_alpha(t, 4.0))
        text(d, (W // 2, 760), "«Konisbayev» posti oldida", F("m", 34), fill=GREY, anchor="mm", alpha=fadein_alpha(t, 4.4))
        bug(d); credit(d, cr); return comp(im, L)
    out = quote_card(im, t, "Bu normal holat hisoblanadi", "Husan Tangriyev", "O‘zbekiston Bojxona qo‘mitasi vakili", 8.6, size=82)
    L, d = layer()
    a = fadein_alpha(t, 15.3)
    text(d, (260, 860), "Kuniga 1 500 dan ortiq mashina o‘tadigan yo‘nalishda 100 ta fura — odatiy hol", F("sb", 32), fill=AMBER, alpha=a)
    bug(d); credit(d, cr); return comp(out, L)

# -- S18 compare 199.3-210
def s_compare(t, D):
    im, cr = photo(QAP1, t / D, 1.0, 1.1)
    im = darken(im, 0.7)
    L, d = layer()
    text(d, (W // 2, 210), "IKKALA RAQAM HAM TO‘G‘RI — TURLI KUNLAR", F("b", 38), fill=AMBER, anchor="mm", alpha=fadein_alpha(t, 0.3))
    base = 860
    for i, (lab, v, a0, col) in enumerate([("13-noyabr", 990, 3.6, RED), ("20-noyabr", 100, 7.0, GREEN)]):
        x = 560 + i * 520; hmax = 520 * v / 990; ph = hmax * eo(prog(t, a0, a0 + 1.0)); a = fadein_alpha(t, a0)
        d.rectangle([x, base - ph, x + 280, base], fill=col + (a,))
        big_number(d, (x + 140, base - ph - 55), v, t, a0, a0 + 1.0, f=F("black", 72))
        text(d, (x + 140, base + 45), lab, F("b", 36), anchor="mm", alpha=a)
    bug(d); credit(d, cr + " · Kaplanbek o‘tish joyi"); return comp(im, L)

# -- S19 root 210-225.5
def s_root(t, D):
    im, cr = photo(HOWOT, t / D, 1.15, 1.0, 0.55, 0.5, 0.45, 0.5)
    L, d = layer()
    L.alpha_composite(dark(0.45))
    text(d, (140, 380), "MUAMMONING ILDIZI", F("b", 38), fill=AMBER, alpha=fadein_alpha(t, 0.3))
    text(d, (140, 440), "bitta postdagi navbat emas", F("xb", 64), alpha=fadein_alpha(t, 4.0))
    a = fadein_alpha(t, 8.6)
    text(d, (140, 560), "O‘zbekiston — tranzit yo‘lakka aylanmoqda", F("black", 66), alpha=a)
    text(d, (140, 660), "Chegara infratuzilmasi bu tezlikka yetisha olmayapti", F("sb", 40), fill=GREY, alpha=fadein_alpha(t, 11.8))
    bug(d); credit(d, cr); return comp(im, L)

# -- S20 national stats 225.5-242.6
def s_national(t, D):
    im, cr = photo(HOWO, t / D, 1.0, 1.1)
    im = darken(im, 0.72)
    L, d = layer()
    text(d, (140, 200), "O‘ZBEKISTONNING BARCHA CHEGARALARI · KUNIGA YUK MASHINALARI", F("b", 32), fill=AMBER, alpha=fadein_alpha(t, 0.2))
    a = fadein_alpha(t, 4.4)
    if a:
        d.rectangle([140, 300, 640, 470], fill=RED + (a,))
        text(d, (390, 385), "+70%", F("black", 120), anchor="mm", alpha=a, shadow=False)
        text(d, (390, 510), "3 yilda", F("b", 36), anchor="mm", alpha=a)
    base = 880
    for i, (lab, v, a0, col) in enumerate([("Hozir", 5100, 8.4, BLUE), ("2030 maqsad", 10500, 12.0, AMBER)]):
        x = 860 + i * 480; hmax = 560 * v / 10500; ph = hmax * eo(prog(t, a0, a0 + 1.3)); aa = fadein_alpha(t, a0)
        d.rectangle([x, base - ph, x + 280, base], fill=col + (aa,))
        big_number(d, (x + 140, base - ph - 55), v, t, a0, a0 + 1.3, f=F("black", 68), suffix="+" if i == 0 else "")
        text(d, (x + 140, base + 45), lab, F("b", 34), anchor="mm", alpha=aa)
    text(d, (140, 990), "Manba: O‘zbekiston Bojxona qo‘mitasi · Gazeta.uz, 14.11.2026", F("m", 26), fill=GREY, alpha=fadein_alpha(t, 0.5))
    bug(d); credit(d, cr); return comp(im, L)

# -- S21 opportunity 242.6-250.9
def s_opportunity(t, D):
    im, cr = photo(TSK, t / D, 1.0, 1.12)
    L, d = layer(); L.alpha_composite(dark(0.4))
    text(d, (W // 2, 330), "KATTA IMKONIYAT", F("black", 90), anchor="mm", alpha=fadein_alpha(t, 0.2))
    for i, (s, a0) in enumerate([("Ish o‘rinlari", 2.4), ("Logistika markazlari", 4.2), ("Byudjetga daromad", 5.5)]):
        a = fadein_alpha(t, a0); x = 360 + i * 600
        if a:
            d.rectangle([x - 270, 520, x + 270, 640], fill=(9, 16, 28, int(a * 0.85)))
            d.rectangle([x - 270, 520, x - 260, 640], fill=GREEN + (a,))
            text(d, (x, 580), s, F("b", 40), anchor="mm", alpha=a, shadow=False)
    bug(d); credit(d, cr); return comp(im, L)

# -- S22 cost 250.9-266.6
def s_cost(t, D):
    im, cr = photo(MAZ, t / D, 1.0, 1.12)
    def ex(d):
        if t < 7.6:
            lower_third(d, t, "XARAJAT", "Chegarada turgan har bir kun — qo‘shimcha xarajat", 0.3, "Yuk narxiga qo‘shilishi mumkin")
        else:
            lower_third(d, t, "NARXLARGA TA’SIRI", "Rasmiy baho hozircha yo‘q", 7.7, "Savol ochiq qolmoqda")
    return with_credit(im, cr, t, ex)

# -- S23 what next 266.6-270
def s_next(t, D):
    im, cr = photo(ISS, t / D, 1.15, 1.0)
    out = title_card(im, t, "ASOSIY SAVOL", "KEYIN NIMA BO‘LADI?")
    L, d = layer(); bug(d); credit(d, cr); return comp(out, L)

# -- S24 G'ishtko'prik 270-301.6
def s_gisht(t, D):
    if t < 8.5:
        p = eio(prog(t, 0, 3))
        im, g = mapview("close", (lerp(68.9, 69.2, p), lerp(41.2, 41.38, p), lerp(2.6, 1.4, p)))
        L, d = layer()
        citylabel(d, g(*TASH), "Toshkent", 240, 32)
        countrylabel(d, g(68.85, 41.52), "QOZOG‘ISTON", 200, 36); countrylabel(d, g(69.5, 41.22), "O‘ZBEKISTON", 200, 36)
        pin(d, g(*GISHT), "G‘ishtko‘prik", t, 2.2, side="l", sub="Qozog‘istonda: Chernyayevka")
        text(d, (140, 830), "BUGUN, 23-NOYABR", F("b", 34), fill=AMBER, alpha=fadein_alpha(t, 0.3))
        text(d, (140, 880), "Post 25-noyabrda qayta ochiladi", F("black", 60), alpha=fadein_alpha(t, 0.6))
        bug(d); credit(d, MAPCR + " · post joylashuvi taxminiy"); return comp(im, L)
    im, cr = photo(ZZB, (t - 8.5) / (D - 8.5), 1.0, 1.12)
    L, d = layer()
    L.alpha_composite(Image.new("RGBA", (W, H), (9, 16, 28, 0)))
    tl = [("2025-fevral", "Ta’mir uchun yopildi", 12.2, RED), ("Reja: 4 oy", "", 15.8, GREY), ("Amalda: ≈20 oy", "", 18.6, AMBER), ("25-noyabr, 16:00", "Fuqarolar uchun ochiladi", 21.5, GREEN)]
    d.rectangle([0, 150, W, 330], fill=(9, 16, 28, int(fadein_alpha(t, 12.0) * 0.82)))
    for i, (a_, b_, a0, col) in enumerate(tl):
        x = 140 + i * 430; a = fadein_alpha(t, a0)
        d.rectangle([x, 180, x + 8, 300], fill=col + (a,))
        text(d, (x + 24, 190), a_, F("black", 40), alpha=a, shadow=False)
        if b_: text(d, (x + 24, 250), b_, F("m", 28), fill=GREY, alpha=a, shadow=False)
    if t > 28.0:
        lower_third(d, t, "SPOT.UZ", "Yuk mashinalari qachondan o‘tishi aniq aytilmagan", 28.1)
    else:
        lower_third(d, t, "JIBEK JOLI – G‘ISHTKO‘PRIK", "Shu o‘tish joyi (2024-yil surati)", 8.8)
    bug(d); credit(d, cr); return comp(im, L)

# -- S25 measures 301.6-324.5
def s_measures(t, D):
    im, cr = photo(QAP1, t / D, 1.12, 1.0, 0.45, 0.5, 0.55, 0.5)
    L, d = layer(); L.alpha_composite(dark(0.5))
    items = [("Furalar bir nechta postga taqsimlanmoqda", "«Atameken», «Qazig‘urt» va boshqalar", 0.8),
             ("2 ta post — kecha-kunduz", "Ikki davlat kelishuvi", 7.3),
             ("+100–150 fura/kun", "Ta’mirdan keyin yangi yo‘nalish · Qozog‘iston tomoni", 11.6),
             ("Dovut-ota posti — dekabrda", "Kutilmoqda", 20.0)]
    text(d, (140, 190), "CHORALAR", F("b", 36), fill=AMBER, alpha=fadein_alpha(t, 0.2))
    for i, (h, s, a0) in enumerate(items):
        a = fadein_alpha(t, a0); y = 270 + i * 175; x = int(lerp(100, 140, eo(prog(t, a0, a0 + 0.6))))
        if a:
            d.rectangle([x, y, x + 10, y + 130], fill=RED + (a,))
            text(d, (x + 36, y + 10), h, F("black", 54), alpha=a)
            text(d, (x + 36, y + 80), s, F("m", 30), fill=GREY, alpha=a)
    bug(d); credit(d, cr + " · Kaplanbek o‘tish joyi"); return comp(im, L)

# -- S26 One Stop 324.5-351
def s_onestop(t, D):
    if t >= 17.8:
        im, cr = photo(CUS, (t - 17.8) / (D - 17.8), 1.0, 1.08)
        out = quote_card(im, t, "Bu faqat O‘zbekistonning xohishi bilan hal etiladigan masala emas", "Farhod Olimjonov", "Bojxona qo‘mitasi vakili · Gazeta.uz, 14.11.2026", 17.9, size=60)
        L, d = layer(); bug(d); credit(d, cr); return comp(out, L)
    im, cr = photo(ZZS, t / 17.8, 1.0, 1.1)
    im = darken(im, 0.72)
    L, d = layer()
    text(d, (W // 2, 200), "«ONE STOP» — YAGONA NAZORAT", F("black", 70), anchor="mm", alpha=fadein_alpha(t, 0.4))
    # before: two booths; after: one
    p = eio(prog(t, 7.0, 9.0))
    a = fadein_alpha(t, 1.5)
    labels = ["Qozog‘iston bojxonasi", "O‘zbekiston bojxonasi"]
    for i in range(2):
        x = lerp(560 + i * 800, 960, p) - 220
        d.rounded_rectangle([x, 420, x + 440, 640], 24, fill=((BLUE if i == 0 else GREEN) + (int(a * (1 - 0.5 * p * i)),)))
        if p < 0.6: text(d, (x + 220, 530), labels[i], F("b", 34), anchor="mm", alpha=int(a * (1 - p / 0.6)), shadow=False)
    if p > 0.5:
        aa = int(255 * clamp((p - 0.5) * 2))
        text(d, (960, 530), "Bir joyda, bir marta", F("black", 40), anchor="mm", alpha=aa, shadow=False)
    a2 = fadein_alpha(t, 12.5)
    if a2:
        d.rectangle([710, 720, 1210, 840], fill=AMBER + (a2,))
        text(d, (960, 780), "≈2× tezroq", F("black", 64), fill=NAVY, anchor="mm", alpha=a2, shadow=False)
        text(d, (960, 885), "O‘zbekiston bojxonasi bahosi", F("m", 28), fill=GREY, anchor="mm", alpha=a2)
    bug(d); credit(d, cr); return comp(im, L)

# -- S27 conclusion 351-371.6
def s_conclusion(t, D):
    im, cr = photo(JOD1, t / D, 1.0, 1.2, 0.5, 0.5, 0.6, 0.55)
    L, d = layer(); L.alpha_composite(dark(0.5))
    text(d, (140, 260), "XULOSA", F("b", 36), fill=AMBER, alpha=fadein_alpha(t, 0.3))
    text(d, (140, 310), "40 km navbat — tasodif emas", F("black", 72), alpha=fadein_alpha(t, 1.0))
    for i, (s, a0) in enumerate([("Yo‘llar kengayishi", 11.6), ("Postlar ko‘payishi", 13.4), ("Yagona bojxona tizimi", 14.6)]):
        a = fadein_alpha(t, a0); y = 480 + i * 120
        if a:
            d.ellipse([140, y + 12, 176, y + 48], fill=GREEN + (a,))
            text(d, (200, y + 30), s, F("xb", 52), anchor="lm", alpha=a)
    a = fadein_alpha(t, 18.2)
    text(d, (140, 880), "Aks holda bu manzara yana takrorlanishi mumkin", F("sb", 38), fill=AMBER, alpha=a)
    bug(d); credit(d, cr + "  |  Arxiv surat"); return comp(im, L)

# -- S28 CTA 371.6-383.25
def s_cta(t, D):
    im, cr = photo(TSN, t / D, 1.0, 1.1)
    L, d = layer(); L.alpha_composite(dark(0.6))
    text(d, (W // 2, 330), "SAVOL SIZGA", F("b", 40), fill=AMBER, anchor="mm", alpha=fadein_alpha(t, 0.2))
    lines = ["O‘zbekiston haqiqiy tranzit", "markaziga aylanishga tayyormi?"]
    for i, ln in enumerate(lines):
        text(d, (W // 2, 440 + i * 100), ln, F("black", 80), anchor="mm", alpha=fadein_alpha(t, 0.5 + 0.2 * i))
    a = fadein_alpha(t, 9.6)
    if a:
        d.rounded_rectangle([W // 2 - 380, 720, W // 2 + 380, 820], 50, fill=RED + (a,))
        text(d, (W // 2, 770), "Fikringizni izohlarda yozing", F("b", 40), anchor="mm", alpha=a, shadow=False)
    fo = int(255 * eio(prog(t, D - 1.0, D)))
    if fo: L.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, fo)))
    bug(d) if fo < 128 else None; credit(d, cr)
    return comp(im, L)

SCENES = [
 (0.0, 6.6, s_hook), (6.6, 11.3, s_drivers), (11.3, 20.2, s_map1), (20.2, 26.1, s_customs), (26.1, 36.4, s_questions),
 (36.4, 48.8, s_map2), (48.8, 71.6, s_breakdown), (71.6, 78.3, s_versus), (78.3, 95.0, s_early), (95.0, 100.0, s_why),
 (100.0, 111.0, s_capacity), (111.0, 128.0, s_growth), (128.0, 134.6, s_transit), (134.6, 153.0, s_flows), (153.0, 167.6, s_iran),
 (167.6, 178.4, s_khorgos), (178.4, 199.3, s_nov20), (199.3, 210.0, s_compare), (210.0, 225.5, s_root), (225.5, 242.6, s_national),
 (242.6, 250.9, s_opportunity), (250.9, 266.6, s_cost), (266.6, 270.0, s_next), (270.0, 301.6, s_gisht), (301.6, 324.5, s_measures),
 (324.5, 351.0, s_onestop), (351.0, 371.6, s_conclusion), (371.6, DUR, s_cta)]
XF = 0.35

def frame_at(T):
    for i, (a, b, fn) in enumerate(SCENES):
        if a <= T < b or (i == len(SCENES) - 1 and T >= a):
            cur = fn(T - a, b - a)
            if i > 0 and T - a < XF:
                pa, pb, pfn = SCENES[i - 1]
                prev = pfn(T - pa, pb - pa)
                cur = Image.blend(prev, cur, eio((T - a) / XF))
            return cur
    return Image.new("RGB", (W, H))

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still":
        for T in map(float, sys.argv[3:]):
            frame_at(T).save(f"{sys.argv[2]}/still_{T:07.2f}.jpg", quality=88)
    else:  # segment render: start end outfile
        t0, t1, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        n0, n1 = int(round(t0 * FPS)), int(round(t1 * FPS))
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-g", "50", out], stdin=subprocess.PIPE)
        for n in range(n0, n1):
            p.stdin.write(frame_at(n / FPS).tobytes())
        p.stdin.close(); p.wait()
