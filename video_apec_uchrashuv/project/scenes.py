"""Storyboard: every scene = start time, plate builder, overlays, source credit, transition."""
import os
from engine import *

ROOT = os.path.dirname(os.path.abspath(__file__))
_rows = [l.rstrip("\n").split("\t") for l in open(os.path.join(ROOT, "kremlin/photos_ok.tsv"))]


def P(i):
    return os.path.join(ROOT, "media/kremlin", _rows[i][1].split("/")[-1])


def M(*p):
    return os.path.join(ROOT, "media", *p)


def have(p):
    return os.path.exists(p) and os.path.getsize(p) > 10000


KR_F = "FOTO: Kremlin.ru · CC BY 4.0"
KR_V = "VIDEO: Kremlin.ru · CC BY 4.0"
ARCH_KR = "ARXIV VIDEO: Kremlin.ru, 15.08.2025 · CC BY 4.0"
BRAVO = "ARXIV: AQSH Energetika vazirligi, 1954 · Wikimedia Commons (public domain)"
NASA = "FOTO: NASA / XKS ekipaji (public domain)"
NAVY_V = "VIDEO: AQSH Dengiz kuchlari (NAVCENT) · Wikimedia Commons (public domain)"
UNSC = "FOTO: Jdforrester · Wikimedia Commons · CC BY 4.0"
GFX = ""  # own graphics
MAPSRC = "XARITA: Natural Earth (public domain)"

S = []  # scenes


def scene(t0, plate, ov=None, cr="", tr="cut", ticker_on=True, label=""):
    S.append(dict(t0=t0, plate=plate, ov=ov or [], cr=cr, tr=tr, tk=ticker_on, label=label))


# ---------------- plate builders (return callable(lt,dur,ctx)->Image)
def photo(i_or_path, z0=1.0, z1=1.12, c0=(0.5, 0.5), c1=(0.5, 0.5), bf=True):
    path = P(i_or_path) if isinstance(i_or_path, int) else i_or_path
    return lambda lt, dur, ctx: grade(kenburns(path, lt / dur, z0, z1, c0, c1, blurfill=bf))


def seq(*parts):
    """parts: (rel_start, plate) — switch plates within one scene (hard cuts)."""
    def f(lt, dur, ctx):
        cur = None; st = 0; en = dur
        for k, (s, p) in enumerate(parts):
            if lt >= s:
                cur = p; st = s; en = parts[k + 1][0] if k + 1 < len(parts) else dur
        img = cur(lt - st, en - st, ctx)
        if lt - st < 0.12 and st > 0:
            img = whip(img, lt - st, 0.12)
        return img
    return f


def video(path, start, speed=1.0, gr=True, zoom=None, center=(0.5, 0.5)):
    def f(lt, dur, ctx):
        key = ("v", path, start)
        if key not in ctx:
            ctx[key] = VideoPlate(path, start, dur + 0.5, speed)
        img = ctx[key].frame()
        if zoom:
            z = lerp(zoom[0], zoom[1], lt / dur)
            w, h = W / z, H / z
            x0 = min(max(center[0] * W - w / 2, 0), W - w); y0 = min(max(center[1] * H - h / 2, 0), H - h)
            img = img.transform((W, H), Image.AFFINE, (1 / z, 0, x0, 0, 1 / z, y0), resample=Image.BILINEAR)
        return grade(img) if gr else img
    return f


def gbg(lt, dur, ctx):
    return news_bg(ctx.get("gt", 0))


def maplate(v0, v1, hl=None, pins=(), arcs=(), dimp=None):
    def f(lt, dur, ctx):
        p = min(1, lt / max(0.1, dur * 0.7))
        v = view_lerp(v0, v1, p)
        img = draw_map(v, hl)
        for (lon, lat, lab, t_on, *rest) in pins:
            if lt >= t_on:
                pin(img, v, lon, lat, lab, lt - t_on, side=rest[0] if rest else "r")
        for (a, b, t_on) in arcs:
            if lt >= t_on:
                arc(img, v, a, b, (lt - t_on) / 1.6)
        return grade(img, contrast=1.0, sat=1.0)
    return f


def blur_of(plate):
    return lambda lt, dur, ctx: blurred(plate(lt, dur, ctx), 16, 0.55)


# ---------------- overlay builders (callable(img,lt,dur)->None or Image)
def HL(s, t0=0.0, t1=None, **kw):
    return lambda img, lt, dur: headline(img, s, lt - t0, (t1 if t1 else dur) - t0, **kw)


def LT(title, sub, t0=0.2, t1=None, y=760):
    return lambda img, lt, dur: lower_third(img, title, sub, lt - t0, (t1 if t1 else dur) - t0, y)


def QC(q, who, t0=0.2, side="r"):
    return lambda img, lt, dur: quote_card(img, q, who, lt - t0, dur - t0, side)


def BUMP(title, sub=None, num=None):
    return lambda img, lt, dur: bumper(img, title, sub, lt, dur, num)


def CUSTOM(fn):
    return fn


