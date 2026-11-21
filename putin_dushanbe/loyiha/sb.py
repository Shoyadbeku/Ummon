"""Storyboard: every shot, overlay, credit and SFX cue, timed to the voice-over."""
import json, os
from engine import *

A = os.path.join(ROOT, 'assets'); CL = os.path.join(ROOT, 'clips')
TOTAL = 381.5
CB_META = json.load(open(os.path.join(ROOT, 'web/commons_base.json')))
CB_KEYS = list(CB_META.keys())

CR_K = 'FOTO: kremlin.ru · CC BY 4.0'
CR_KV = 'VIDEO: kremlin.ru · CC BY 4.0'
CR_MOD_V = 'VIDEO: Rossiya Mudofaa vazirligi (mil.ru) / Wikimedia Commons · CC BY 4.0'
CR_MOD_P = 'FOTO: Rossiya Mudofaa vazirligi (mil.ru) / Wikimedia Commons · CC BY 4.0'
CR_PRES = 'FOTO: Rossiya Prezidenti matbuot xizmati / Wikimedia Commons · CC BY 4.0'
CR_GOV = 'FOTO: TASS / Valeriy Sharifulin · government.ru'
CR_MAP = 'XARITA: Natural Earth (public domain) · grafika: muallif'
CR_GFX = None
EXTRA_CR = {
    0: 'FOTO: Bradley Lail / ISAF, Wikimedia Commons · CC BY 2.0',
    1: 'FOTO: Bradley Lail / ISAF, Wikimedia Commons · CC BY 2.0',
    2: 'ARXIV FOTO: A. Solomonov / RIA Novosti, Wikimedia Commons · CC BY-SA 3.0',
    3: 'FOTO: Khwahan / Wikimedia Commons · CC BY-SA 3.0',
    4: 'FOTO: Ninara / Wikimedia Commons · CC BY 2.0',
    5: 'FOTO: Ninara / Wikimedia Commons · CC BY 2.0',
    6: 'FOTO: Solijonovm1996 / Wikimedia Commons · CC BY-SA 4.0',
    7: 'FOTO: Drksll / Wikimedia Commons · CC BY-SA 4.0',
    8: 'FOTO: Citiguide / Wikimedia Commons · CC BY-SA 3.0',
}


def K(pid, **kw): return ImgSrc(f'{A}/kremlin/{pid}.jpg', **kw), CR_K
def KV(name, off=0, speed=1.0): return VidSrc(f'{CL}/{name}.mp4', off, speed), CR_KV
def CW(i, off=0, speed=1.0): return VidSrc(f'{A}/commons/base_{i:02d}.webm', off, speed), CR_MOD_V
def CB(i, **kw):
    ext = 'jpeg' if 29 <= i <= 36 else 'jpg'
    cr = CR_PRES if 28 <= i <= 36 else CR_MOD_P
    return ImgSrc(f'{A}/commons/base_{i:02d}.{ext}', **kw), cr
def EX(i, **kw): return ImgSrc(f'{A}/commons/extra_{i:02d}.jpg', **kw), EXTRA_CR[i]
def G(i, **kw): return ImgSrc(f'{A}/gov/kabul_{i}.jpg', **kw), CR_GOV
def CARD(): return CardSrc(), None
def MAP(**kw): return MapSrc(**kw), CR_MAP


SHOTS = []
def shot(s, e, sc, tr='fade', note=''):
    src, cr = sc
    SHOTS.append(dict(s=s, e=e, src=src, credit=cr, tr=tr, note=note))

OV = []
SFX = []  # (time, kind, extra)
def sfx(t, kind, x=None): SFX.append((t, kind, x))

TJ = (204, 40, 52); UZ = (30, 136, 229)

