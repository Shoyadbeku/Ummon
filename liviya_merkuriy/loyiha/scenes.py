# Storyboard: every scene with timing (seconds on the voice-over timeline),
# footage or graphics, overlays and credits.
import os, math
from gfx import *

S = ROOT
CL = os.path.join(S, 'clips') + '/'
IMG = os.path.join(S, 'img') + '/'

SBU = CL + 'hromadske_ua_91466_0.mp4'
NIGHT_BLAST = CL + 'readovkanews_117197_bb7eeb1808.mp4'
SHORE_FIRE = CL + 'Tsaplienko_102433_7d76a55379.mp4'
DRONE_WAKES = CL + 'insiderUKR_139140_8058c19d3c.mp4'
DAY_SMOKE = CL + 'insiderUKR_139140_bc2b7ca8a2.mp4'
RED_CARGO = CL + 'insiderUKR_139144_8785f5c2a6.mp4'
CARGO_HIT = CL + 'Tsaplienko_102455_7a7fe6120a.mp4'
CARGO_V = CL + 'meduzalive_150932_1e7e869b49.mp4'

CR_SBU = 'VIDEO: Ukraina Xavfsizlik xizmati (SBU) / V. Zelenskiy Telegram kanali'
CR_SOC = 'VIDEO: Ijtimoiy tarmoqlar / {}'
CR_MERK = 'FOTO: Rossiya Mudofaa vazirligi / Wikimedia Commons, CC BY 4.0'
CR_MERK2 = 'FOTO: 13243546A / Wikimedia Commons, CC BY-SA 4.0'

TOTAL = 357.75  # voice ends 355.25, +2.5 s outro


def photo(key):
    for ext in ('.jpg', '.jpeg', '.png'):
        p = IMG + key + ext
        if os.path.exists(p):
            return p
    return None


def photo_credit(key):
    import json
    try:
        m = json.load(open(IMG + 'meta.json'))[key]
    except Exception:
        return ''
    a = m['artist'] or 'Wikimedia Commons'
    return f"FOTO: {a} / Wikimedia Commons, {m['license']}"


SC = []


def clip(t0, t1, src, ss, speed=1.0, overlay=None, darken=0.0, credit_=None, tag=None, zoom=True):
    SC.append(dict(kind='clip', t0=t0, t1=t1, src=src, ss=ss, speed=speed, overlay=overlay, darken=darken,
                   credit=credit_, tag=tag, zoom=zoom))


def gfx(t0, t1, draw, credit_=None, tag=None):
    SC.append(dict(kind='gfx', t0=t0, t1=t1, draw=draw, credit=credit_, tag=tag))


TAG_BNG = 'BINGAZI, LIVIYA  ·  22-NOYABR'

# ----------------------------------------------------------------- HOOK
clip(0.00, 2.10, SBU, 12.0, speed=0.85,
     overlay=lambda im, t, d: caption(im, 'FRONTDAN ≈2 400 KM UZOQDA', t, d + 2.1, size=72, accent_words=('≈2', '400', 'KM')),
     credit_=CR_SBU)
clip(2.10, 4.20, SBU, 15.0, speed=0.9,
     overlay=lambda im, t, d: caption(im, 'FRONTDAN ≈2 400 KM UZOQDA', t + 2.1, d + 2.1, size=72, accent_words=('≈2', '400', 'KM')),
     credit_=CR_SBU)


def m_distance(im, t, d):
    c = cam_lerp((31, 45, 40), (28, 40, 58), t / d)
    hl = {'LBY': (120, 84, 30, 255), 'UKR': (40, 70, 120, 255)}
    im.paste(draw_map(c, hl), (0, 0))
    country_label(im, c, 31.5, 49.2, 'UKRAINA', t - 0.1, size=30)
    country_label(im, c, 18.0, 27.5, 'LIVIYA', t - 0.4, size=38, color=AMBER)
    k = clamp((t - 0.2) / 1.4)
    B = arc(im, c, (38.0, 48.3), (20.07, 32.12), ease(k), bend=0.18)
    map_label(im, c, 38.0, 48.3, 'Front chizig‘i', t, size=26, color=WHITE)
    if k >= 1:
        map_label(im, c, 20.07, 32.12, 'Bingazi', t - 1.6, size=30, anchor='r')
    if B and k > 0.4:
        x, y = B(0.5)
        f = F('InterDisplay-Black', 52)
        a = ease((t - 0.8) / 0.4)
        L = layer(); dd = ImageDraw.Draw(L)
        s = '≈2 400 km'
        dd.rectangle((x + 20, y - 40, x + 60 + text_w(f, s), y + 34), fill=(255, 178, 36, int(240 * a)))
        dd.text((x + 40, y - 34), s, font=f, fill=NAVY + (int(255 * a),))
        im.alpha_composite(L)
    caption(im, 'Afrika qirg‘og‘i · Liviya', t - 0.2, d, size=48, y=900, accent_words=('Liviya',))


gfx(4.20, 6.55, m_distance)
clip(6.55, 9.00, NIGHT_BLAST, 0.0, credit_=CR_SOC.format('Readovka (Telegram)'), tag=TAG_BNG)
clip(9.00, 11.60, SHORE_FIRE, 6.0, credit_=CR_SOC.format('Clash Report (Telegram)'), tag=TAG_BNG)


def s_merkury(im, t, d):
    im.paste(ken_burns(photo('merkury_parade'), t, d, 1.02, 1.16, 0.45, 0.5, 0.6, 0.5), (0, 0))
    vignette(im)
    lower_third(im, '«MERKURIY» KORVETI', 'Rossiya Harbiy-dengiz floti · 20380 loyihasi', t - 0.4, d)


gfx(11.60, 17.10, s_merkury, credit_=CR_MERK)


