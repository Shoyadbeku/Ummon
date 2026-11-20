"""Full-frame motion-graphics scenes."""
import numpy as np, math
from PIL import Image, ImageDraw, ImageFilter
from gfx import *

_bg_cache = {}
def news_bg(ctx, t, tint=(14, 26, 50)):
    key = (ctx.W, ctx.H, tint)
    if key not in _bg_cache:
        W, H = ctx.W, ctx.H
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((x - W * 0.62) / W) ** 2 + ((y - H * 0.35) / H) ** 2)
        g = np.clip(1.15 - r * 1.3, 0.25, 1)[..., None]
        base = (np.array(tint, np.float32) * g + np.array([4, 7, 14], np.float32) * (1 - g))
        im = Image.fromarray(base.clip(0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im, "RGBA")
        step = ctx.s(120)
        for gx in range(0, W, step): d.line([gx, 0, gx, H], fill=(255, 255, 255, 9), width=1)
        for gy in range(0, H, step): d.line([0, gy, W, gy], fill=(255, 255, 255, 9), width=1)
        _bg_cache[key] = np.asarray(im)
    f = _bg_cache[key].copy()
    # moving light sweep
    W = ctx.W
    cx = int(((t * 0.08) % 1.4 - 0.2) * W)
    x0, x1 = max(0, cx - ctx.s(500)), min(W, cx + ctx.s(500))
    if x1 > x0:
        xs = np.arange(x0, x1)
        w = (1 - np.abs(xs - cx) / ctx.s(500)) ** 2 * 10
        f[:, x0:x1] = np.clip(f[:, x0:x1].astype(np.int16) + w[None, :, None].astype(np.int16), 0, 255).astype(np.uint8)
    return f


def draw_on(f):
    im = Image.fromarray(f)
    return im, ImageDraw.Draw(im, "RGBA")


def title_card(main, sub, date):
    def fn(ctx, t, dur, st):
        s = ctx.s
        f = news_bg(ctx, t, (40, 16, 22))
        im, d = draw_on(f)
        a = ease_out(t / 0.5)
        # red bar wipe
        bw = int(ctx.W * 0.62 * ease_out(t / 0.6))
        d.rectangle([s(190), s(780), s(190) + bw, s(800)], fill=RED)
        fm = font("black", s(230)); fs = font("semi", s(88)); fd = font("bold", s(64))
        y = s(830) + (1 - a) * s(60)
        draw_text(d, (s(190), y), main, fm, (255, 255, 255, int(255 * a)), tracking=s(4))
        b = ease_out((t - 0.35) / 0.5)
        d.text((s(196), s(1110) + (1 - b) * s(40)), sub, font=fs, fill=(230, 234, 242, int(255 * b)))
        c = ease_out((t - 0.7) / 0.5)
        tw = fd.getlength(date) + s(60)
        d.rectangle([s(190), s(620), s(190) + tw, s(720)], fill=(255, 255, 255, int(240 * c)))
        d.text((s(220), s(636)), date, font=fd, fill=NAVY + (int(255 * c),))
        return np.asarray(im)
    return fn


def vote_scene(no=51, yes=48):
    def fn(ctx, t, dur, st):
        s = ctx.s
        f = news_bg(ctx, t)
        im, d = draw_on(f)
        fh = font("black", s(110)); fl = font("bold", s(78)); fn_ = font("black", s(260)); fsm = font("semi", s(56))
        d.text((s(240), s(200)), "AQSh SENATI · 19-NOYABR", font=fh, fill=WHITE)
        d.text((s(244), s(350)), "Eron urushi bo‘yicha rezolyutsiya (Kongress ruxsati talabi)", font=fsm, fill=GREY)
        maxw = s(2600)
        for i, (lab, val, col, t0) in enumerate([("QARSHI", no, RED, 0.2), ("TARAFDOR", yes, TEAL, 0.5)]):
            y = s(640) + i * s(520)
            p = ease_out((t - t0) / 1.0)
            d.text((s(240), y), lab, font=fl, fill=OFF)
            w = int(maxw * val / 100 * 1.8 * p)
            d.rectangle([s(240), y + s(120), s(240) + w, y + s(330)], fill=col)
            num = str(int(round(val * p)))
            d.text((s(240) + w + s(50), y + s(90)), num, font=fn_, fill=WHITE)
        return np.asarray(im)
    return fn


def counter_scene(value=48_300_000_000, label="URUSHNING AQShga NARXI", note="13-noyabr holatiga · Pentagon ma’lumoti"):
    def fn(ctx, t, dur, st):
        s = ctx.s
        f = news_bg(ctx, t, (36, 20, 14))
        im, d = draw_on(f)
        p = ease_out(t / 2.2)
        v = value * p
        txt = "$" + f"{int(v):,}".replace(",", " ")
        fl = font("black", s(100)); fv = font("black", s(330)); fn_ = font("semi", s(64))
        draw_text(d, (s(240), s(520)), label, fl, GOLD, tracking=s(6))
        d.text((s(220), s(700)), txt, font=fv, fill=WHITE)
        a = ease_out((t - 2.0) / 0.5)
        d.rectangle([s(240), s(1160), s(240) + int(s(1900) * a), s(1260)], fill=RED + (int(255 * a),))
        d.text((s(280), s(1170)), "≈ 48,3 MLRD DOLLAR", font=font("black", s(76)), fill=(255, 255, 255, int(255 * a)))
        d.text((s(244), s(1340)), note, font=fn_, fill=(190, 198, 212, int(255 * a)))
        return np.asarray(im)
    return fn


def brent_scene(pre=72.0, now=92.5):
    def fn(ctx, t, dur, st):
        s = ctx.s
        f = news_bg(ctx, t, (14, 30, 40))
        im, d = draw_on(f)
        fh = font("black", s(110)); fs = font("semi", s(56)); fv = font("black", s(150)); fl = font("bold", s(64))
        d.text((s(240), s(190)), "BRENT NEFTI, 1 BARREL", font=fh, fill=WHITE)
        d.text((s(244), s(340)), "Taxminiy narx · Manba: Reuters (20-noyabr)", font=fs, fill=GREY)
        base_y = s(1820); scale = s(13.5)
        bars = [("URUSHDAN OLDIN", pre, (120, 135, 160), 0.3), ("20-NOYABR, 2026", now, RED, 1.1)]
        for i, (lab, val, col, t0) in enumerate(bars):
            x = s(700) + i * s(1300)
            p = ease_out((t - t0) / 1.1)
            h = int((val - 0) * scale * p)
            d.rectangle([x, base_y - h, x + s(700), base_y], fill=col)
            d.text((x, base_y + s(40)), lab, font=fl, fill=OFF)
            if p > 0.05:
                txt = f"≈ ${val * p:.1f}".replace(".", ",") if i else f"≈ ${val * p:.0f}"
                d.text((x, base_y - h - s(190)), txt, font=fv, fill=WHITE)
        a = ease_out((t - 2.4) / 0.5)
        if a > 0:
            pct = (now / pre - 1) * 100
            txt = f"+{pct:.0f}%"
            fb = font("black", s(170))
            tw = fb.getlength(txt)
            x, y = s(3020), s(560)
            d.rounded_rectangle([x - s(40), y - s(20), x + tw + s(40), y + s(210)], radius=s(20), fill=GOLD + (int(255 * a),))
            d.text((x, y), txt, font=fb, fill=NAVY + (int(255 * a),))
        d.line([s(600), base_y, s(3500), base_y], fill=(255, 255, 255, 90), width=s(6))
        return np.asarray(im)
    return fn


def scenarios_scene(focus=None, t_second=0.0):
    """Two cards; focus: 1, 2 or None(both)."""
    def fn(ctx, t, dur, st):
        s = ctx.s
        f = news_bg(ctx, t)
        im, d = draw_on(f)
        fh = font("black", s(110)); fn_ = font("black", s(200)); ft = font("black", s(92)); fb = font("semi", s(64))
        d.text((s(240), s(170)), "IKKI SSENARIY", font=fh, fill=WHITE)
        cards = [("1", "DIPLOMATIYA", "Yangi yilgacha katta qaror yo‘q — diplomatiyaga vaqt qoladi", TEAL, 0.2),
                 ("2", "YANGI ZARBALAR", "Qisqa, lekin shiddatli yangi harbiy kampaniya", RED, t_second)]
        for i, (n, title, body, col, t0) in enumerate(cards):
            a = ease_out((t - t0) / 0.6)
            if a <= 0: continue
            x = s(240) + i * s(1720); y = s(460) + (1 - a) * s(80)
            dim = 1.0 if (focus is None or focus == i + 1) else 0.35
            al = int(255 * a * dim)
            d.rounded_rectangle([x, y, x + s(1600), y + s(1380)], radius=s(26), fill=(10, 18, 36, int(230 * a)), outline=col + (al,), width=s(10))
            d.rectangle([x, y, x + s(1600), y + s(300)], fill=col + (al,))
            d.text((x + s(70), y + s(40)), n, font=fn_, fill=(255, 255, 255, al))
            d.text((x + s(300), y + s(100)), title, font=ft, fill=(255, 255, 255, al))
            for j, l in enumerate(wrap(body, fb, s(1450))):
                d.text((x + s(70), y + s(400) + j * s(96)), l, font=fb, fill=(235, 238, 245, al))
        return np.asarray(im)
    return fn


def question_scene(lines, sub=None, tint=(14, 26, 50)):
    def fn(ctx, t, dur, st):
        s = ctx.s
        f = news_bg(ctx, t, tint)
        im, d = draw_on(f)
        fq = font("black", s(150))
        y = s(700) - len(lines) * s(90)
        for i, l in enumerate(lines):
            a = ease_out((t - 0.25 * i) / 0.5)
            tw = fq.getlength(l)
            d.text(((ctx.W - tw) / 2, y + i * s(190) + (1 - a) * s(50)), l, font=fq, fill=(255, 255, 255, int(255 * a)))
        if sub:
            a = ease_out((t - 0.25 * len(lines)) / 0.5)
            fs = font("semi", s(72)); tw = fs.getlength(sub)
            d.text(((ctx.W - tw) / 2, y + len(lines) * s(190) + s(60)), sub, font=fs, fill=GOLD + (int(255 * a),))
        return np.asarray(im)
    return fn


def end_card():
    def fn(ctx, t, dur, st):
        s = ctx.s
        f = news_bg(ctx, t, (40, 16, 22))
        im, d = draw_on(f)
        a = ease_out(t / 0.5); b = ease_out((t - 0.5) / 0.5); c = ease_out((t - 1.0) / 0.5)
        fq = font("black", s(150)); fs = font("bold", s(80)); fsm = font("semi", s(54))
        l1 = "FIKRINGIZNI IZOHLARDA YOZING"
        tw = fq.getlength(l1)
        d.text(((ctx.W - tw) / 2, s(640)), l1, font=fq, fill=(255, 255, 255, int(255 * a)))
        # subscribe button
        lab = "OBUNA BO‘LING"
        bw = fs.getlength(lab) + s(200)
        x = (ctx.W - bw) / 2; y = s(980)
        pulse = 1 + 0.04 * math.sin(t * 5) * b
        cx, cy = x + bw / 2, y + s(90)
        hw, hh = bw / 2 * pulse, s(90) * pulse
        d.rounded_rectangle([cx - hw, cy - hh, cx + hw, cy + hh], radius=s(30), fill=RED + (int(255 * b),))
        d.text((x + s(100), y + s(38)), lab, font=fs, fill=(255, 255, 255, int(255 * b)))
        l3 = "Barcha video va foto manbalari — video tavsifida"
        tw = fsm.getlength(l3)
        d.text(((ctx.W - tw) / 2, s(1330)), l3, font=fsm, fill=(200, 206, 218, int(255 * c)))
        return np.asarray(im)
    return fn


def timeline_scene(items):
    """items: [(date, text, t_on)] horizontal timeline."""
    def fn(ctx, t, dur, st):
        s = ctx.s
        f = news_bg(ctx, t)
        im, d = draw_on(f)
        fh = font("black", s(110)); fd = font("black", s(84)); ft = font("semi", s(58))
        d.text((s(240), s(220)), "ERON URUSHI: QISQA XRONOLOGIYA", font=fh, fill=WHITE)
        y = s(1050)
        p = ease_in_out(t / 1.2)
        d.line([s(240), y, s(240) + int(s(3360) * p), y], fill=(255, 255, 255, 120), width=s(10))
        n = len(items)
        for i, (date, text, ton) in enumerate(items):
            a = ease_out((t - ton) / 0.5)
            if a <= 0: continue
            x = s(420) + i * (s(3000) // max(1, n - 1)) if n > 1 else s(1900)
            r = s(34) * ease_out_back((t - ton) / 0.4)
            col = RED if i == n - 1 else GOLD
            d.ellipse([x - r, y - r, x + r, y + r], fill=col)
            tw = fd.getlength(date)
            d.text((x - tw / 2, y - s(230) - (1 - a) * s(40)), date, font=fd, fill=col + (int(255 * a),))
            for j, l in enumerate(wrap(text, ft, s(900))):
                lw = ft.getlength(l)
                d.text((x - lw / 2, y + s(90) + j * s(76)), l, font=ft, fill=(235, 238, 245, int(255 * a)))
        return np.asarray(im)
    return fn