# ============================== HOOK =====================================
shot(0.0, 1.6, K('81303_20', z0=1.0, z1=1.08), 'cut', 'Shenzhen: Si, Putin, Tramp')
shot(1.6, 3.2, K('81303_07', z0=1.06, z1=1.0), 'flash', 'Uch rahbar yaqin plan')
shot(3.2, 5.0, K('81303_01', z0=1.0, z1=1.1), 'cut', 'Bir stol atrofida')
shot(5.0, 7.6, K('81285_10', z0=1.02, z1=1.12, fx=.62), 'whip', 'APEC China 2026, Putin samolyoti')
shot(7.6, 9.6, K('81308_01', z0=1.0, z1=1.1), 'fade', 'Dushanbe aeroporti, ROSSIYA samolyoti')
shot(9.6, 13.8, K('81245_02', z0=1.0, z1=1.12, fy=.4), 'fade', 'Moskva, 12-noyabr: Putin va Rahmon')
shot(13.8, 16.5, K('81308_02', z0=1.0, z1=1.1), 'fade', 'Dushanbe: samolyot yonida')
shot(16.5, 17.7, CARD(), 'flash', 'NEGA?')
shot(17.7, 20.1, K('81313_02', z0=1.0, z1=1.08), 'cut', 'Dushanbe muzokaralari')
shot(20.1, 23.8, CW(25, 18.0), 'flash', '201-baza: T-72 o‘q otmoqda')
shot(23.8, 30.9, MAP(cam=[(0, 66, 39.5, 30), (7, 67.5, 39.2, 22)], hi=[('TJK', TJ, .2, 99), ('UZB', UZ, 2.3, 99)],
                     cities=[('Dushanbe', 68.77, 38.56, .6, 'star'), ('Toshkent', 69.29, 41.31, 2.6, 'small')]),
     'whip', 'Xarita: Tojikiston va Oʻzbekiston')
shot(30.9, 33.0, CARD(), 'flash', 'Sarlavha')
OV += [LocTag(0.15, 4.9, 'SHENZHEN, XITOY · 19-NOYABR'), Flash(0.0, .3),
       LocTag(9.8, 13.6, 'MOSKVA · 12-NOYABR'),
       Kinetic(16.5, 17.7, ['NEGA?'], size=220, dim=0, accent_word='NEGA'),
       LowerThird(20.3, 23.6, 'Rossiyaning 201-harbiy bazasi', 'Tojikiston', tag='ASOSIY MAVZU'),
       Kinetic(30.95, 33.0, ['PUTIN DUSHANBEDA'], size=120, dim=0, sub='201-baza va Markaziy Osiyo xavfsizligi')]
for t in (0.0, 16.5, 20.1, 31.0): sfx(t, 'impact')
for t in (1.6, 5.0, 23.8): sfx(t, 'whoosh')
sfx(29.0, 'riser', 2.0)

# ============================== 1. TASHRIF ================================
OV.append(Chapter(33.4, 93.9, '1', 'DUSHANBE TASHRIFI'))
shot(33.0, 36.0, K('81308_00', z0=1.0, z1=1.1), 'fade', 'Tungi kutib olish')
shot(36.0, 38.6, K('81308_04', z0=1.08, z1=1.0, fx=.6), 'fade', 'Faxriy qorovul')
shot(38.6, 42.2, K('81308_03', z0=1.0, z1=1.1, fy=.4), 'fade', 'Qoʻl siqish')
shot(42.2, 45.8, K('81313_23', z0=1.0, z1=1.12), 'fade', 'Saroy zali, keng plan')
shot(45.8, 51.7, K('81313_20', z0=1.0, z1=1.1), 'fade', 'Muzokaralar')
shot(51.7, 56.0, K('81313_03', z0=1.12, z1=1.0), 'fade', 'Muzokaralar, keng')
shot(56.0, 59.4, CW(26, 5.0), 'whip', 'Bazadagi vertolyotlar')
shot(59.4, 62.3, KV('csto_hall', 1), 'fade', 'ODKB sessiyasi, Kreml')
shot(62.3, 64.8, KV('csto_table', 1), 'fade', 'ODKB stoli')
shot(64.8, 68.0, KV('csto_putin', 1), 'fade', 'Putin ODKBda')
shot(68.0, 71.6, KV('csto_rahmon', 1), 'fade', 'Rahmon ODKBda')
shot(71.6, 75.8, K('81313_05', z0=1.0, z1=1.1), 'fade', 'Qoʻl siqish')
shot(75.8, 78.2, K('81313_12', z0=1.08, z1=1.0), 'fade', 'Bayroqlar oldida')
shot(78.2, 83.0, K('81313_01', z0=1.0, z1=1.12, fx=.55), 'fade', 'Saroy hovlisi')
shot(83.0, 87.9, K('81313_17', z0=1.0, z1=1.1), 'fade', 'Aurus, bayroqlar')
shot(87.9, 94.2, CW(13, 84.0), 'whip', 'Shtab mashgʻuloti')
OV += [LocTag(33.3, 39.5, 'DUSHANBE · 20-NOYABR 2026'),
       LowerThird(38.8, 44.8, 'Ishchi tashrif', 'Davlat tashrifi emas — aniq masalalar boʻyicha uchrashuv', tag='RASMIY MAQOM'),
       LowerThird(51.9, 55.9, 'ODKB doirasidan tashqarida', 'Xavfsizlik — ikki tomonlama formatda', tag='PUTIN'),
       LocTag(59.6, 71.4, 'ARXIV · ODKB SESSIYASI, MOSKVA · 11-NOYABR'),
       FactBox(59.6, 64.7, 'ODKB', ['Kollektiv xavfsizlik shartnomasi tashkiloti', 'Rossiya boshchiligidagi harbiy ittifoq'],
               pos='right', y=330, width=720),
       FactBox(78.5, 87.7, 'KREML: D. PESKOV', ['Putin muzokaralarda qatnashgan harbiylar va Mudofaa vazirligi vakillari bilan alohida suhbat oʻtkazgan'],
               pos='left', y=330, width=820),
       FactBox(88.2, 94.0, 'IGOR KOSTYUKOV', ['Rossiya harbiy razvedkasi rahbari', 'Rossiya matbuoti xabariga koʻra, suhbatda ishtirok etgan'],
               pos='left', y=330, width=820)]