def person_card(im, t, d, key, name, role, quote=None, qdelay=0.8, fy=0.3):
    im.paste(grid_bg(t), (0, 0))
    p = photo(key)
    if p:
        bg = ken_burns(p, t, d, 1.05, 1.12, 0.5, fy, 0.5, fy, blur=28, darken=0.55)
        im.paste(bg, (0, 0))
        ph = round_photo(p, 420, 0.5, fy)
        k = ease(t / 0.5)
        L = layer(); dd = ImageDraw.Draw(L)
        cx, cy = 420, 470
        dd.ellipse((cx - 222, cy - 222, cx + 222, cy + 222), outline=AMBER + (int(255 * k),), width=8)
        L.alpha_composite(ph, (cx - 210, cy - 210))
        paste_alpha(im, L, k)
        x0 = 760
    else:
        x0 = 200
        f = F('InterDisplay-Black', 170)
        ini = ''.join(w[0] for w in name.split()[:2])
        L = layer(); dd = ImageDraw.Draw(L)
        k = ease(t / 0.5)
        dd.ellipse((200 - 0, 270, 200 + 400, 670), fill=(255, 178, 36, int(255 * k)))
        dd.text((400 - text_w(f, ini) / 2, 370), ini, font=f, fill=NAVY + (int(255 * k),))
        im.alpha_composite(L)
        x0 = 700
    fn = F('InterDisplay-ExtraBold', 64)
    fr = F('Inter-SemiBold', 32)
    k = ease((t - 0.2) / 0.4)
    L = layer(); dd = ImageDraw.Draw(L)
    dd.text((x0, 300), name, font=fn, fill=WHITE + (int(255 * k),))
    dd.text((x0, 384), role, font=fr, fill=AMBER + (int(255 * k),))
    im.alpha_composite(L)
    if quote:
        fq = F('InterDisplay-SemiBold', 46)
        lines = wrap(fq, quote, W - x0 - 140)
        kq = ease((t - qdelay) / 0.5)
        L = layer(); dd = ImageDraw.Draw(L)
        dd.text((x0 - 10, 440), '“', font=F('InterDisplay-Black', 120), fill=AMBER + (int(200 * kq),))
        for i, l in enumerate(lines):
            dd.text((x0 + 50, 520 + i * 62 + (1 - kq) * 20), l, font=fq, fill=WHITE + (int(255 * kq),))
        im.alpha_composite(L)


def s_zel1(im, t, d):
    person_card(im, t, d, 'zelensky', 'VOLODIMIR ZELENSKIY', 'Ukraina Prezidenti · 23-noyabr, dushanba',
                'Hujumni Ukraina uyushtirdi. Rossiyaning «Merkuriy» korveti cho‘ktirildi.', qdelay=1.0)


gfx(17.10, 23.40, s_zel1, credit_=None)
SC[-1]['credit_key'] = 'zelensky'
clip(23.40, 25.45, SBU, 19.0, credit_=CR_SBU)
clip(25.45, 30.40, SBU, 0.5,
     overlay=lambda im, t, d: caption(im, 'Urush tarixidagi eng uzoq masofali dengiz hujumlaridan biri', t - 0.2, d, size=50, accent_words=('uzoq', 'masofali')),
     credit_=CR_SBU)


def s_questions(im, t, d):
    im.paste(ken_burns(os.path.join(S, 'stills/sbu_ship.png'), t, d, 1.05, 1.15, blur=14, darken=0.62), (0, 0))
    f = F('InterDisplay-ExtraBold', 76)
    for i, (q, td) in enumerate([('Ukraina kemani Afrikada qanday topdi?', 0.1), ('Bu urush uchun nimani anglatadi?', 2.7)]):
        k = ease((t - td) / 0.45)
        if k <= 0:
            continue
        L = layer(); dd = ImageDraw.Draw(L)
        y = 360 + i * 170
        tw = text_w(f, q)
        dd.rectangle((W / 2 - tw / 2 - 40, y - 20, W / 2 - tw / 2 - 28, y + 96), fill=AMBER + (int(255 * k),))
        dd.text((W / 2 - tw / 2 + (1 - k) * 40, y), q, font=f, fill=WHITE + (int(255 * k),))
        im.alpha_composite(L)


gfx(30.40, 35.60, s_questions)


def bumper(title, sub=None, num=None):
    def draw(im, t, d):
        im.paste(grid_bg(t), (0, 0))
        f = F('InterDisplay-Black', 120 if len(title) < 16 else 84)
        k = ease(t / 0.35)
        L = layer(); dd = ImageDraw.Draw(L)
        tw = text_w(f, title)
        lw = (tw + 120) * ease(t / 0.5)
        y = H / 2 - 80
        dd.rectangle((W / 2 - lw / 2, y + 150, W / 2 + lw / 2, y + 160), fill=AMBER + (255,))
        dd.text((W / 2 - tw / 2, y - 10 + (1 - k) * 30), title, font=f, fill=WHITE + (int(255 * k),))
        if sub:
            fs = F('Inter-SemiBold', 40)
            k2 = ease((t - 0.3) / 0.4)
            for i, l in enumerate(wrap(fs, sub, 1500)):
                sw = text_w(fs, l)
                dd.text((W / 2 - sw / 2, y + 190 + i * 54), l, font=fs, fill=GREY + (int(255 * k2),))
        im.alpha_composite(L)
        # flash in
        if t < 0.12:
            im.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(200 * (1 - t / 0.12)))))
    return draw


gfx(35.60, 37.10, bumper('FAKTLAR'))