# ---------------- custom graphics
def triptych(lt, dur, ctx):
    img = news_bg(ctx.get("gt", 0))
    items = [(9, "DONALD TRAMP", "AQSH", 0.55, (0.5, 0.35)), (3, "SI SZINPIN", "XITOY", 1.75, (0.5, 0.35)), (7, "VLADIMIR PUTIN", "ROSSIYA", 2.85, (0.5, 0.4))]
    pw = W // 3
    d = ImageDraw.Draw(img, "RGBA")
    for k, (i, nm, cty, ts, c) in enumerate(items):
        if lt < ts:
            continue
        a = eout((lt - ts) / 0.35)
        im = load_photo(P(i)); iw, ih = im.size
        s = max(pw / iw, H / ih) * lerp(1.25, 1.1, eout((lt - ts) / 3))
        vw, vh = pw / s, H / s
        x0 = min(max(c[0] * iw - vw / 2, 0), iw - vw); y0 = min(max(c[1] * ih - vh / 2, 0), ih - vh)
        tile = im.transform((pw, H), Image.AFFINE, (1 / s, 0, x0, 0, 1 / s, y0), resample=Image.BICUBIC)
        tile = grade(tile.resize((W, H))).resize((pw, H)) if False else tile
        yo = int((1 - a) * 120)
        img.paste(tile, (k * pw, yo))
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([k * pw, H - 300, (k + 1) * pw, H], fill=(0, 0, 0, 150))
        d.rectangle([k * pw, H - 300, (k + 1) * pw, H - 292], fill=RED)
        d.text((k * pw + pw / 2, H - 220), nm, font=font("InterDisplay-Black", 58), fill=WHITE, anchor="mm")
        d.text((k * pw + pw / 2, H - 155), cty, font=font("Inter-Bold", 34), fill=GOLD, anchor="mm")
        if k:
            d.rectangle([k * pw - 3, 0, k * pw + 3, H], fill=WHITE)
    return grade(img, 1.03, 0.97)


def flag(d, kind, x, y, w, h):
    if kind == "RU":
        for i, c in enumerate([(255, 255, 255), (0, 57, 166), (213, 43, 30)]):
            d.rectangle([x, y + i * h / 3, x + w, y + (i + 1) * h / 3], fill=c)
    elif kind == "CN":
        d.rectangle([x, y, x + w, y + h], fill=(222, 41, 16))
        star(d, x + w * 0.17, y + h * 0.27, h * 0.16, (255, 222, 0))
        for (u, v) in [(0.33, 0.1), (0.4, 0.2), (0.4, 0.35), (0.33, 0.45)]:
            star(d, x + w * u, y + h * v, h * 0.055, (255, 222, 0))
    elif kind == "US":
        for i in range(13):
            d.rectangle([x, y + i * h / 13, x + w, y + (i + 1) * h / 13], fill=(178, 34, 52) if i % 2 == 0 else (255, 255, 255))
        d.rectangle([x, y, x + w * 0.4, y + h * 7 / 13], fill=(60, 59, 110))
    elif kind == "GB":
        d.rectangle([x, y, x + w, y + h], fill=(1, 33, 105))
        d.line([x, y, x + w, y + h], fill=WHITE, width=int(h / 6)); d.line([x, y + h, x + w, y], fill=WHITE, width=int(h / 6))
        d.rectangle([x + w * 0.42, y, x + w * 0.58, y + h], fill=WHITE); d.rectangle([x, y + h * 0.38, x + w, y + h * 0.62], fill=WHITE)
        d.rectangle([x + w * 0.45, y, x + w * 0.55, y + h], fill=(200, 16, 46)); d.rectangle([x, y + h * 0.42, x + w, y + h * 0.58], fill=(200, 16, 46))
    elif kind == "FR":
        for i, c in enumerate([(0, 85, 164), (255, 255, 255), (239, 65, 53)]):
            d.rectangle([x + i * w / 3, y, x + (i + 1) * w / 3, y + h], fill=c)


def star(d, cx, cy, r, col):
    import math as m
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.4
        a = -m.pi / 2 + i * m.pi / 5
        pts.append((cx + rr * m.cos(a), cy + rr * m.sin(a)))
    d.polygon(pts, fill=col)


def p5(lt, dur, ctx):
    base = blurred(grade(kenburns(M("commons/unsc_chamber.jpg"), lt / dur, 1.0, 1.08)), 10, 0.6) if have(M("commons/unsc_chamber.jpg")) else news_bg(ctx.get("gt", 0))
    d = ImageDraw.Draw(base, "RGBA")
    d.text((W / 2, 170), "BMT XAVFSIZLIK KENGASHI — 5 DOIMIY AʼZO", font=font("InterDisplay-Black", 62), fill=WHITE, anchor="mm")
    items = [("US", "AQSH", True), ("RU", "ROSSIYA", True), ("CN", "XITOY", True), ("GB", "BUYUK BRITANIYA", False), ("FR", "FRANSIYA", False)]
    for k, (fk, nm, hi) in enumerate(items):
        ts = 0.3 + k * 0.25
        if lt < ts:
            continue
        a = eout((lt - ts) / 0.4)
        x = 160 + k * 330; y = 360 + (1 - a) * 60
        on = hi and lt > 3.2
        d.rounded_rectangle([x - 12, y - 12, x + 252, y + 330], 12, fill=(255, 255, 255, 40 if not on else 70), outline=(RED if on else (255, 255, 255, 80)), width=6 if on else 2)
        flag(d, fk, x + 16, y + 20, 208, 138)
        d.text((x + 120, y + 215), nm, font=font("Inter-Bold", 28 if len(nm) < 10 else 22), fill=WHITE, anchor="mm")
        if on:
            d.text((x + 120, y + 280), "YADROVIY", font=font("Inter-Black", 30), fill=GOLD, anchor="mm")
        elif lt > 3.2:
            d.rectangle([x - 12, y - 12, x + 252, y + 330], fill=(0, 0, 0, 120))
    return base