for t in (38.8, 51.9, 56.0, 59.6, 78.5, 87.9): sfx(t, 'whoosh')
sfx(92.2, 'riser', 2.0)

# ============================== 2. 201-BAZA ===============================
OV.append(Chapter(94.6, 153.8, '2', '201-HARBIY BAZA'))
shot(94.2, 98.0, CW(10, 0.3), 'flash', 'Baza askarlari')
shot(98.0, 100.8, CB(0, z0=1.0, z1=1.1), 'fade', 'Baza darvozasi')
shot(100.8, 105.6, EX(2, z0=1.0, z1=1.08, fy=.55), 'fade', 'Arxiv 1989: Termiz koʻprigi, sovet qoʻshinlari')
shot(105.6, 108.5, CB(9, z0=1.0, z1=1.1), 'fade', 'Baza shtabi binosi')
shot(108.5, 112.9, MAP(cam=[(0, 69.5, 38.6, 9), (4.4, 69.0, 38.3, 6.5)], hi=[('TJK', TJ, 0, 99)],
                       cities=[('DUSHANBE — shtab', 68.77, 38.56, .3, 'star'), ('BOKHTAR — garnizon', 68.77, 37.84, 1.5, 'star')],
                       country_labels=('UZB', 'AFG', 'KGZ')), 'whip', 'Xarita: Dushanbe, Bokhtar')
shot(112.9, 114.5, CW(25, 70.5), 'whip', 'Tank')
shot(114.5, 115.6, CB(2, z0=1.0, z1=1.06), 'cut', 'Artilleriya')
shot(115.6, 116.6, CB(17, z0=1.0, z1=1.06), 'cut', 'Razvedka')
shot(116.6, 117.9, CB(4, z0=1.0, z1=1.06), 'cut', 'BTR kolonnasi')
shot(117.9, 122.9, CW(26, 20.5), 'fade', 'Poligon, BMP')
shot(122.9, 126.0, CB(29, z0=1.0, z1=1.1), 'fade', '2012: Putin bazada')
shot(126.0, 129.9, CB(32, z0=1.0, z1=1.1), 'fade', '2012: Putin va Rahmon bazada')
shot(129.9, 138.4, KV('pc_quote', 3.0), 'fade', 'Shenzhen matbuot anjumani — iqtibos')
shot(138.4, 143.4, K('81313_16', z0=1.0, z1=1.1), 'fade', 'Qoʻl siqish')
shot(143.4, 150.0, K('81313_06', z0=1.12, z1=1.0), 'fade', 'Bayroqlar oldida')
shot(150.0, 154.0, K('81313_21', z0=1.0, z1=1.1), 'fade', 'Norasmiy davom')
TL = [(101.0, 'SOVET DAVRI', '201-motoʻqchi\ndiviziya'), (105.7, '2004', 'Harbiy baza\nrasmiylashtirildi'),
      (123.0, '2012', 'Muddatni uzaytirish\nkelishuvi'), (127.3, '2042', 'Kelishuv\nmuddati')]