def m_benghazi(im, t, d):
    c = cam_lerp((18, 31, 34), (20.5, 31.6, 9), clamp(t / 4.0))
    hl = {'LBY': (60, 70, 92, 255)}
    im.paste(draw_map(c, hl), (0, 0))
    country_label(im, c, 17.5, 27.5, 'LIVIYA', t, size=44)
    country_label(im, c, 29.0, 26.5, 'MISR', t, size=34)
    if t > 3.4:
        map_label(im, c, 20.07, 32.12, 'Bingazi', t - 3.4, size=38, sub='Harbiy-dengiz bazasi')
    # date card
    panel_text(im, 1220, 120, 600, '22-NOYABR, YAKSHANBA', 'Liviya sharqidagi Bingazi shahri, harbiy-dengiz bazasi', t, delay=1.2, title_size=44)
    f = F('Inter-SemiBold', 24)
    a = ease((t - 0.3) / 0.4)
    L = layer(); dd = ImageDraw.Draw(L)
    dd.text((90, H - 90), 'MA’LUMOT: Associated Press, CBS News', font=f, fill=GREY + (int(255 * a),))
    im.alpha_composite(L)


gfx(37.10, 46.55, m_benghazi)
clip(46.55, 50.65, SHORE_FIRE, 24.0,
     overlay=lambda im, t, d: caption(im, 'Mahalliy aholi kuchli portlashlarni eshitgan va olovni ko‘rgan', t - 0.1, d, size=46, accent_words=()),
     credit_=CR_SOC.format('Clash Report (Telegram)'), tag=TAG_BNG)


def ov_seven(im, t, d):
    big_stat(im, '7', 'TA DENGIZ DRONI', 'Ukrainada ishlab chiqarilgan — Zelenskiy', t, d)


clip(50.65, 55.45, SBU, 5.5, overlay=ov_seven, darken=0.55, credit_=CR_SBU)
clip(55.45, 62.80, SBU, 24.0, speed=0.8,
     overlay=lambda im, t, d: lower_third(im, 'ZELENSKIY:', '«Merkuriy» korveti cho‘ktirildi', t - 0.5, d),
     credit_=CR_SBU)


def s_ka27(im, t, d):
    p = photo('ka27')
    if p:
        im.paste(ken_burns(p, t, d, 1.04, 1.14), (0, 0))
        vignette(im)
    else:
        im.paste(ken_burns(os.path.join(S, 'stills/sbu_ship.png'), t, d, 1.1, 1.2, blur=6, darken=0.45), (0, 0))
    lower_third(im, 'KA-27 HARBIY VERTOLYOTI', 'Zelenskiy: korvet bortida yo‘q qilingan', t - 0.3, d)


gfx(62.80, 68.40, s_ka27)
SC[-1]['credit_key'] = 'ka27'
SC[-1]['credit_fallback'] = CR_SBU
clip(68.40, 71.90, SBU, 21.0,
     overlay=lambda im, t, d: lower_third(im, 'SBU', 'Operatsiya tafsilotlarini ma’lum qildi', t - 0.2, d),
     credit_=CR_SBU)
clip(71.90, 78.65, DRONE_WAKES, 0.0, credit_=CR_SOC.format('Insider UA (Telegram)'),
     overlay=lambda im, t, d: caption(im, 'Dronlar avval belgilangan joyga yetkazilgan', t - 0.1, d, size=46, accent_words=('belgilangan', 'joyga')))


def ship(dd, x, y, w, col, kind='big'):
    h = w * 0.16
    dd.polygon([(x - w / 2, y), (x + w / 2, y), (x + w / 2 - w * 0.08, y + h), (x - w / 2 + w * 0.12, y + h)], fill=col)
    dd.rectangle((x - w * 0.2, y - h * 0.9, x + w * 0.12, y), fill=col)
    dd.rectangle((x - w * 0.12, y - h * 1.6, x - w * 0.02, y - h * 0.9), fill=col)


def s_mothership(im, t, d):
    im.paste(grid_bg(t), (0, 0))
    L = layer(); dd = ImageDraw.Draw(L)
    sea = 640
    dd.rectangle((0, sea, W, H), fill=(14, 30, 54, 255))
    for i in range(12):
        yy = sea + 20 + i * 34
        dd.line((0, yy, W, yy), fill=(24, 44, 74, 255), width=2)
    # mother ship (left) and target (right)
    k1 = ease(t / 0.5)
    ship(dd, 360, sea - 8, 380, (120, 150, 190, int(255 * k1)))
    ship(dd, 1560, sea - 8, 420, (200, 70, 60, int(255 * ease((t - 0.3) / 0.5))))
    f = F('Inter-Bold', 32)
    for (x, s, td) in [(360, 'Ona kema (dron tashuvchi)', 0.2), (1560, 'Nishon', 0.5)]:
        a = ease((t - td) / 0.4)
        tw = text_w(f, s)
        dd.text((x - tw / 2, sea + 70), s, font=f, fill=WHITE + (int(255 * a),))
    # drones
    for i in range(7):
        u = clamp((t - 0.9 - i * 0.18) / 2.6)
        if u <= 0:
            continue
        x = 520 + (1380 - 520) * ease_io(u)
        y = sea + 26 + (i - 3) * 9
        dd.line((x - 140 * min(u * 3, 1), y, x, y), fill=(200, 220, 255, 120), width=3)
        dd.polygon([(x, y - 6), (x + 26, y), (x, y + 6)], fill=AMBER + (255,))
    a = ease((t - 0.9) / 0.4)
    ff = F('Inter-Bold', 30)
    dd.text((W / 2 - text_w(ff, 'Dengiz dronlari') / 2, sea + 150), 'Dengiz dronlari', font=ff, fill=AMBER + (int(255 * a),))
    im.alpha_composite(L)
    caption(im, 'Dronlar nishon yaqinidagi ona kemadan uchirilgan', t - 0.1, d, size=50, y=170, accent_words=('ona', 'kemadan'))
    if t > 3.7:
        k = clamp((t - 3.7) / 0.3)
        im.alpha_composite(Image.new('RGBA', (W, H), (255, 200, 120, int(120 * (1 - k)))))
    f2 = F('Inter-SemiBold', 24)
    L2 = layer(); ImageDraw.Draw(L2).text((90, H - 90), 'SXEMA · MA’LUMOT: Ukraina Xavfsizlik xizmati (SBU)', font=f2, fill=GREY + (230,))
    im.alpha_composite(L2)