def timeline_newstart(lt, dur, ctx):
    img = news_bg(ctx.get("gt", 0))
    d = ImageDraw.Draw(img, "RGBA")
    d.text((120, 150), "NEW START (SNV-3) — AQSH va ROSSIYA", font=font("InterDisplay-Black", 60), fill=WHITE)
    d.text((120, 232), "Strategik yadroviy qurollarni cheklash boʻyicha soʻnggi yirik shartnoma", font=font("Inter-Medium", 34), fill=GREY)
    y = 560; x0, x1 = 260, 1560
    p = eout(lt / 3.2)
    d.line([x0, y, lerp(x0, x1, p), y], fill=WHITE, width=6)
    ev = [(0.0, "2010", "Imzolandi (Praga)"), (0.55, "2021", "5 yilga uzaytirildi"), (1.0, "5-FEVRAL 2026", "MUDDATI TUGADI")]
    for k, (u, yr, s) in enumerate(ev):
        if p < u:
            continue
        x = lerp(x0, x1, u)
        last = k == 2
        c = RED if last else GOLD
        d.ellipse([x - 20, y - 20, x + 20, y + 20], fill=c, outline=WHITE, width=4)
        d.text((x, y - 70), yr, font=font("InterDisplay-Black", 52 if last else 46), fill=c, anchor="mm")
        d.text((x, y + 70), s, font=font("Inter-Bold", 34), fill=WHITE, anchor="mm")
    if lt > 7.8:
        a = eout((lt - 7.8) / 0.5)
        d.rectangle([0, 760, W, 900], fill=RED + (int(230 * a),))
        d.text((W / 2, 830), "1970-yillardan beri ilk bor — HECH QANDAY YURIDIK CHEKLOV YOʻQ", font=font("InterDisplay-Black", 50), fill=WHITE + (int(255 * a),), anchor="mm")
    return img


def sipri(lt, dur, ctx):
    img = news_bg(ctx.get("gt", 0))
    d = ImageDraw.Draw(img, "RGBA")
    d.text((W / 2, 130), "DUNYODAGI YADROVIY KALLAKLAR · 2026-yil yanvar", font=font("InterDisplay-Black", 54), fill=WHITE, anchor="mm")
    # phase A: counter (0 - 11.5), phase B: donut 83% (11.5-17), phase C: China 620 (17-)
    if lt < 11.6:
        n = round(12187 * eout(max(0, lt - 5.0) / 2.2))
        s = f"{n:,}".replace(",", " ")
        d.text((W / 2, 500), s if lt > 5.0 else "SIPRI", font=font("InterDisplay-Black", 230), fill=GOLD, anchor="mm")
        d.text((W / 2, 680), "yadroviy kallak" if lt > 5.0 else "Stokgolm Xalqaro Tinchlik Tadqiqotlari Instituti", font=font("Inter-Bold", 52 if lt > 5.0 else 44), fill=WHITE, anchor="mm")
    elif lt < 17.3:
        q = lt - 11.6
        cx, cy, r = 660, 560, 250
        ang = 360 * 0.83 * eout(q / 1.2)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(60, 72, 100))
        d.pieslice([cx - r, cy - r, cx + r, cy + r], -90, -90 + ang, fill=RED)
        d.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], fill=NAVY)
        d.text((cx, cy), f"{int(83 * eout(q / 1.2))}%", font=font("InterDisplay-Black", 110), fill=WHITE, anchor="mm")
        d.text((1020, 470), "AQSH va ROSSIYA", font=font("InterDisplay-Black", 70), fill=WHITE)
        d.text((1020, 570), "foydalanishga tayyor", font=font("Inter-Medium", 44), fill=GREY)
        d.text((1020, 630), "kallaklarning ~83 foizi", font=font("Inter-Medium", 44), fill=GREY)
    else:
        q = lt - 17.3
        d.text((W / 2, 300), "XITOY", font=font("InterDisplay-Black", 90), fill=WHITE, anchor="mm")
        n = round(620 * eout(q / 1.3))
        d.text((W / 2, 520), f"≈{n}", font=font("InterDisplay-Black", 220), fill=GOLD, anchor="mm")
        d.text((W / 2, 690), "kallak", font=font("Inter-Bold", 52), fill=WHITE, anchor="mm")
        if q > 2.8:
            a = eout((q - 2.8) / 0.4)
            d.rectangle([0, 790, W, 900], fill=RED + (int(230 * a),))
            d.text((W / 2, 845), "DUNYODAGI ENG TEZ OʻSAYOTGAN YADROVIY ARSENAL", font=font("InterDisplay-Black", 50), fill=WHITE + (int(255 * a),), anchor="mm")
    return img