OV += [Kinetic(94.3, 97.8, ['201-BAZA', 'NIMA?'], size=150, dim=.45, accent_word='NIMA'),
       LowerThird(98.2, 100.7, '201-Rossiya harbiy bazasi', 'Shtab: Dushanbe', tag='HARBIY BAZA'),
       LocTag(101.0, 105.4, 'ARXIV · 1989'),
       Timeline(100.9, 108.4, TL), Timeline(122.95, 129.8, TL),
       LocTag(112.9, 114.5, 'TANK'), LocTag(114.5, 115.6, 'ARTILLERIYA'), LocTag(115.6, 116.6, 'RAZVEDKA'),
       LocTag(116.6, 117.9, 'HAVO HUJUMIDAN MUDOFAA'),
       FactBox(118.1, 122.7, 'XORIJDAGI ENG YIRIK', ['Rossiya matbuoti bazani mamlakatning xorijdagi eng yirik harbiy obyekti deb ataydi'],
               pos='left', y=300, width=800),
       LocTag(123.1, 129.7, 'ARXIV · 201-BAZA, 5-OKTABR 2012'),
       Quote(130.2, 138.2, '201-baza — mintaqadagi xavfsizlikning juda yaxshi, real kafolati.', 'Vladimir Putin',
             'Shenzhen, 19-noyabr · matbuot anjumani'),
       FactBox(143.7, 149.8, 'D. PESKOV', ['Baza — barqarorlik uchun “yaxshi element”', 'Tomonlar oʻrtasida “toʻliq tushunish” bor'],
               pos='right', y=300, width=760),
       LowerThird(150.2, 153.8, 'Yangi hujjat imzolangani haqida xabar yoʻq', None, tag='HOZIRCHA')]
sfx(94.2, 'impact')
for t in (98.2, 108.5, 112.9, 114.5, 115.6, 116.6, 130.2, 143.7, 150.2): sfx(t, 'whoosh')
sfx(152.0, 'riser', 2.0)

# ============================== 3. NEGA HOZIR =============================
OV.append(Chapter(157.6, 253.6, '3', 'NEGA AYNAN HOZIR?'))
shot(154.0, 157.5, CARD(), 'flash', 'NEGA AYNAN HOZIR?')
shot(157.5, 167.8, MAP(cam=[(0, 68, 38.5, 16), (2.2, 69.6, 37.0, 11.5), (10.3, 69.6, 36.9, 10.5)],
                       hi=[('TJK', TJ, 0, 99)], borders=[('TJK-AFG', (255, 196, 0), 2.2, 2.4)],
                       rivers=[('Panj', 1.8), ('Amu Darya', 1.8)],
                       labels=[('AFGʻONISTON', 68.5, 35.4, .5, 32, (230, 230, 230)), ('PANJ', 71.3, 37.3, 4.2, 26, (120, 190, 255)), ('AMUDARYO', 67.3, 37.05, 4.2, 26, (120, 190, 255))],
                       country_labels=('TJK', 'AFG', 'UZB', 'KGZ')), 'whip', 'Chegara xaritasi')
shot(167.8, 172.6, EX(3, z0=1.0, z1=1.12), 'fade', 'Panj daryosi, chegara')
shot(172.6, 179.7, EX(4, z0=1.0, z1=1.12, fx=.45), 'fade', 'Panj boʻyidagi yoʻl')
shot(179.7, 191.2, MAP(cam=[(0, 69.6, 38.0, 8.5), (11.5, 69.4, 37.7, 6.5)], hi=[('TJK', TJ, 0, 99)],
                       admin_hi=[('Khatlon', (255, 170, 0), .6, 99)],
                       labels=[('XATLON VILOYATI', 69.2, 38.2, 1.2, 34, (255, 210, 120))],
                       cities=[('Dushanbe', 68.77, 38.56, .2, 'small')],
                       country_labels=('AFG', 'UZB')), 'whip', 'Xatlon viloyati')
shot(191.2, 197.2, G(3, z0=1.0, z1=1.1), 'fade', 'Kobul: Rossiya–Afgʻoniston muzokaralari')
shot(197.2, 204.9, G(0, z0=1.0, z1=1.1, fx=.4), 'fade', 'Overchuk Kobulda')
shot(204.9, 208.6, G(1, z0=1.0, z1=1.1), 'fade', 'Overchuk va Baradar')
shot(208.6, 217.4, (SplitSrc(ImgSrc(f'{A}/gov/kabul_2.jpg', 1.0, 1.08), VidSrc(f'{A}/commons/base_11.webm', 72.0),
                             'KOBUL BILAN MULOQOT', 'CHEGARA YONIDA BAZA'),
                    'FOTO: TASS / government.ru · VIDEO: mil.ru / Wikimedia Commons, CC BY 4.0'), 'whip', 'Ikki yoʻl: split-ekran')