gfx(78.65, 83.00, s_mothership)
gfx(83.00, 84.55, bumper('MUHIM TAFSILOT'))


def s_compare(im, t, d):
    im.paste(grid_bg(t), (0, 0))
    f = F('InterDisplay-Black', 56)
    L = layer(); dd = ImageDraw.Draw(L)
    k = ease(t / 0.5)
    dd.text((W / 2 - text_w(f, 'IKKI XIL TALQIN') / 2, 90), 'IKKI XIL TALQIN', font=f, fill=WHITE + (int(255 * k),))
    im.alpha_composite(L)
    panel_text(im, 140, 220, 780, 'KIYEV (Zelenskiy)', None, t, accent=BLUE, title_size=42, delay=0.1)
    panel_text(im, 1000, 220, 780, 'LIVIYA HARBIYLARI (AP)', None, t, accent=AMBER, title_size=42, delay=2.9)
    rows_l = [('7 ta dengiz droni ishlatilgan', 0.5), ('Korvet cho‘ktirilgan', 1.2)]
    rows_r = [('Kamida 4 ta dron urib tushirilgan', 6.8), ('2 tasi kemaga tekkan', 8.2), ('Kema cho‘kmagan — jiddiy shikastlangan', 10.6)]
    for i, (s, td) in enumerate(rows_l):
        panel_text(im, 140, 340 + i * 130, 780, None, s, t, accent=BLUE, body_size=38, delay=td)
    for i, (s, td) in enumerate(rows_r):
        panel_text(im, 1000, 340 + i * 130, 780, None, s, t, accent=AMBER, body_size=38, delay=td)


gfx(84.55, 98.80, s_compare)
clip(98.80, 103.80, SHORE_FIRE, 12.0,
     overlay=lambda im, t, d: big_stat(im, '10+', 'KISHI YARALANGAN', 'Liviya va Rossiya ekipajlaridan — Liviya rasmiysi (AP)', t, d),
     darken=0.5, credit_=CR_SOC.format('Clash Report (Telegram)'))


def s_satellite(im, t, d):
    im.paste(ken_burns(photo('merkury2'), t, d, 1.05, 1.18, 0.5, 0.5, 0.55, 0.5, darken=0.6), (0, 0))
    f = F('InterDisplay-ExtraBold', 50)
    L = layer(); dd = ImageDraw.Draw(L)
    k = ease(t / 0.4)
    dd.text((140, 150), 'SUN’IY YO‘LDOSH SURATLARI NIMANI KO‘RSATMOQDA', font=f, fill=WHITE + (int(255 * k),))
    im.alpha_composite(L)
    rows = [('✓', 'Korvet ag‘darilgan', 0.3, AMBER), ('✓', 'Qisman suv ostida qolgan', 1.6, AMBER),
            ('✓', 'Hozir harakatlana olmaydi', 5.0, AMBER), ('?', 'To‘liq cho‘kkani mustaqil manbalarda tasdiqlanmagan', 8.8, RED)]
    fi = F('InterDisplay-Black', 48)
    fb = F('Inter-SemiBold', 44)
    for i, (ic, s, td, col) in enumerate(rows):
        a = ease((t - td) / 0.4)
        if a <= 0:
            continue
        L = layer(); dd = ImageDraw.Draw(L)
        y = 290 + i * 140
        off = (1 - a) * 40
        dd.rectangle((140 + off, y, 1500 + off, y + 104), fill=(9, 16, 30, int(220 * a)))
        dd.rectangle((140 + off, y, 244 + off, y + 104), fill=col + (int(255 * a),))
        dd.text((192 + off - text_w(fi, ic) / 2, y + 22), ic, font=fi, fill=NAVY + (int(255 * a),))
        dd.text((280 + off, y + 26), s, font=fb, fill=WHITE + (int(255 * a),))
        im.alpha_composite(L)


gfx(103.80, 116.80, s_satellite, credit_=CR_MERK2)
clip(116.80, 121.70, SBU, 30.0,
     overlay=lambda im, t, d: lower_third(im, 'MV «ANGARA»', 'Rossiya yuk kemasi · Zelenskiy: zarba berilgan', t - 0.4, d),
     credit_=CR_SBU)
clip(121.70, 125.60, SBU, 34.9, speed=0.77,
     overlay=lambda im, t, d: caption(im, 'Zelenskiy: Rossiya bu kemadan qurol tashish uchun foydalangan', t - 0.1, d, size=46, accent_words=('qurol',)),
     credit_=CR_SBU)
clip(125.60, 128.30, SBU, 43.0,
     overlay=lambda im, t, d: lower_third(im, 'AQSH SANKSIYALARI', '«Angara» sanksiyalar ro‘yxatida', t - 0.1, d),
     credit_=CR_SBU)
clip(128.30, 132.60, RED_CARGO, 0.0,
     overlay=lambda im, t, d: caption(im, 'Ukraina: «Merkuriy» aynan shu kemani kuzatib borgan', t - 0.1, d, size=48, accent_words=('«Merkuriy»',)),
     credit_=CR_SOC.format('Insider UA (Telegram)'))