def thucydides(lt, dur, ctx):
    img = news_bg(ctx.get("gt", 0))
    d = ImageDraw.Draw(img, "RGBA")
    d.text((W / 2, 150), "“FUKIDID TUZOGʻI”", font=font("InterDisplay-Black", 96), fill=GOLD, anchor="mm")
    d.text((W / 2, 250), "Qadimgi yunon tarixchisi Fukidid nomi bilan ataladigan nazariya", font=font("Inter-Medium", 36), fill=GREY, anchor="mm")
    base = 860
    # rising power bar (left) grows, ruling power (right) steady
    p = eout(max(0, lt - 3.5) / 4.0)
    hl = lerp(120, 470, p); hr = 450
    d.rectangle([520, base - hl, 760, base], fill=RED)
    d.rectangle([1160, base - hr, 1400, base], fill=(90, 140, 220))
    d.text((640, base + 40), "Tez kuchayib", font=font("Inter-Bold", 34), fill=WHITE, anchor="mm")
    d.text((640, base + 82), "borayotgan davlat", font=font("Inter-Bold", 34), fill=WHITE, anchor="mm")
    d.text((1280, base + 40), "Amaldagi", font=font("Inter-Bold", 34), fill=WHITE, anchor="mm")
    d.text((1280, base + 82), "yetakchi davlat", font=font("Inter-Bold", 34), fill=WHITE, anchor="mm")
    if lt > 7.8:
        a = eout((lt - 7.8) / 0.4)
        d.text((W / 2, 560), "⚔", font=font("Inter-Black", 120), fill=WHITE + (int(255 * a),), anchor="mm") if False else None
        d.rectangle([760, 520, 1160, 600], fill=(0, 0, 0, int(160 * a)))
        d.text((W / 2, 560), "RAQOBAT → URUSH?", font=font("InterDisplay-Black", 44), fill=GOLD + (int(255 * a),), anchor="mm")
    return img


def iran_hormuz_map():
    hl = {"IRN": (150, 40, 50), "ISR": (40, 90, 170), "USA": (40, 90, 170)}
    return maplate((52, 28, 60), (55.5, 26.2, 16), hl, pins=[(56.3, 26.55, "HORMUZ BOʻGʻOZI", 1.2), (53.7, 32.4, "ERON", 0.6, "l")])


def central_asia(lt, dur, ctx):
    hl = {"UZB": (40, 160, 110), "RUS": (130, 50, 60), "CHN": (150, 40, 40)}
    v = view_lerp((75, 48, 120), (72, 47, 60), min(1, lt / (dur * 0.6)))
    img = draw_map(v, hl)
    pin(img, v, 69.24, 41.3, "OʻZBEKISTON", lt - 0.3)
    d = ImageDraw.Draw(img, "RGBA")
    if lt > 3.0:
        arc(img, v, (69.24, 41.3), (50, 57), (lt - 3.0) / 1.2, color=GOLD)
        arc(img, v, (69.24, 41.3), (100, 36), (lt - 3.4) / 1.2, color=GOLD)
        if lt > 4.2:
            pin(img, v, 50, 57, "ROSSIYA — yirik savdo hamkori", lt - 4.2, color=(130, 50, 60), size=30, side="l")
            pin(img, v, 100, 36, "XITOY — yirik savdo hamkori", lt - 4.4, color=(150, 40, 40), size=30, side="r")
    return grade(img, 1.0, 1.0)


def checklist(lt, dur, ctx):
    img = blurred(grade(kenburns(P(5), lt / dur, 1.05, 1.15)), 14, 0.62)
    d = ImageDraw.Draw(img, "RGBA")
    d.text((W / 2, 220), "HOZIRCHA:", font=font("InterDisplay-Black", 70), fill=GOLD, anchor="mm")
    items = ["Imzolangan aniq hujjat", "Eʼlon qilingan aniq reja", "Toʻxtagan urush"]
    for k, s in enumerate(items):
        ts = 0.5 + k * 1.6
        if lt < ts:
            continue
        a = eout((lt - ts) / 0.3)
        y = 380 + k * 150
        d.rounded_rectangle([420, y - 55, 1500, y + 55], 10, fill=(0, 0, 0, int(170 * a)))
        d.line([470, y - 25, 520, y + 25], fill=RED, width=12); d.line([470, y + 25, 520, y - 25], fill=RED, width=12)
        d.text((580, y), s, font=font("InterDisplay-Bold", 56), fill=WHITE + (int(255 * a),), anchor="lm")
        if lt > ts + 0.4:
            d.text((1440, y), "YOʻQ", font=font("InterDisplay-Black", 48), fill=RED, anchor="rm")
    return img