shot(217.4, 221.8, KV('d25_putin', 2), 'fade', 'Arxiv: Putin Dushanbeda, 2025')
shot(221.8, 231.1, K('81313_08', z0=1.0, z1=1.05), 'fade', 'Savdo grafigi foni')
shot(231.1, 238.5, K('81313_07', z0=1.0, z1=1.1), 'fade', 'Migratsiya')
shot(238.5, 244.3, K('81313_14', z0=1.0, z1=1.1), 'fade', 'Dasturxon')
shot(244.3, 249.4, K('81313_19', z0=1.1, z1=1.0), 'fade', 'Qoʻl siqish')
shot(249.4, 253.9, K('81313_00', z0=1.0, z1=1.1, fx=.35), 'fade', 'Rahmon')
OV += [Kinetic(154.05, 157.5, ['NEGA AYNAN', 'HOZIR?'], size=150, dim=0, accent_word='HOZIR'),
       Counter(160.0, 167.6, 0, 1300, lambda v: f'{int(v):,}'.replace(',', ' ') + '+ KM', 'TOJIKISTON–AFGʻONISTON CHEGARASI',
               dur=1.8, pos=(W / 2, 200), size=120),
       FactBox(168.0, 179.5, 'D. PESKOV', ['Chegarada hodisalar boʻlib turadi, kontrabandachilar faol',
                                          'Shu bilan birga vaziyatda maʼlum barqarorlik va bashorat qilish imkoniyati saqlanmoqda'],
               pos='left', y=300, width=820),
       FactBox(181.6, 191.0, '2025-YIL NOYABR', ['Afgʻoniston hududidan uyushtirilgan hujum',
                                                'Xatlon viloyatida 3 nafar Xitoy fuqarosi halok boʻldi', 'Manba: Tojikiston TIV'],
               pos='right', y=520, width=760, accent=AMBER, size=36),
       LowerThird(192.9, 197.0, 'Rossiya Tolibon hukumatini rasman tan oldi', None, tag='2025-YIL IYUL'),
       LowerThird(197.5, 204.6, 'Aleksey Overchuk', 'Rossiya Bosh vaziri oʻrinbosari · Kobul, 13-noyabr', tag='KOBUL'),
       LocTag(217.5, 221.6, 'ARXIV · DUSHANBE, OKTABR 2025'),
       Bars(221.9, 231.0, 'ROSSIYA–TOJIKISTON SAVDOSI', [('2025-yil\n(yillik oʻsish)', 25, '+25%', .3),
                                                         ('2026-yil\n(9 oy)', 19, '≈+19%', 5.2)],
            'Manba: V. Putin, Dushanbe, 20-noyabr 2026 (kremlin.ru)'),
       FactBox(231.3, 238.3, 'MEHNAT MIGRATSIYASI', ['Rossiyada ishlayotgan yuz minglab markaziy osiyolik oilalarga bevosita taalluqli'],
               pos='left', y=300, width=800),
       LowerThird(238.8, 244.0, 'Kelishuvlar tafsiloti eʼlon qilinmadi', 'Tojikiston Prezidenti matbuot xizmati', tag='NOMAʼLUM'),
       LowerThird(244.6, 249.2, 'Rus tiliga eʼtibor uchun minnatdorlik', None, tag='PUTIN'),
       Quote(249.6, 253.8, 'Rossiya — strategik hamkor va ishonchli ittifoqchi.', 'Emomali Rahmon', 'Tojikiston Prezidenti',
             side='right', size=50)]
sfx(154.0, 'impact')
for t in (157.5, 168.0, 179.7, 181.6, 192.9, 197.5, 208.6, 217.4, 221.9, 231.3, 238.8, 249.6): sfx(t, 'whoosh')
sfx(160.0, 'ticks', 1.8); sfx(222.2, 'ticks', 1.0); sfx(227.0, 'ticks', 1.0)
sfx(251.9, 'riser', 2.0)