def s_timeline(im, t, d):
    im.paste(ken_burns(photo('merkury_parade'), t, d, 1.1, 1.2, 0.5, 0.5, 0.45, 0.5, blur=10, darken=0.7), (0, 0))
    L = layer(); dd = ImageDraw.Draw(L)
    y = 560
    k = ease_io(clamp(t / 1.2))
    dd.line((160, y, 160 + (W - 320) * k, y), fill=AMBER + (255,), width=6)
    im.alpha_composite(L)
    pts = [(300, '2023-YIL MAY', 'Flotga qabul qilingan (TASS)', 0.3),
           (960, 'VAZIFASI', 'Qirg‘oq suvlarini patrullash, boshqa kemalarni kuzatib borish', 5.7),
           (1620, '2026-YIL 22-NOYABR', 'Bingazida dron hujumi', 9.5)]
    for x, ti, sb, td in pts:
        a = ease((t - td) / 0.4)
        if a <= 0:
            continue
        L = layer(); dd = ImageDraw.Draw(L)
        dd.ellipse((x - 18, y - 18, x + 18, y + 18), fill=AMBER + (int(255 * a),), outline=NAVY + (int(255 * a),), width=5)
        ft = F('InterDisplay-ExtraBold', 44)
        fb = F('Inter-Medium', 32)
        tw = text_w(ft, ti)
        dd.text((x - tw / 2, y - 110 + (1 - a) * 20), ti, font=ft, fill=WHITE + (int(255 * a),))
        for i, l in enumerate(wrap(fb, sb, 520)):
            lw = text_w(fb, l)
            dd.text((x - lw / 2, y + 50 + i * 44), l, font=fb, fill=GREY + (int(255 * a),))
        im.alpha_composite(L)
    f = F('InterDisplay-Black', 64)
    L = layer(); ImageDraw.Draw(L).text((160, 160), '«MERKURIY» KORVETI', font=f, fill=WHITE + (int(255 * ease(t / 0.4)),))
    im.alpha_composite(L)


gfx(132.60, 144.20, s_timeline, credit_=CR_MERK)
gfx(144.20, 147.70, bumper('NIMA UCHUN LIVIYA?', 'Rossiya harbiy kemasi Liviyada nima qilayotgan edi?'))

WEST_POLY = [(9.0, 34.0), (16.6, 34.0), (16.6, 30.2), (14.5, 29.0), (9.0, 29.0)]


def libya_split(im, c, t):
    from shapely.geometry import Polygon
    lby = [g for a3, n, g in geo() if a3 == 'LBY'][0]
    west = lby.intersection(Polygon(WEST_POLY))
    east = lby.difference(Polygon(WEST_POLY))
    S2 = 2
    L = Image.new('RGBA', (W * S2, H * S2), (0, 0, 0, 0))
    dd = ImageDraw.Draw(L)
    for g, col, td in [(west, (70, 140, 230), 0.2), (east, (255, 178, 36), 2.0)]:
        a = ease((t - td) / 0.6)
        for p in ([g] if g.geom_type == 'Polygon' else g.geoms):
            pts = [(c.xy(x, y)[0] * S2, c.xy(x, y)[1] * S2) for x, y in p.exterior.coords]
            dd.polygon(pts, fill=col + (int(150 * a),))
    im.alpha_composite(L.resize((W, H), Image.LANCZOS))


def m_split(im, t, d):
    c = Cam(17.5, 28.5, 24)
    im.paste(draw_map(c, {'LBY': (52, 64, 86, 255)}), (0, 0))
    libya_split(im, c, t - 0.2)
    map_label(im, c, 13.19, 32.89, 'Tripoli', t - 3.3, size=30, anchor='r')
    map_label(im, c, 20.07, 32.12, 'Bingazi', t - 7.6, size=30)
    panel_text(im, 90, 650, 640, 'G‘ARB · TRIPOLI', 'Abdulhamid Dbeyba hukumati', t, accent=BLUE, delay=3.3)
    panel_text(im, 1190, 650, 660, 'SHARQ VA JANUB · BINGAZI', 'General Xalifa Haftar boshchiligidagi kuchlar', t, accent=AMBER, delay=7.6)
    for key, x, td in (('dbeibah', 90 + 20, 3.5), ('haftar', 1190 + 20, 7.8)):
        p = photo(key)
        if p:
            a = ease((t - td) / 0.4)
            ph = round_photo(p, 150, 0.5, 0.3)
            L = layer(); L.alpha_composite(ph, (x, 480))
            paste_alpha(im, L, a)
    caption(im, 'Liviya bir necha yildan beri amalda ikkiga bo‘lingan', t, 3.2, size=48, y=110, accent_words=('ikkiga',))
    f = F('Inter-SemiBold', 22)
    L = layer(); ImageDraw.Draw(L).text((90, H - 60), 'Nazorat hududlari taxminiy', font=f, fill=GREY + (200,))
    im.alpha_composite(L)


gfx(147.70, 160.90, m_split)
SC[-1]['credit_key'] = 'haftar'


def m_moscow(im, t, d):
    c = cam_lerp((17.5, 28.5, 24), (29, 44, 68), clamp(t / 2.2))
    im.paste(draw_map(c, {'LBY': (52, 64, 86, 255), 'RUS': (110, 50, 50, 255)}), (0, 0))
    k = clamp((t - 1.6) / 1.4)
    arc(im, c, (37.62, 55.75), (20.07, 32.12), ease(k), color=RED, bend=-0.2, head=True)
    map_label(im, c, 37.62, 55.75, 'Moskva', t - 1.6, size=30)
    map_label(im, c, 20.07, 32.12, 'Bingazi', t - 1.0, size=30, anchor='r')
    caption(im, 'Sharqiy hukumat Moskva bilan yaqin harbiy aloqalarga ega', t - 0.2, 3.6, size=48, y=110, accent_words=('Moskva',))
    panel_text(im, 1080, 640, 760, 'SHARQIY HUKUMAT BAYONOTI', '«Merkuriy» Bingaziga hamkorlik kelishuvi asosida yoqilg‘i va oziq-ovqat olish uchun kirgan', t, accent=AMBER, delay=3.7)