def split_view(lt, dur, ctx):
    a_ = grade(kenburns(P(18), lt / dur, 1.1, 1.2, (0.5, 0.45), (0.5, 0.42)))
    b_ = grade(kenburns(P(2), lt / dur, 1.15, 1.05))
    img = Image.new("RGB", (W, H))
    img.paste(a_.crop((W // 4, 0, W // 4 + W // 2, H)), (0, 0))
    img.paste(b_.crop((W // 4, 0, W // 4 + W // 2, H)), (W // 2, 0))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([W // 2 - 4, 0, W // 2 + 4, H], fill=WHITE)
    for k, (s, ts) in enumerate([("MULOQOT QAYTMOQDA", 0.3), ("ODDIY FOTOSESSIYA?", 7.5)]):
        if lt < ts:
            continue
        a = eout((lt - ts) / 0.35)
        x = k * W // 2
        d.rectangle([x + 40, 150, x + W // 2 - 40, 260], fill=(RED if k else (40, 120, 90)) + (int(235 * a),))
        d.text((x + W // 4, 205), s, font=font("InterDisplay-Black", 54), fill=WHITE + (int(255 * a),), anchor="mm")
    if lt < 7.5:
        d.rectangle([W // 2, 0, W, H], fill=(0, 0, 0, 140))
    return img


def endcard(lt, dur, ctx):
    img = blurred(grade(kenburns(P(0), lt / dur, 1.0, 1.1)), 14, 0.6)
    d = ImageDraw.Draw(img, "RGBA")
    a = eout(lt / 0.5)
    d.text((W / 2, 400), "Fikringizni izohlarda yozib qoldiring", font=font("InterDisplay-Black", 76), fill=WHITE + (int(255 * a),), anchor="mm")
    d.rounded_rectangle([W / 2 - 330, 500, W / 2 + 330, 590], 45, fill=RED + (int(255 * a),))
    d.text((W / 2, 545), "OBUNA BOʻLING", font=font("InterDisplay-Black", 44), fill=WHITE + (int(255 * a),), anchor="mm")
    d.text((W / 2, 690), "Barcha manbalar va litsenziyalar — video tavsifida", font=font("Inter-Medium", 34), fill=GREY, anchor="mm")
    return img


def brent(lt, dur, ctx):
    base = video(M("commons/tanker_niovi.webm"), 8)(lt, dur, ctx) if have(M("commons/tanker_niovi.webm")) else grade(kenburns(M("nasa/iss063e002679.jpg"), lt / dur, 1.2, 1.3))
    img = blurred(base, 6, 0.45) if lt > 0 else base
    d = ImageDraw.Draw(img, "RGBA")
    a = eout(lt / 0.4)
    d.text((W / 2, 300), "BRENT NEFTI · SHU HAFTA", font=font("InterDisplay-Black", 58), fill=WHITE + (int(255 * a),), anchor="mm")
    d.text((W / 2, 500), "≈ 93 $", font=font("InterDisplay-Black", 240), fill=GOLD + (int(255 * a),), anchor="mm")
    d.text((W / 2, 660), "1 barrel uchun", font=font("Inter-Bold", 46), fill=WHITE + (int(255 * a),), anchor="mm")
    if lt > 5.6:
        b = eout((lt - 5.6) / 0.4)
        for k, s in enumerate(["YOQILGʻI", "YUK TASHISH", "DOʻKONDAGI NARXLAR"]):
            if lt < 5.6 + k * 0.9:
                continue
            x = 360 + k * 600
            d.rounded_rectangle([x - 260, 770, x + 260, 870], 12, fill=RED + (int(235 * b),))
            d.text((x, 820), s, font=font("InterDisplay-Black", 44), fill=WHITE, anchor="mm")
    return img


# =====================================================================
# STORYBOARD  (times in seconds, from the voice-over word timestamps)
# =====================================================================
bravo = M("commons/castle_bravo.webm")
hook0 = video(bravo, 3.0, speed=1.0, zoom=(1.5, 1.6), center=(0.66, 0.40)) if have(bravo) else photo(8, 1.25, 1.05)

# 1 HOOK
scene(0.00, seq((0, hook0), (2.45, photo(8, 1.35, 1.12, (0.55, 0.5), (0.5, 0.45))), (4.75, photo(2, 1.18, 1.0, (0.5, 0.4), (0.5, 0.42)))),
      [HL("TARIXDA BIRINCHI MARTA", 0.25, 2.4, pos="c", size=92),
       HL("ENG YIRIK 3 YADROVIY DAVLAT", 2.55, 4.7, pos="c", size=84, color=GOLD),
       HL("BIR STOL ATROFIDA", 4.85, None, pos="bl", size=80)],
      cr=BRAVO, tr="flash", ticker_on=False, label="Hook: yadroviy sinov arxivi → uch tomonlama stol")
S[-1]["cr_fn"] = lambda lt: BRAVO if (lt < 2.45 and have(bravo)) else KR_F
scene(7.30, triptych, [], cr=KR_F, tr="flash", ticker_on=False, label="Uch yetakchi: Tramp, Si, Putin")
scene(11.20, photo(31, 1.0, 1.15, (0.5, 0.35), (0.5, 0.3)),
      [HL("XITOY · SHENCHJEN", 0.15, None, pos="bl", size=72, sub="APEC sammiti doirasida · 19-noyabr, 2026")], cr=KR_F, tr="whip", ticker_on=False,
      label="Shenchjen fonidagi APEC rasmi")
scene(13.38, photo(6, 1.0, 1.1, (0.35, 0.5), (0.4, 0.5)), [QC("Biz haqiqatan ham tarix yaratyapmiz.", "Donald Tramp, uch tomonlama uchrashuvda", 0.4)],
      cr=KR_F, ticker_on=False, label="Tramp iqtibosi (Kreml stenogrammasi)")
scene(17.90, photo(5, 1.0, 1.15, (0.5, 0.5), (0.62, 0.45)), [HL("≈ 1,5 SOAT MUZOKARA", 0.2, 2.9, size=70), HL("UMUMIY BAYONOT — YOʻQ", 3.0, None, size=70, accent=GOLD)],
      cr=KR_F, ticker_on=False, label="Muzokaralar zali")
scene(23.62, blur_of(photo(4, 1.0, 1.1)), [HL("YOPIQ ESHIKLAR ORTIDA NIMA GAPLASHILDI?", 0.1, None, pos="c", size=80, box=False)], cr=KR_F, tr="whip", ticker_on=False,
      label="Savol kartasi")
scene(26.60, maplate((35, 40, 110), (42, 40, 70), {"UKR": (60, 110, 200), "IRN": (170, 50, 60)}, pins=[(31, 49, "UKRAINA", 0.3), (53.7, 32.4, "ERON", 1.6)]),
      [HL("YADROVIY QUROLLAR?", 3.0, None, pos="t", size=72, accent=GOLD)], cr=MAPSRC, ticker_on=False, label="Ukraina / Eron xaritasi")
scene(31.12, central_asia, [HL("BU BIZGA QANDAY TAʼSIR QILADI?", 0.2, None, pos="t", size=66)], cr=MAPSRC, ticker_on=False, label="Oʻzbekiston xaritada")
# 2 FACTS
scene(34.50, gbg, [BUMP("ASOSIY FAKTLAR")], tr="flash", ticker_on=False, label="Bumper")
scene(36.35, maplate((100, 30, 160), (114.06, 22.54, 7), {"CHN": (150, 40, 40)}, pins=[(114.06, 22.54, "SHENCHJEN", 2.2)]),
      [HL("19-NOYABR, 2026", 2.4, None, pos="t", size=64, sub="Xitoy janubi, Guangdun provinsiyasi")], cr=MAPSRC, label="Xarita: Shenchjen")
scene(40.75, video(M("kremlin/apec_ceo_summit_HD.mp4"), 481, zoom=(1.0, 1.1)),
      [LT("APEC — OSIYO-TINCH OKEANI IQTISODIY HAMKORLIGI", "Forumga 21 iqtisodiyot aʼzo", 0.4)], cr=KR_V, label="APEC biznes-sammiti zali (video)")
scene(48.95, seq((0, photo(0, 1.0, 1.12, (0.5, 0.55), (0.5, 0.5))), (2.3, photo(8, 1.0, 1.1, (0.45, 0.5), (0.5, 0.45)))),
      [LT("KILIN VILLA QARORGOHI", "Yetakchilar dumaloq stol atrofida", 0.3)], cr=KR_F, label="Uchrashuv qarorgohi va dumaloq stol")
scene(53.55, photo(3, 1.0, 1.12, (0.5, 0.4), (0.5, 0.38)), [LT("SI SZINPIN", "Xitoy Xalq Respublikasi raisi · mezbon", 0.15)], cr=KR_F, label="Si Szinpin")
scene(55.56, photo(1, 1.0, 1.08), [HL("≈ 90 DAQIQA", 0.4, None, size=96, sub="Xitoy davlat telekanali CCTV maʼlumoti")], cr=KR_F, label="Davomiylik")
# 3 WHY HISTORIC
scene(61.15, gbg, [BUMP("NEGA BU TARIXIY?")], tr="flash", label="Bumper")
scene(63.75, p5, [], cr=UNSC if have(M("commons/unsc_chamber.jpg")) else GFX, label="BMT XK grafikasi")
scene(70.85, photo(2, 1.05, 1.2, (0.5, 0.42), (0.5, 0.38)), [HL("UCH TOMONLAMA FORMAT — ILK MARTA", 0.3, None, size=66)], cr=KR_F, label="Uch yetakchi")
scene(76.75, photo(38, 1.0, 1.12), [HL("Pekin uchrashuvni rasman shu hafta tasdiqladi", 0.3, None, size=56)], cr=KR_F, label="Sammit maydoni")
scene(80.65, gbg, [BUMP("KUN XRONOLOGIYASI")], tr="flash", label="Bumper")
scene(83.05, maplate((118, 18, 40), (118, 18, 34), {"CHN": (150, 40, 40), "PHL": (60, 110, 200)},
                     pins=[(120.98, 14.6, "MANILA", 0.1), (114.06, 22.54, "SHENCHJEN", 1.8, "l")], arcs=[((120.98, 14.6), (114.06, 22.54), 0.3)]),
      [LT("CHORSHANBA", "Tramp Shenchjenga keldi · Si Szinpin aeroportda kutib oldi", 0.3)], cr=MAPSRC, label="Tramp yoʻli: ASEAN (Manila) → Shenchjen")
scene(88.00, seq((0, photo(29, 1.0, 1.1, (0.5, 0.45), (0.5, 0.4))), (2.0, photo(30, 1.05, 1.15))),
      [LT("KECHKI QABUL MAROSIMI", "Uch yetakchi qisqa vaqt birga koʻrindi", 0.2)], cr=KR_F, label="Gala-qabul")
scene(92.05, seq((0, photo(16, 1.0, 1.1, (0.5, 0.45), (0.55, 0.45))), (3.6, photo(19, 1.0, 1.12))),
      [LT("PAYSHANBA · TRAMP — PUTIN", "Kreml: suhbat taxminan 40 daqiqa davom etdi", 0.3)], cr=KR_F, label="Tramp–Putin uchrashuvi")
scene(99.30, video(M("kremlin/alaska_2025_presser_HD.mp4"), 62, zoom=(1.0, 1.08)),
      [HL("ARXIV · ALYASKA, 2025-YIL AVGUST", 0.2, None, pos="t", size=56, accent=GOLD)], cr=ARCH_KR, label="Alyaska 2025 arxiv videosi")
scene(105.35, photo(12, 1.0, 1.12, (0.4, 0.5), (0.35, 0.5)), [HL("Kreml yordamchisi Yuriy Ushakov: asosiy mavzu — Ukraina", 0.3, None, size=54)], cr=KR_F, label="Kreml delegatsiyasi")
scene(109.50, photo(22, 1.0, 1.15), [HL("“Uchrashuv yaxshi oʻtdi”", 0.2, 2.6, size=64), HL("Alohida muhim bayonot berilmadi", 2.7, None, size=58, accent=GOLD)], cr=KR_F, label="Tramp–Putin, umumiy plan")
scene(115.80, photo(28, 1.25, 1.35, (0.3, 0.45), (0.38, 0.45)), [LT("TRAMP — SI SZINPIN", "CCTV: suhbat taxminan bir soat davom etdi", 0.3)], cr=KR_F, label="Tramp va Si")
scene(123.00, thucydides, [], cr=GFX, label="Fukidid tuzogʻi grafikasi")
scene(135.70, photo(37, 1.0, 1.1, (0.5, 0.4), (0.5, 0.4)), [QC("Bu tuzoqqa tushish aslo muqarrar emas.", "Si Szinpin", 0.25, "l")], cr=KR_F, label="Si iqtibosi")
scene(139.10, iran_hormuz_map(), [HL("Tramp: Xitoy ham Hormuz orqali energiya oqimidan manfaatdor", 1.6, None, size=50)], cr=MAPSRC, label="Hormuz xaritasi")
# 4 TRILATERAL
scene(146.30, seq((0, photo(4, 1.0, 1.12)), (2.6, photo(7, 1.05, 1.15, (0.5, 0.45), (0.5, 0.4)))),
      [LT("UCH TOMONLAMA UCHRASHUV", "Kilin villa · Shenchjen", 0.3)], cr=KR_F, label="Uch tomonlama uchrashuv boshlandi")
scene(151.45, photo(3, 1.1, 1.25, (0.5, 0.35), (0.5, 0.33)),
      [QC("Buyuk davlatlar oʻrtasidagi yaxshi qoʻshnichilik — tanlovlardan biri emas, yagona toʻgʻri yoʻl.", "Si Szinpin", 0.2)], cr=KR_F, label="Si iqtibosi (Kreml stenogrammasi)")
scene(157.35, video(bravo, 14, speed=0.6, zoom=(1.5, 1.65), center=(0.66, 0.40)) if have(bravo) else photo(5),
      [HL("“DAMOKL QILICHI”", 0.3, 4.6, pos="c", size=100, color=GOLD),
       HL("Yadroviy urushda gʻolib boʻlmaydi — u hech qachon boshlanmasligi kerak", 5.0, None, size=54)], cr=BRAVO, label="Damokl qilichi: yadroviy portlash arxivi")
scene(169.50, photo(7, 1.0, 1.15, (0.5, 0.45), (0.45, 0.42)),
      [LT("VLADIMIR PUTIN", "Rossiya prezidenti", 0.2, 3.6),
       HL("BMT Nizomi va xalqaro huquq", 0.6, 4.2, size=58), HL("Mintaqaviy mojarolar, jumladan Ukraina", 4.3, 11.3, size=58), HL("Energetika xavfsizligini muhokama qilish", 11.4, None, size=58, accent=GOLD)],
      cr=KR_F, label="Putin chiqishi")
scene(185.40, photo(9, 1.0, 1.15, (0.5, 0.35), (0.5, 0.33)),
      [LT("DONALD TRAMP", "AQSH prezidenti", 0.1, 3.4), HL("Yadroviy qurollar sonini qanday kamaytirish mumkin?", 3.5, None, size=56)], cr=KR_F, label="Tramp chiqishi")
scene(196.60, photo(21, 1.0, 1.1, (0.35, 0.5), (0.3, 0.5)),
      [QC("Yadroviy qurolga ega boʻlgach, undan voz kechish juda qiyin.", "Donald Tramp", 0.2, "r")], cr=KR_F, label="Tramp iqtibosi (Kreml stenogrammasi)")
scene(204.45, maplate((53, 32, 40), (53, 32, 30), {"IRN": (150, 40, 50)}, pins=[(51.39, 35.69, "TEHRON", 0.5)]),
      [HL("“Eronga yadroviy qurol olishga yoʻl qoʻymaymiz”", 0.6, None, size=58, sub="Donald Tramp")], cr=MAPSRC, label="Eron xaritasi")
# 5 WHY IT MATTERS
scene(209.70, gbg, [BUMP("BU NIMA UCHUN MUHIM?")], tr="flash", label="Bumper")
scene(213.00, video(bravo, 30, speed=0.7, zoom=(1.5, 1.55), center=(0.66, 0.40)) if have(bravo) else gbg, [BUMP("YADROVIY QUROLLAR", None, "1-SABAB")], cr=BRAVO if have(bravo) else "", tr="flash", label="1-sabab")
scene(215.14, timeline_newstart, [], cr=GFX, label="New START xronologiyasi")
scene(232.85, sipri, [], cr="MANBA: SIPRI Yearbook 2026", label="SIPRI statistikasi")
scene(256.80, photo(34, 1.0, 1.12, (0.75, 0.5), (0.8, 0.5)),
      [HL("Xitoy pozitsiyasi: avval AQSH va Rossiya qisqartirsin", 0.3, 10.7, size=54), HL("Hozircha bu — muzokara emas", 10.9, None, size=62, accent=GOLD)], cr=KR_F, label="Xitoy pozitsiyasi")
scene(271.50, gbg, [BUMP("ERON", None, "2-SABAB")], tr="flash", label="2-sabab")
scene(272.96, maplate((48, 30, 50), (52, 28, 36), {"IRN": (150, 40, 50), "ISR": (40, 90, 170)}, pins=[(53.7, 32.4, "ERON", 0.3), (35, 31.5, "ISROIL", 0.8, "l")]),
      [HL("AQSH va Isroilning Eron bilan urushi — 9-oy", 0.4, None, size=56)], cr=MAPSRC, label="Eron urushi xaritasi")
_irgc = M("commons/irgc_speedboat.webm")
scene(276.85, video(_irgc, 2) if have(_irgc) else photo(M("nasa/iss040e009362.jpg"), 1.0, 1.2),
      [HL("Hormuz orqali qatnov hanuz izdan chiqqan", 0.2, None, size=56)], cr=NAVY_V if have(_irgc) else NASA, label="Hormuz: dengizdagi vaziyat")
scene(280.15, photo(M("nasa/iss063e002679.jpg"), 1.0, 1.25, (0.5, 0.5), (0.45, 0.5)),
      [LT("HORMUZ BOʻGʻOZI", "Dunyo neft savdosining eng muhim yoʻllaridan biri", 0.2)], cr=NASA, label="Hormuz kosmosdan")
scene(283.90, brent, [], cr=NAVY_V if have(M("commons/tanker_niovi.webm")) else NASA, label="Brent narxi")
scene(296.98, photo(5, 1.12, 1.0, (0.4, 0.5), (0.5, 0.5)),
      [HL("Xitoy davlat OAV: barqaror energiya oqimi boʻyicha kelishuv", 0.3, 7.2, size=54), HL("Kelishuvning aniq matni eʼlon qilinmagan", 7.3, None, size=58, accent=GOLD)], cr=KR_F, label="Energiya kelishuvi")
scene(308.80, gbg, [BUMP("BIZNING MINTAQA", None, "3-SABAB")], tr="flash", label="3-sabab")
scene(311.00, central_asia, [HL("Yuz minglab vatandoshlarimiz Rossiyada ishlaydi", 4.5, 9.4, size=52),
                             HL("Urush · sanksiyalar · katta davlatlar munosabatlari → Markaziy Osiyo iqtisodiyoti", 9.5, None, size=46, maxw=1700)],
      cr=MAPSRC, label="Markaziy Osiyo xaritasi")
scene(325.90, photo(10, 1.0, 1.12), [HL("Mintaqamiz uchun ham kichik voqea emas", 0.2, None, size=60)], cr=KR_F, label="Yetakchilar uchrashuvdan keyin")
# 6 WHAT NEXT
scene(331.20, gbg, [BUMP("ENDI NIMA BOʻLADI?")], tr="flash", label="Bumper")
scene(333.25, photo(24, 1.0, 1.12), [HL("Aniq natija eʼlon qilinmagan", 0.2, 2.5, size=60), HL("Tramp Vashingtonga qaytdi", 2.6, None, size=60, accent=GOLD)], cr=KR_F, label="Natija")
scene(338.10, maplate((15, 50, 60), (13.4, 52.5, 22), {"DEU": (60, 110, 200), "UKR": (230, 190, 40)}, pins=[(13.4, 52.52, "BERLIN", 1.0)]),
      [LT("BERLIN · BUGUN", "Ukrainaga yordam beruvchi davlatlar uchrashuvi", 1.2)], cr=MAPSRC, label="Berlin xaritasi")
_ukr = blur_of(maplate((31, 49, 30), (31, 49, 26), {"UKR": (60, 110, 200)}, pins=[(30.52, 50.45, "KIYEV", 0.2)]))
scene(343.00, _ukr, [QC("AQSH vakillari ukrainalik rasmiylarga Xitoydagi muzokaralar haqida maʼlumot beradi.", "Volodimir Zelenskiy", 0.2, "l"),
                    ], cr="", label="Zelenskiy bayonoti")
scene(349.80, _ukr, [QC("Agar Tramp va Si Szinpin Rossiyaga bosim oʻtkazsa, urush tugashi mumkin.", "Volodimir Zelenskiy", 0.2, "r")], cr="", label="Zelenskiy fikri")
scene(356.20, maplate((-95, 35, 70), (-80.2, 25.8, 22), {"USA": (60, 110, 200)}, pins=[(-80.2, 25.8, "FLORIDA · G20", 1.2)]),
      [HL("DEKABR — G20 SAMMITI", 0.3, None, pos="t", size=66, sub="Tramp va Si yana uchrashishi kutilmoqda · Putin ishtiroki noaniq")], cr=MAPSRC, label="G20 Florida")
scene(366.80, split_view, [LT("IGOR REYTEROVICH", "Ukrainalik tahlilchi", 10.5, None, y=820)], cr=KR_F, label="Ikki xil baho")
# 7 OUTRO
scene(382.30, seq((0, photo(0, 1.1, 1.0)), (3.4, photo(29, 1.0, 1.12)), (6.3, photo(18, 1.0, 1.1)), (9.4, photo(11, 1.0, 1.12))),
      [HL("TARIXGA YANGI SANA YOZILDI", 0.2, 3.3, size=70), HL("Tinchlik · Barqarorlik · Yadroviy xavfni kamaytirish", 8.4, None, size=56, accent=GOLD)], cr=KR_F, tr="flash", label="Xulosa montaji")
scene(394.80, checklist, [], cr=KR_F, label="Hozircha yoʻq: hujjat, reja, sulh")
scene(401.40, photo(2, 1.0, 1.15, (0.5, 0.4), (0.5, 0.38)),
      [HL("Bir stolda oʻtirishning oʻzi dunyoni xavfsizroq qiladimi?", 0.3, 4.6, pos="c", size=62), HL("Yoki bu hali amalga oshmagan bir lahzami?", 4.8, None, pos="c", size=62, color=GOLD)], cr=KR_F, label="Yakuniy savol")
scene(409.60, endcard, [], cr=KR_F, ticker_on=False, label="Yakuniy kadr / CTA")

END = 415.02
for k, s in enumerate(S):
    s["t1"] = S[k + 1]["t0"] if k + 1 < len(S) else END