# ============================== 4. OʻZBEKISTON ============================
OV.append(Chapter(257.2, 290.9, '4', 'OʻZBEKISTON'))
shot(253.9, 257.0, CARD(), 'flash', 'Savol')
shot(257.0, 262.7, MAP(cam=[(0, 65.5, 39.5, 17), (5.7, 67.2, 37.6, 10)], hi=[('UZB', UZ, 0, 99)],
                       borders=[('UZB-AFG', (255, 196, 0), 1.6, 2.0)], rivers=[('Amu Darya', .8)],
                       cities=[('Termiz', 67.28, 37.22, 2.0, 'star')],
                       labels=[('AMUDARYO', 66.2, 37.75, 2.6, 26, (120, 190, 255)), ('AFGʻONISTON', 67.0, 36.3, .4, 30, (230, 230, 230))],
                       country_labels=('UZB', 'AFG', 'TJK', 'TKM')), 'whip', 'Oʻzbekiston–Afgʻoniston chegarasi')
shot(262.7, 267.5, EX(0, z0=1.0, z1=1.12), 'fade', 'Termiz–Hayraton “Doʻstlik” koʻprigi')
shot(267.5, 273.8, EX(6, z0=1.0, z1=1.12), 'fade', 'Toshkent')
shot(273.8, 280.0, EX(7, z0=1.0, z1=1.1), 'fade', 'Toshkent, tun')
shot(280.0, 291.2, CARD(), 'fade', 'Taqqoslash')
OV += [Kinetic(253.95, 257.0, ['BULARNING OʻZBEKISTONGA', 'QANDAY ALOQASI BOR?'], size=96, dim=0, accent_word='OʻZBEKISTONGA'),
       LowerThird(263.0, 267.3, 'Amudaryo ustidagi “Doʻstlik” koʻprigi', 'Termiz — Hayraton', tag='CHEGARA'),
       LowerThird(270.1, 273.6, 'Oʻzbekiston ODKBdagi aʼzoligini toʻxtatdi', None, tag='2012'),
       FactBox(274.0, 279.8, 'TASHQI SIYOSAT KONSEPSIYASI', ['Oʻzbekiston hududida xorijiy harbiy bazalar joylashtirilmaydi'],
               pos='left', y=330, width=820),
       Compare(280.2, 291.2, ('TOJIKISTON', ['Rossiya bilan harbiy ittifoq (ODKB)', 'Hududida 201-Rossiya bazasi'], TJ, 2.5),
               ('OʻZBEKISTON', ['Oʻz kuchiga tayanadi', 'Bloklardan tashqarida', 'Xorijiy bazalarsiz'], UZ, 6.7)),
       Kinetic(280.0, 291.2, ['BIR MINTAQA — IKKI YONDASHUV'], size=56, dim=0, y=110, bar=False, stagger=.05)]
sfx(253.9, 'impact')
for t in (257.0, 263.0, 270.1, 274.0, 280.0, 282.7, 286.9): sfx(t, 'whoosh')
sfx(289.2, 'riser', 2.0)

# ============================== 5. KEYIN NIMA =============================
OV.append(Chapter(292.8, 345.9, '5', 'KEYIN NIMA BOʻLADI?'))
shot(291.2, 292.6, CARD(), 'flash', 'Endi nima boʻladi?')
shot(292.6, 298.7, CW(25, 12.5), 'fade', 'Poligondagi tank')
shot(298.7, 302.0, K('81308_05', z0=1.0, z1=1.1), 'fade', 'Putin va Rahmon')
shot(302.0, 310.2, KV('csto70', 0), 'fade', 'ODKB, Putin nutqi')
shot(310.2, 313.4, CB(21, z0=1.0, z1=1.1), 'fade', 'Mashgʻulot')
shot(313.4, 319.5, K('81313_10', z0=1.0, z1=1.1), 'fade', 'Dushanbe')
shot(319.5, 325.6, K('81313_15', z0=1.12, z1=1.0), 'fade', 'Saroy zali')
shot(325.6, 333.8, MAP(cam=[(0, 91.5, 32, 66), (8.2, 91.5, 32.5, 61)], phi0=32,
                       arcs=[((114.12, 22.55), (68.77, 38.56), .6, 5.0, (255, 255, 255))],
                       cities=[('Shenzhen', 114.12, 22.55, .3, 'star'), ('Dushanbe', 68.77, 38.56, 5.2, 'star')],
                       country_labels=('TJK', 'CHN', 'KAZ', 'IND', 'MNG', 'AFG', 'PAK'), hi=[('TJK', TJ, 4.8, 99)]),
     'whip', 'Parvoz: Shenzhen → Dushanbe')