gfx(160.90, 172.60, m_moscow)


def m_med(im, t, d):
    c = Cam(24, 31, 40)
    im.paste(draw_map(c, {'LBY': (120, 84, 30, 255), 'SYR': (110, 50, 50, 255)}), (0, 0))
    country_label(im, c, 38.5, 35.0, 'SURIYA', t, size=30)
    country_label(im, c, 17.5, 27.0, 'LIVIYA', t, size=40, color=AMBER)
    arc(im, c, (35.9, 34.9), (20.07, 32.12), ease(clamp((t - 0.6) / 1.4)), color=RED, bend=0.15)
    arc(im, c, (20.07, 32.12), (17.0, 16.0), ease(clamp((t - 2.6) / 1.4)), color=RED, bend=-0.1)
    country_label(im, c, 16.0, 14.5, 'AFRIKA ICHKARISI', t - 3.6, size=28)
    panel_text(im, 1080, 700, 760, 'AP', 'Rossiya Liviyadan Suriya bilan O‘rtayer dengizi janubi o‘rtasidagi tayanch nuqta va tranzit markazi sifatida foydalanadi', t, accent=RED, delay=1.0)


gfx(172.60, 181.45, m_med)


def m_west(im, t, d):
    c = cam_lerp((17.5, 30.5, 20), (16.6, 32.0, 11), clamp(t / 2))
    im.paste(draw_map(c, {'LBY': (52, 64, 86, 255)}), (0, 0))
    map_label(im, c, 15.09, 32.38, 'Misrata', t - 2.0, size=30)
    map_label(im, c, 13.19, 32.89, 'Tripoli', t - 2.8, size=30, dy=-40)
    map_label(im, c, 12.73, 32.76, 'Zaviya', t - 3.6, size=30, anchor='r', dy=10)
    map_label(im, c, 20.07, 32.12, 'Bingazi', t - 1.0, size=30)
    panel_text(im, 90, 700, 900, 'AP VA CBS MA’LUMOTI', 'Ukrainalik harbiylar (asosan dron mutaxassislari) g‘arbiy Liviyada yashirin kelishuv asosida faoliyat yuritadi', t, accent=BLUE, delay=0.6)
    k = clamp((t - 12.0) / 1.5)
    if k > 0:
        arc(im, c, (13.8, 33.1), (19.9, 32.3), ease(k), color=AMBER, bend=-0.1, dashed=True)
        panel_text(im, 1100, 200, 740, 'LIVIYA RASMIYLARI', 'Dronlar aynan g‘arbdagi shunday bazadan uchirilgan', t, accent=AMBER, delay=12.2)


gfx(181.45, 197.70, m_west)


def m_malta(im, t, d):
    c = cam_lerp((16.6, 32.0, 11), (16.5, 34.0, 16), clamp(t / 1.5))
    im.paste(draw_map(c, {'LBY': (52, 64, 86, 255)}), (0, 0))
    map_label(im, c, 14.51, 35.9, 'Malta', t - 1.0, size=30)
    map_label(im, c, 15.6, 34.6, '«Arctic Metagaz»', t - 3.6, size=30, color=AMBER, sub='SGT tankeri', anchor='r', dy=40)
    caption(im, 'Ukrainaning O‘rtayer dengizidagi birinchi harakati emas', t, 3.4, size=48, y=110, accent_words=('birinchi',))
    panel_text(im, 1080, 650, 760, '2026-YIL MART', 'Rossiyaning suyultirilgan gaz tashuvchi tankeri dengiz dronlari hujumidan jiddiy shikastlangan', t, accent=RED, delay=3.4)
    panel_text(im, 1080, 880, 760, None, 'Moskva o‘shanda ham Ukrainani aybladi', t, accent=RED, delay=12.2, body_size=34)


gfx(197.70, 212.40, m_malta)
gfx(212.40, 215.30, bumper('NEGA BU MUHIM?'))


def m_geo(im, t, d):
    c = cam_lerp((25, 48.5, 96), (25, 48.2, 84), clamp(t / 6))
    im.paste(draw_map(c, {'RUS': (90, 44, 44, 255), 'UKR': (40, 70, 120, 255), 'FIN': (52, 64, 86, 255), 'LBY': (52, 64, 86, 255)}), (0, 0))
    for i, (lon, lat, td) in enumerate([(26.5, 59.9, 2.8), (20.07, 32.12, 14.0)]):
        if t > td:
            r = 40 + 80 * (((t - td) * 0.5) % 1)
            x, y = c.xy(lon, lat)
            L = layer(); dd = ImageDraw.Draw(L)
            dd.ellipse((x - r, y - r, x + r, y + r), outline=RED + (int(200 * (1 - ((t - td) * 0.5) % 1)),), width=4)
            im.alpha_composite(L)
    map_label(im, c, 26.5, 59.9, 'Fin ko‘rfazi', t - 2.8, size=30, sub='Rossiya bilan bog‘liq yuk kemasi yonib ketdi', anchor='r', dy=50)
    map_label(im, c, 20.07, 32.12, 'Bingazi', t - 14.0, size=30)
    section_num(im, 1, 'URUSH GEOGRAFIYASI KENGAYMOQDA', t, d + 1)
    panel_text(im, 1180, 560, 680, 'FINLANDIYA HARBIYLARI', 'Ukraina aloqador bo‘lishi ehtimoli bor', t, accent=AMBER, delay=9.9)
    panel_text(im, 1180, 760, 680, 'KIYEV', 'Buni na tasdiqladi, na rad etdi', t, accent=BLUE, delay=14.1)


gfx(215.30, 232.30, m_geo)
clip(232.30, 240.90, DAY_SMOKE, 0.0, speed=0.75,
     overlay=lambda im, t, d: (section_num(im, 1, 'URUSH GEOGRAFIYASI KENGAYMOQDA', t + 5, d + 5),
                               caption(im, 'SBU: Rossiya floti uchun Qora dengizdan uzoqda ham xavfsiz yo‘l yo‘q', t - 0.2, d, size=46, maxw=1700, accent_words=('xavfsiz', 'yo‘l', 'yo‘q'))),
     credit_=CR_SOC.format('Insider UA (Telegram)'))
clip(240.90, 246.70, SHORE_FIRE, 40.0,
     overlay=lambda im, t, d: section_num(im, 2, 'LIVIYANING O‘ZI XAVF OSTIDA', t, d + 1),
     credit_=CR_SOC.format('Clash Report (Telegram)'), tag=TAG_BNG)


def s_un(im, t, d):
    im.paste(ken_burns(os.path.join(S, 'stills/sbu_ship.png'), t, d, 1.2, 1.3, blur=20, darken=0.72), (0, 0))
    section_num(im, 2, 'LIVIYANING O‘ZI XAVF OSTIDA', t + 5, d + 5)
    f = F('InterDisplay-Black', 58)
    L = layer(); dd = ImageDraw.Draw(L)
    k = ease(t / 0.4)
    dd.text((140, 200), 'BMTNING LIVIYADAGI MISSIYASI', font=f, fill=(120, 180, 255, int(255 * k)))
    im.alpha_composite(L)
    panel_text(im, 140, 320, 1640, None, 'Jiddiy xavotir bildirdi va zudlik bilan mustaqil, shaffof tergov o‘tkazishga chaqirdi', t, accent=BLUE, body_size=44, delay=0.3)
    panel_text(im, 140, 540, 1640, None, '«Liviya xorijiy mojarolar maydoniga aylanmasligi kerak»', t, accent=BLUE, body_size=48, delay=3.3)


gfx(246.70, 254.90, s_un)


def s_govs(im, t, d):
    im.paste(grid_bg(t), (0, 0))
    section_num(im, 2, 'LIVIYANING O‘ZI XAVF OSTIDA', t + 5, d + 5)
    panel_text(im, 140, 260, 780, 'G‘ARBIY HUKUMAT (TRIPOLI)', 'Mamlakatni xalqaro mojarolar maydoniga aylantirishni qat’iyan rad etadi', t, accent=BLUE, delay=0.1, body_size=36)
    panel_text(im, 1000, 260, 780, 'SHARQIY HUKUMAT (BINGAZI)', 'Rossiya bilan birgalikda tergov boshladi', t, accent=AMBER, delay=5.1, body_size=36)
    panel_text(im, 1000, 520, 780, None, 'Barcha zarur vositalar bilan javob berish huquqini saqlab qoladi', t, accent=RED, delay=8.4, body_size=36)


gfx(254.90, 268.30, s_govs)


def m_lanes(im, t, d):
    c = Cam(18, 36, 42)
    im.paste(draw_map(c, {}), (0, 0))
    lanes = [((-5.6, 36.0), (32.3, 31.3)), ((-5.6, 36.0), (12.0, 38.0)), ((12.0, 38.0), (32.3, 31.3)), ((15, 37), (29.0, 41.0)), ((10.0, 37.3), (20.0, 33.0))]
    for i, (a, b) in enumerate(lanes):
        arc(im, c, a, b, ease(clamp((t - i * 0.25) / 1.2)), color=(120, 180, 255), width=3, bend=0.04, dashed=True, head=False, phase=t * 3)
    map_label(im, c, 20.07, 32.12, 'Bingazi', t - 0.8, size=28)
    section_num(im, 3, 'DENGIZ YO‘LLARI', t, d + 1)
    caption(im, 'O‘rtayer dengizi — dunyoning eng gavjum savdo yo‘llaridan biri', t - 0.3, d, size=48, accent_words=('gavjum', 'savdo'))


gfx(268.30, 273.80, m_lanes)
clip(273.80, 279.90, CARGO_HIT, 0.0, speed=0.85,
     overlay=lambda im, t, d: (section_num(im, 3, 'DENGIZ YO‘LLARI', t + 5, d + 5),
                               lower_third(im, 'SAVDO KEMASIGA ZARBA', 'Malta bayrog‘i ostida · Bingazi yaqinida', t - 0.3, d)),
     credit_=CR_SOC.format('Telegram'))
clip(279.90, 285.00, CARGO_V, 5.0,
     overlay=lambda im, t, d: (section_num(im, 3, 'DENGIZ YO‘LLARI', t + 5, d + 5),
                               caption(im, 'Ekipaj evakuatsiya qilindi · Xalqaro yuk tashish xavfi ortmoqda', t - 0.1, d, size=46, accent_words=('xavfi',))),
     credit_=CR_SOC.format('Meduza (Telegram)'))
gfx(285.00, 286.70, bumper('ENDI NIMA BO‘LADI?'))


def s_kremlin(im, t, d):
    im.paste(grid_bg(t), (0, 0))
    panel_text(im, 240, 300, 1440, 'KREML', 'Hozircha rasmiy izoh bermadi', t, accent=RED, delay=0.0, title_size=56, body_size=44)
    panel_text(im, 240, 560, 1440, 'ROSSIYA MUDOFAA VAZIRLIGI', 'Ma’lumot keyinroq berilishini aytdi', t, accent=RED, delay=2.2, title_size=56, body_size=44)


gfx(286.70, 292.00, s_kremlin)


def s_expert(im, t, d):
    person_card(im, t, d, '_none_', 'JALEL HARCHAOUI', 'Qirollik mudofaa tadqiqotlari instituti (RUSI), London',
                'Ukrainaning bu zarbalari hayratlanarli darajada dadil va provokatsion.', qdelay=4.3)
    panel_text(im, 700, 820, 1080, None, 'Endi asosiy savol — Rossiya qanday javob qaytarishi', t, accent=AMBER, delay=9.1, body_size=40)
    f = F('Inter-SemiBold', 22)
    L = layer(); ImageDraw.Draw(L).text((90, H - 60), 'MANBA: Associated Press', font=f, fill=GREY + (220,))
    im.alpha_composite(L)