shot(333.8, 341.1, K('81303_24', z0=1.0, z1=1.1), 'fade', 'Uch rahbar')
shot(341.1, 346.1, K('81303_03', z0=1.0, z1=1.08), 'fade', 'Shenzhen sammiti banneri')
OV += [Kinetic(291.25, 292.6, ['ENDI NIMA BOʻLADI?'], size=120, dim=0),
       LocTag(292.8, 302.0, '1 · BAZA QOLADI'),
       Counter(293.0, 298.5, 0, 16, lambda v: f'{int(round(v))} YIL', '2042-YILGACHA', dur=1.6, pos=(W / 2, 470), dim=.35),
       LocTag(302.2, 313.2, '2 · 2027 — ODKB RAISLIGI'),
       LowerThird(302.6, 310.0, 'Tojikiston ODKBga raislik qiladi', 'Ustuvor yoʻnalish: Afgʻon chegarasi xavfsizligi', tag='2027'),
       LocTag(313.6, 325.4, '3 · MIGRATSIYA'),
       FactBox(314.0, 325.3, 'HOZIRCHA NOMAʼLUM', ['Migratsiya boʻyicha qanday qarorlar qabul qilingani eʼlon qilinmagan',
                                                  'Yangi kelishuvlar Rossiyadagi minglab mehnat muhojirlariga taʼsir qilishi mumkin'],
               pos='right', y=300, width=800),
       LocTag(325.8, 333.6, 'SHENZHEN → DUSHANBE'),
       FactBox(335.7, 340.9, 'TALQIN', ['Moskva Markaziy Osiyo xavfsizligini oʻz taʼsir doirasida saqlab qolmoqchi ekanini koʻrsatmoqda'],
               pos='left', y=300, width=820, accent=AMBER),
       LowerThird(341.3, 345.9, 'Bu — talqin, tashrifning rasmiy maqsadi emas', None, tag='MUHIM')]
sfx(291.2, 'impact'); sfx(293.0, 'ticks', 1.6)
for t in (302.6, 314.0, 325.6, 335.7, 341.3): sfx(t, 'whoosh')
sfx(344.1, 'riser', 2.0)

# ============================== XULOSA ====================================
OV.append(Chapter(346.4, 364.9, '6', 'XULOSA'))
shot(346.1, 350.0, K('81303_26', z0=1.0, z1=1.1), 'flash', 'Shenzhen stoli')
shot(350.0, 355.1, CW(10, 31.0), 'fade', 'Baza mashgʻuloti')
shot(355.1, 359.8, K('81313_13', z0=1.0, z1=1.1), 'fade', 'Putin va Rahmon sayrda')
shot(359.8, 365.2, EX(8, z0=1.0, z1=1.12), 'fade', 'Toshkent panoramasi')
shot(365.2, TOTAL, CARD(), 'fade', 'Savol va yakun')
OV += [Kinetic(346.15, 348.0, ['XULOSA'], size=130, dim=.45),
       Kinetic(365.3, 381.4, ['MARKAZIY OSIYO XAVFSIZLIGINI', 'KIM TAʼMINLASHI KERAK?'], size=84, dim=0, y=330,
               sub='Mintaqa davlatlarining oʻzimi yoki tashqi kuchlarning harbiy bazalarimi?'),
       EndCard(371.6, 381.4, [('Fikringizni izohlarda yozing', font('Bold', 46), WHITE)], y=700),
       EndCard(375.3, 381.4, [('Manbalar: kremlin.ru · government.ru · Rossiya Mudofaa vazirligi (mil.ru) / Wikimedia Commons · Natural Earth',
                               font('Medium', 24), GREY)], y=960)]
sfx(346.1, 'impact'); sfx(365.2, 'whoosh')

# ---- credits (on top) + vignette below overlays
for sh in SHOTS:
    if sh['credit']:
        OV.append(Credit(sh['s'] + .1, sh['e'] - .05, sh['credit']))
OV.insert(0, Vignette(0, TOTAL + 1))

# sanity: contiguous
for a, b in zip(SHOTS, SHOTS[1:]):
    assert abs(a['e'] - b['s']) < 1e-6, (a['s'], a['e'], b['s'])
assert SHOTS[0]['s'] == 0 and abs(SHOTS[-1]['e'] - TOTAL) < 1e-6


def timeline():
    return Timeline_(SHOTS, OV, TOTAL)