gfx(292.00, 305.70, s_expert)


def s_diplomacy(im, t, d):
    im.paste(grid_bg(t), (0, 0))
    f = F('InterDisplay-Black', 60)
    L = layer(); dd = ImageDraw.Draw(L)
    k = ease(t / 0.4)
    dd.text((160, 150), 'DIPLOMATIYA', font=f, fill=WHITE + (int(255 * k),))
    fs = F('Inter-SemiBold', 30)
    dd.text((160, 230), 'Hujum diplomatik jarayonga ham ta’sir qilishi mumkin', font=fs, fill=GREY + (int(255 * k),))
    im.alpha_composite(L)
    y = 600
    kk = ease_io(clamp((t - 3.0) / 1.5))
    L = layer(); dd = ImageDraw.Draw(L)
    dd.line((200, y, 200 + 1520 * kk, y), fill=AMBER + (255,), width=6)
    # pause segment
    if kk > 0.2:
        x0, x1 = 360, 1320
        dd.rectangle((x0, y - 10, x0 + (x1 - x0) * clamp((kk - 0.2) / 0.6), y + 10), fill=(90, 100, 120, 255))
    im.alpha_composite(L)
    pts = [(360, 'MUZOKARALAR TO‘XTADI', '', 3.4), (840, '9 OYLIK TANAFFUS', '', 4.2), (1320, '2026-YIL NOYABR BOSHI', 'AQSH vositachiligida muzokaralar qayta tiklandi (TIME)', 5.0)]
    for x, ti, sb, td in pts:
        a = ease((t - td) / 0.4)
        if a <= 0:
            continue
        L = layer(); dd = ImageDraw.Draw(L)
        dd.ellipse((x - 16, y - 16, x + 16, y + 16), fill=AMBER + (int(255 * a),))
        ft = F('InterDisplay-ExtraBold', 36)
        dd.text((x - text_w(ft, ti) / 2, y - 80), ti, font=ft, fill=WHITE + (int(255 * a),))
        fb = F('Inter-Medium', 30)
        for i, l in enumerate(wrap(fb, sb, 560)):
            dd.text((x - text_w(fb, l) / 2, y + 40 + i * 40), l, font=fb, fill=GREY + (int(255 * a),))
        im.alpha_composite(L)
    panel_text(im, 460, 830, 1000, None, 'Ammo tinchlikka olib boradigan aniq yo‘l hali ko‘rinmayapti', t, accent=RED, delay=10.8, body_size=38)


gfx(305.70, 320.10, s_diplomacy)


def s_zel2(im, t, d):
    person_card(im, t, d, 'zelensky', 'VOLODIMIR ZELENSKIY', 'Berlin · NATO Parlament Assambleyasi',
                'Bugun Rossiya javobimizni neftni qayta ishlash zavodlari yonayotgan Sibirdan tortib, harbiy kemalari cho‘kayotgan Liviya qirg‘og‘igacha his qilmoqda.', qdelay=3.8)


gfx(320.10, 333.00, s_zel2)
SC[-1]['credit_key'] = 'zelensky'
clip(333.00, 338.30, SBU, 38.0, speed=0.85,
     overlay=lambda im, t, d: caption(im, 'Urush endi front chizig‘i bilan cheklanib qolmayapti', t - 0.1, d, size=52, accent_words=('front', 'chizig‘i')),
     credit_=CR_SBU)
clip(338.30, 345.70, DRONE_WAKES, 9.0, speed=0.9,
     overlay=lambda im, t, d: caption(im, 'Arzon va uzoqqa yetadigan dengiz dronlari minglab kilometr uzoqdagi kemani ham nishonga aylantirmoqda', t - 0.1, d, size=46, accent_words=('Arzon', 'minglab', 'kilometr')),
     credit_=CR_SOC.format('Insider UA (Telegram)'))


def s_cta(im, t, d):
    im.paste(ken_burns(os.path.join(S, 'stills/sbu_day.png'), t, d, 1.05, 1.15, blur=16, darken=0.7), (0, 0))
    f = F('InterDisplay-ExtraBold', 66)
    lines = wrap(f, 'Urushning boshqa qit’alarga yoyilishi tinchlikni yaqinlashtiradimi yoki uzoqlashtiradimi?', 1500)
    k = ease(t / 0.5)
    L = layer(); dd = ImageDraw.Draw(L)
    for i, l in enumerate(lines):
        dd.text((W / 2 - text_w(f, l) / 2, 300 + i * 84 + (1 - k) * 20), l, font=f, fill=WHITE + (int(255 * k),))
    im.alpha_composite(L)
    k2 = ease((t - 7.2) / 0.5)
    if k2 > 0:
        fb = F('InterDisplay-Bold', 48)
        s = 'Fikringizni izohlarda yozib qoldiring'
        L = layer(); dd = ImageDraw.Draw(L)
        tw = text_w(fb, s)
        dd.rectangle((W / 2 - tw / 2 - 40, 700, W / 2 + tw / 2 + 40, 790), fill=AMBER + (int(255 * k2),))
        dd.text((W / 2 - tw / 2, 716), s, font=fb, fill=NAVY + (int(255 * k2),))
        im.alpha_composite(L)
    if t > d - 1.0:
        im.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * clamp((t - (d - 1.0)) / 1.0)))))


gfx(345.70, TOTAL, s_cta)

# sanity: contiguous
for a, b in zip(SC, SC[1:]):
    assert abs(a['t1'] - b['t0']) < 1e-6, (a['t0'], b['t0'])
