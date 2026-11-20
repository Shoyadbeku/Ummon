"""Storyboard -> shots. Times are seconds on the voice-over timeline."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import *
from overlays import *
from engine import VideoShot, PhotoShot, GraphicShot
from maps import MapScene, map_shot_fn, CITY
import scenes

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
A = lambda k: next(os.path.join(ROOT, "assets", f) for f in os.listdir(os.path.join(ROOT, "assets")) if f.split(".")[0] == k and not f.endswith((".part", ".tmp")))
def have(k):
    try: A(k); return True
    except StopIteration: return False

DOD = "VIDEO: U.S. Department of War / DVIDS · Public domain"
CR = {
    "v_strikes1": "ARXIV · " + DOD, "v_tlam1": "ARXIV · " + DOD, "v_tlam2": "ARXIV · " + DOD, "v_kc135": "ARXIV · " + DOD,
    "v_b1": "ARXIV · " + DOD, "v_kharg": "ARXIV · " + DOD, "v_irgc_strike": "ARXIV · " + DOD, "v_lincoln_night": "ARXIV · " + DOD,
    "v_lincoln4k": "ARXIV · " + DOD, "v_bainbridge": "ARXIV · " + DOD, "v_ford": "ARXIV · " + DOD, "v_blockade": "ARXIV · " + DOD, "v_launch": "ARXIV · VIDEO: U.S. Central Command · Public domain",
    "v_trump_major": "ARXIV · VIDEO: The White House · Public domain", "v_trump_hegseth": "ARXIV · VIDEO: U.S. Department of War · Public domain",
    "v_iran_missile": "ARXIV · VIDEO: Mehr News Agency · CC BY 4.0", "v_brief": "ARXIV · " + DOD,
    "p_birol": "FOTO: IAEA Imagebank / Wikimedia Commons · CC BY 2.0",
    "p_ravid": "FOTO: Xuthoria / Wikimedia Commons · CC BY-SA 4.0",
    "p_trump_mal": "ARXIV · FOTO: The White House · Public domain",
    "p_trump_netanyahu2": "ARXIV · FOTO: The White House (28.07.2026) · Public domain",
    "p_baghaei2": "ARXIV · FOTO: Foad Ashtari / Mehr News Agency · CC BY 4.0",
    "p_islamabad1": "ARXIV · FOTO: Hamed Malekpour / Mehr News Agency · CC BY 4.0 · Islomobod muzokaralari",
    "p_capitol": "FOTO: Noclip / Wikimedia Commons · Public domain",
    "p_senate": "ARXIV · FOTO: U.S. Senate Photo Studio · Public domain",
    "p_whitehouse": "FOTO: Nishkid64 / Wikimedia Commons · Public domain",
    "p_briefing2": "ARXIV · FOTO: CPO James Mullen / U.S. DoW · Public domain · Pentagon brifing zali",
    "p_pif58": "ARXIV FOTO · PIF minorasi, Riyod · Kolaiel / Wikimedia Commons · CC0",
    "p_pif46": "ARXIV FOTO · PIF minorasi, Riyod · Kolaiel / Wikimedia Commons · CC0",
    "p_kafd10": "ARXIV FOTO · KAFD, Riyod · Kolaiel / Wikimedia Commons · CC0",
    "p_kafd13": "ARXIV FOTO · KAFD, Riyod · Kolaiel / Wikimedia Commons · CC0",
    "p_kafd12": "ARXIV FOTO · KAFD, Riyod · Kolaiel / Wikimedia Commons · CC0",
    "p_kafd18": "ARXIV FOTO · KAFD, Riyod · Kolaiel / Wikimedia Commons · CC0",
    "p_houthi2": "ARXIV · FOTO: Henry Ridgwell / VOA · Public domain",
    "p_hodeidah": "ARXIV · FOTO: Hudayda · MAHMOUD / Panoramio · CC BY 3.0",
    "p_hormuz_mines": "ARXIV · FOTO: NAVCENT Public Affairs · Public domain",
    "p_tehran4": "ARXIV · FOTO: Avash News Agency · CC BY 4.0",
    "p_tehran1": "ARXIV · FOTO: Avash News Agency · CC BY 4.0",
    "p_fuel_eugene": "FOTO: Rick Obst / Wikimedia Commons · CC BY 4.0",
    "p_fuel_th": "FOTO: Chainwit. / Wikimedia Commons · CC BY 4.0",
    "p_fuel_chula": "FOTO: Bnuuy / Wikimedia Commons · CC0",
    "p_tas_airport": "FOTO: Toshkent · Umad / Wikimedia Commons · CC BY 4.0",
    "p_uzair": "FOTO: SmallSonMarex / Wikimedia Commons · CC0",
    "p_grounded": "ARXIV · FOTO: VEO15 / Wikimedia Commons · CC BY 4.0",
    "p_umrah": "ARXIV · FOTO: Mehdi Almasi / Mehr News Agency · CC BY 4.0",
}
MAPCR = "XARITA: Natural Earth ma’lumotlari asosida · Public domain"
GFX = "GRAFIKA: tahririyat"


def build(ctx):
    s = ctx.s
    shots = []
    def V(a, b, key, src_in=0, cr=True, ov=(), **kw):
        o = list(ov)
        if cr and key in CR: o.append(credit(ctx, CR[key], 0.2, b - a - 0.1))
        shots.append(VideoShot(a, b, A(key), src_in, overlays=o, label=key, **kw))
    def P(a, b, key, ka=(0.5, 0.5, 1.0), kb=(0.5, 0.5, 1.12), ov=(), cr=True, **kw):
        o = list(ov)
        if cr and key in CR: o.append(credit(ctx, CR[key], 0.2, b - a - 0.1))
        shots.append(PhotoShot(a, b, A(key), ka, kb, overlays=o, label=key, **kw))
    def G(a, b, fn, ov=(), cr=GFX, **kw):
        o = list(ov)
        if cr: o.append(credit(ctx, cr, 0.3, b - a - 0.1))
        shots.append(GraphicShot(a, b, fn, overlays=o, label="gfx", **kw))
    def M(a, b, scene, ov=(), **kw):
        G(a, b, map_shot_fn(scene), ov, cr=MAPCR, **kw)

    # ---------------- HOOK ----------------
    V(0.00, 2.30, "v_strikes1", 1.0, ov=[kinetic(ctx, ["9 OY"], 0.1, 2.3, size=420, sub="DAVOM ETAYOTGAN URUSH", sub_size=90)])
    V(2.30, 5.38, "v_tlam1", 0.9, trans="flash", tdur=0.2,
      ov=[kinetic(ctx, ["$48 MLRD+"], 0.15, 3.1, size=360, sub="XARAJAT · PENTAGON MA’LUMOTI", sub_size=80)])
    P(5.38, 12.85, "p_birol", (0.48, 0.42, 1.05), (0.42, 0.36, 1.28), trans="dissolve", tdur=0.3,
      ov=[lower_third(ctx, "Fatih Birol", "Xalqaro energetika agentligi (IEA) rahbari", 0.3, 2.6),
          quote_card(ctx, "Energetika xavfsizligi tarixidagi eng katta tahdid", "Fatih Birol, IEA", 2.6, 7.45,
                     x=s(1550), y=s(1050), maxw=1900, size=104)])
    V(12.85, 16.55, "v_kc135", 15.5, trans="dissolve", tdur=0.4)
    V(16.55, 19.30, "v_b1", 33.6, trans="flash", tdur=0.2,
      ov=[kinetic(ctx, ["YANGI ZARBALAR", "BO‘LADIMI?"], 0.15, 2.75, size=250, accent=1)])
    G(19.30, 23.70, scenes.title_card("ERON URUSHI: 9-OY", "Yangi zarbalar arafasidami? · Tahliliy reportaj", "20-NOYABR, 2026"),
      trans="flash", tdur=0.25, cr=None)

    # ---------------- BACKGROUND ----------------
    first = "v_launch" if have("v_launch") else "v_tlam2"
    V(23.70, 26.90, first, 0.5 if first == "v_tlam2" else 9.6, trans="dissolve", tdur=0.3,
      ov=[kinetic(ctx, ["28-FEVRAL, 2026"], 0.2, 6.3, x=s(190), y=s(1330), size=130, align="left",
                  sub="AQSh va Isroil Eronga qarshi keng ko‘lamli operatsiya boshladi", sub_size=66, anim="slide")])
    V(26.90, 30.00, "v_kharg", 15.0)
    P(30.00, 33.90, "p_islamabad1", (0.5, 0.5, 1.02), (0.55, 0.45, 1.18), trans="dissolve", tdur=0.3,
      ov=[kinetic(ctx, ["SULH VA MUZOKARALAR"], 0.3, 3.8, x=s(190), y=s(1450), size=110, align="left", anim="slide")])
    G(33.90, 38.15, scenes.timeline_scene([("28-FEV", "AQSh–Isroil operatsiyasi boshlandi", 0.4),
                                           ("APREL", "Vaqtinchalik sulh, Islomobod muzokaralari", 1.1),
                                           ("NOYABR", "Barqaror kelishuv hali yo‘q", 1.9)]), trans="dissolve", tdur=0.3)
    P(38.15, 39.55, "p_tehran4", (0.5, 0.5, 1.05), (0.5, 0.5, 1.15), trans="flash", tdur=0.15)
    V(39.55, 40.90, "v_irgc_strike", 44.0)
    V(40.90, 44.00, "v_lincoln_night", 13.3,
      ov=[kinetic(ctx, ["SO‘NGGI IKKI KUN"], 0.2, 3.0, size=200, sub="Vaziyat yana keskinlashdi", sub_size=80)])

    # ---------------- 1. WASHINGTON ----------------
    V(44.00, 49.60, "v_trump_major", 60.0, zoom=1.9, focus=(0.5, 0.12), trans="flash", tdur=0.2,
      ov=[section_bumper(ctx, "1", "VASHINGTON", 0.15, 2.5),
          lower_third(ctx, "Donald Tramp", "AQSh prezidenti", 3.0, 5.5, tag="19-NOYABR")])
    P(49.60, 53.00, "p_ravid", (0.35, 0.45, 1.1), (0.38, 0.42, 1.3), trans="dissolve", tdur=0.25,
      ov=[lower_third(ctx, "Barak Ravid", "Jurnalist, Axios", 0.3, 3.3)])
    V(53.00, 59.10, "v_trump_major", 200.0, zoom=1.55, focus=(0.5, 0.08), trans="dissolve", tdur=0.25,
      ov=[quote_card(ctx, "Eron bo‘yicha qaror qabul qilishga shoshilmayapman. Yangi yil boshlangandan keyin nima bo‘lishini ko‘ramiz",
                     "Donald Tramp, 19-noyabr (Axios intervyusi)", 0.15, 6.0, y=s(1080), maxw=2700, size=86)])
    P(59.10, 62.55, "p_trump_mal", (0.5, 0.45, 1.05), (0.47, 0.4, 1.25), trans="dissolve", tdur=0.3)
    V(62.55, 69.85, "v_lincoln4k", 20.0, dark=0.12,
      ov=[headline_card(ctx, "Bloomberg", "AQShning Eronga yangi zarbalarga tayyorgarlik ehtimoli oshmoqda", 0.3, 7.3, s(240), s(380), w=2700),
          headline_card(ctx, "The New York Times", "Isroil Eronga qarshi yangi harbiy kampaniya rejasini ishlab chiqmoqda", 1.6, 7.3, s(900), s(1060), w=2700),
          kinetic(ctx, ["mazmunan keltirildi"], 2.0, 7.3, x=s(2900), y=s(1830), size=44, kind="semi", shadow=False, anim="fade")])
    P(69.85, 78.50, "p_trump_netanyahu2", (0.36, 0.42, 1.15), (0.32, 0.38, 1.45), trans="dissolve", tdur=0.3,
      ov=[lower_third(ctx, "Binyamin Netanyaxu", "Isroil bosh vaziri", 0.4, 4.0),
          kinetic(ctx, ["4–7 KUN"], 4.3, 8.65, x=s(2350), y=s(520), size=300, accent=0, sub="Yangi kampaniya rejasi (NYT)", sub_size=70)])
    V(78.50, 82.00, "v_trump_hegseth", 0.4, trans="dissolve", tdur=0.25,
      ov=[lower_third(ctx, "Donald Tramp", "Fox News telekanaliga intervyu", 0.3, 3.4, tag="18-NOYABR")])
    V(82.00, 87.40, "v_trump_major", 320.0, zoom=1.9, focus=(0.5, 0.12),
      ov=[kinetic(ctx, ["KIMYOVIY YOKI", "BIOLOGIK QUROL?"], 0.2, 5.3, x=s(2050), y=s(700), size=170, align="left", sub="Tramp iddaosi", sub_size=70, anim="slide")])
    P(87.40, 95.30, "p_baghaei2", (0.5, 0.5, 1.0), (0.52, 0.45, 1.1), trans="dissolve", tdur=0.3,
      ov=[kinetic(ctx, ["TEHRON RAD ETDI"], 0.1, 2.5, x=s(190), y=s(1400), size=150, align="left", anim="slide"),
          lower_third(ctx, "Ismoil Baqoiy", "Eron Tashqi ishlar vazirligi vakili", 2.7, 7.8),
          quote_card(ctx, "Xuddi o‘sha yolg‘on ssenariy", "Ismoil Baqoiy", 4.6, 7.85, x=s(2050), y=s(300), maxw=1500, size=96)])

    # ---------------- 2. CONGRESS ----------------
    P(95.30, 98.80, "p_capitol", (0.5, 0.55, 1.0), (0.5, 0.5, 1.14), trans="flash", tdur=0.2,
      ov=[section_bumper(ctx, "2", "KONGRESS", 0.15, 3.3)])
    P(98.80, 106.20, "p_senate", (0.5, 0.55, 1.05), (0.5, 0.5, 1.35), trans="dissolve", tdur=0.3,
      ov=[kinetic(ctx, ["19-NOYABR · AQSh SENATI"], 0.3, 7.3, x=s(190), y=s(1300), size=120, align="left",
                  sub="Urushni davom ettirish uchun Kongress ruxsatini talab qiluvchi rezolyutsiya", sub_size=62, anim="slide")])
    G(106.20, 111.90, scenes.vote_scene(51, 48), trans="push", tdur=0.35,
      ov=[stamp(ctx, "RAD ETILDI", 4.1, 5.7, size=200, x=s(2050), y=s(1380))])
    P(111.90, 119.90, "p_whitehouse", (0.5, 0.5, 1.05), (0.5, 0.45, 1.3), trans="dissolve", tdur=0.3,
      ov=[kinetic(ctx, ["ORALIQ SAYLOVLARDAN KEYINGI", "BIRINCHI OVOZ BERISH"], 0.2, 4.2, size=130),
          kinetic(ctx, ["OQ UYNING QO‘LI", "HOZIRCHA BO‘SH"], 4.5, 7.95, size=170, accent=1)])

    # ---------------- 3. COST ----------------
    P(119.90, 126.80, "p_briefing2", (0.78, 0.4, 1.35), (0.82, 0.36, 1.6), trans="flash", tdur=0.2,
      ov=[section_bumper(ctx, "3", "URUSH NARXI", 0.15, 2.6),
          kinetic(ctx, ["PENTAGON RASMIYSI ARTUR MILLER"], 2.8, 6.8, x=s(190), y=s(1400), size=100, align="left",
                  sub="Senatdagi tinglovda raqamni e’lon qildi", sub_size=66, anim="slide")])
    G(126.80, 133.40, scenes.counter_scene(), trans="dissolve", tdur=0.3)
    V(133.40, 139.15, "v_bainbridge", 3.6, dark=0.05,
      ov=info_box(ctx, "Hisobga kirgan", ["O‘q-dorilar", "Texnikani almashtirish", "Operatsion xarajatlar"], 0.1, 5.7, s(2150), s(500), w=1450, stagger=0.7))
    miss = "v_iran_missile" if have("v_iran_missile") else "v_ford"
    V(139.15, 144.00, miss, 20.0 if miss == "v_iran_missile" else 7.0,
      fit="window" if miss == "v_iran_missile" else "cover",
      ov=info_box(ctx, "Hisobga kirmagan", ["Harbiy bazalarga yetkazilgan zarar", "Iqtisodiy yo‘qotishlar"], 0.1, 4.8, s(2150), s(560), w=1450, stagger=0.8))

    # ---------------- 4. GULF ----------------
    sc = MapScene([(0, 50, 28, 62), (3.5, 50, 26, 50), (6.0, 47.5, 22, 34), (9.7, 47.0, 21.5, 30)],
                  highlights={"IRN": ((130, 28, 34), 4.0), "YEM": ((150, 105, 30), 4.0), "SAU": ((52, 72, 104), 4.0)},
                  labels=[("ERON", 54, 32.5, 4.3, 80), ("YAMAN (HUSIYLAR)", 48.8, 15.0, 4.6, 64), ("SAUDIYA ARABISTONI", 43.5, 21.0, 4.8, 60),
                          ("Riyod", *CITY["Riyadh"], 9.0, 60, "city"), ("San’o", *CITY["Sanaa"], 6.5, 52, "city")],
                  pins=[(*CITY["Riyadh"], 9.0, RED)],
                  arcs=[(*CITY["Sanaa"], *CITY["Riyadh"], 7.5, 9.3, (255, 90, 60), 0.28)])
    M(144.00, 153.70, sc, trans="flash", tdur=0.2, ov=[section_bumper(ctx, "4", "FORS KO‘RFAZI", 0.15, 3.6)])
    P(153.70, 158.10, "p_pif58", (0.5, 0.65, 1.05), (0.5, 0.35, 1.2), trans="dissolve", tdur=0.3,
      ov=[kinetic(ctx, ["SUVEREN BOYLIK FONDI", "SHTAB-KVARTIRASI"], 0.3, 4.3, x=s(190), y=s(1250), size=120, align="left", anim="slide")])
    P(158.10, 160.80, "p_pif46", (0.5, 0.5, 1.05), (0.5, 0.42, 1.18))
    P(160.80, 165.90, "p_kafd10", (0.5, 0.45, 1.05), (0.45, 0.4, 1.22), trans="dissolve", tdur=0.3,
      ov=info_box(ctx, "Saudiya fuqaro muhofazasi", ["Binaga zarar yetgan", "Jabrlanganlar yo‘q"], 0.2, 5.0, s(2100), s(520), w=1500, stagger=0.9))
    P(165.90, 170.20, "p_kafd13", (0.5, 0.5, 1.1), (0.5, 0.5, 1.3),
      ov=[kinetic(ctx, ["2 HAFTADA 2-ZARBA"], 0.2, 4.2, size=220, accent=0, sub="Riyoddagi moliyaviy tumanga", sub_size=80)])
    P(170.20, 173.80, "p_houthi2", (0.5, 0.5, 1.05), (0.5, 0.5, 1.2), trans="flash", tdur=0.2,
      ov=[kinetic(ctx, ["20-NOYABR · HUSIYLAR BAYONOTI"], 0.2, 3.5, x=s(190), y=s(1400), size=110, align="left", anim="slide")])
    P(173.80, 180.70, "p_kafd12", (0.5, 0.5, 1.05), (0.55, 0.45, 1.25),
      ov=info_box(ctx, "Husiylar bayonoti", ["Odamlarni Qirol Abdulla moliyaviy tumanidan (KAFD) uzoqroq turishga chaqirdi",
                                             "KAFDni «harbiy nishon» deb e’lon qildi"], 0.2, 6.8, s(1900), s(480), w=1750, stagger=1.6))
    sc2 = MapScene([(0, 46, 23.5, 32), (5.8, 45, 23.5, 30)], highlights={"SAU": ((60, 70, 96), 0), "YEM": ((150, 105, 30), 0), "IRN": ((130, 28, 34), 0)},
                   zones=[("SAU", 0.6, RED)],
                   labels=[("XAVFLI HAVO HUDUDI", 44.5, 23.0, 1.2, 80), ("YAMAN", 47, 15.6, 0.2, 60), ("ERON", 54, 31.5, 0.2, 70)],
                   pins=[(*CITY["Riyadh"], 0.3, RED)])
    M(180.70, 186.50, sc2, trans="dissolve", tdur=0.3,
      ov=[kinetic(ctx, ["AVIAKOMPANIYALARGA OGOHLANTIRISH"], 0.3, 5.7, y=s(1700), size=110)])
    P(186.50, 191.80, "p_hodeidah", (0.5, 0.5, 1.05), (0.5, 0.5, 1.2), trans="dissolve", tdur=0.3,
      ov=info_box(ctx, "Saudiya boshchiligidagi koalitsiya", ["Hudayda shahri aholisini evakuatsiya qilishga chaqirdi"], 0.2, 5.2, s(1900), s(560), w=1750))
    sc3 = MapScene([(0, 52, 25, 22), (2.4, 56.4, 26.4, 9)],
                   highlights={"IRN": ((130, 28, 34), 0), "ARE": ((60, 75, 100), 0), "OMN": ((60, 75, 100), 0)},
                   labels=[("ERON", 56.8, 28.2, 0.2, 80), ("HORMUZ BO‘G‘OZI", 56.5, 26.45, 1.0, 54, "city"), ("BAA", 54.8, 24.0, 0.8, 60), ("OMAN", 57.2, 23.4, 0.8, 60)],
                   pins=[(*CITY["Hormuz"], 1.0, GOLD)])
    M(191.80, 194.30, sc3, trans="dissolve", tdur=0.3)
    V(194.30, 199.75, "v_blockade", 10.5,
      ov=[kinetic(ctx, ["IRGC DA’VOSI"], 0.3, 5.4, x=s(190), y=s(1250), size=160, align="left",
                  sub="Yana 2 ta neft tankeri minaga urilib yonib ketgan", sub_size=72, anim="slide")])
    P(199.75, 203.20, "p_hormuz_mines", (0.5, 0.5, 1.05), (0.5, 0.5, 1.2),
      ov=[stamp(ctx, "TASDIQLANMAGAN", 0.15, 3.45, size=180)])
    V(203.20, 208.90, "v_blockade", 0.5, dark=0.1,
      ov=[headline_card(ctx, "CBS News", "Bunday da’volar deyarli har kuni aytiladi, lekin kamdan kam tasdiqlanadi", 0.2, 5.6, s(500), s(700), w=2800)])
    P(208.90, 217.70, "p_tehran4", (0.45, 0.5, 1.05), (0.5, 0.5, 1.3), darken=0.25, trans="dissolve", tdur=0.3,
      ov=[quote_card(ctx, "Agar ular infratuzilmaga zarba bersa, biz ham albatta ularning infratuzilmasiga zarba beramiz",
                     "Eron qo‘mondoni", 0.4, 8.7, maxw=2600, size=100)])

    # ---------------- WHY IT MATTERS ----------------
    G(217.70, 221.00, scenes.question_scene(["BULARNING", "BIZGA QANDAY ALOQASI BOR?"]), trans="flash", tdur=0.2, cr=None)
    P(221.00, 222.90, "p_fuel_eugene", (0.5, 0.5, 1.0), (0.5, 0.5, 1.12),
      ov=[kinetic(ctx, ["1. NEFT NARXI"], 0.1, 1.9, size=220, accent=0)])
    G(222.90, 233.45, scenes.brent_scene(72.0, 92.5), trans="dissolve", tdur=0.3)
    P(233.45, 236.10, "p_fuel_th", (0.5, 0.5, 1.05), (0.5, 0.45, 1.2), trans="dissolve", tdur=0.25,
      ov=[kinetic(ctx, ["YOQILG‘I"], 0.2, 2.6, x=s(190), y=s(1450), size=150, align="left", anim="slide")])
    P(236.10, 238.90, "p_fuel_chula", (0.5, 0.4, 1.05), (0.5, 0.45, 1.2),
      ov=[kinetic(ctx, ["YUK TASHISH · OZIQ-OVQAT"], 0.2, 2.75, x=s(190), y=s(1450), size=130, align="left", anim="slide")])
    P(238.90, 241.30, "p_tas_airport", (0.5, 0.5, 1.05), (0.5, 0.5, 1.18),
      ov=[kinetic(ctx, ["O‘ZBEKISTON HAM", "CHETDA QOLMAYDI"], 0.2, 2.4, size=170, accent=0)])
    P(241.30, 243.70, "p_uzair", (0.5, 0.5, 1.0), (0.55, 0.5, 1.15), trans="flash", tdur=0.2,
      ov=[kinetic(ctx, ["2. TRANSPORT VA SAFARLAR"], 0.1, 2.4, size=180, accent=0)])
    sc4 = MapScene([(0, 58, 33, 46), (8.4, 56, 32, 42)],
                   highlights={"UZB": ((30, 140, 160), 0.2), "SAU": ((60, 70, 96), 0.2), "ARE": ((60, 70, 96), 0.2), "QAT": ((60, 70, 96), 0.2)},
                   labels=[("O‘ZBEKISTON", 64.5, 41.8, 0.3, 64), ("Toshkent", *CITY["Tashkent"], 0.5, 54, "city"),
                           ("Dubay", *CITY["Dubai"], 2.0, 50, "city"), ("Jidda", *CITY["Jeddah"], 2.6, 50, "city"), ("Doha", *CITY["Doha"], 3.2, 50, "city")],
                   pins=[(*CITY["Tashkent"], 0.4, TEAL)],
                   arcs=[(*CITY["Tashkent"], *CITY["Dubai"], 0.8, 2.2, (90, 210, 230), 0.15),
                         (*CITY["Tashkent"], *CITY["Jeddah"], 1.4, 3.0, (90, 210, 230), 0.18),
                         (*CITY["Tashkent"], *CITY["Doha"], 2.0, 3.4, (90, 210, 230), 0.15)])
    M(243.70, 252.10, sc4, trans="dissolve", tdur=0.3,
      ov=info_box(ctx, "Fors ko‘rfazi — bu", ["Ish", "Savdo", "Tranzit parvozlar", "Umra ziyoratlari"], 3.6, 8.4, s(2500), s(500), w=1100, stagger=0.55))
    P(252.10, 258.00, "p_grounded", (0.5, 0.5, 1.05), (0.45, 0.5, 1.25), trans="dissolve", tdur=0.3,
      ov=[kinetic(ctx, ["AVIAKOMPANIYALAR QARORIGA", "TA’SIR QILISHI MUMKIN"], 0.3, 5.8, size=130)])
    P(258.00, 266.10, "p_umrah", (0.5, 0.45, 1.05), (0.5, 0.4, 1.3), trans="dissolve", tdur=0.3,
      ov=info_box(ctx, "Hozircha", ["Parvozlar bekor qilingani haqida rasmiy xabar yo‘q", "Ziyorat va safarga otlanganlar vaziyatni kuzatib borsin"],
                  0.2, 8.0, s(1900), s(480), w=1750, stagger=2.8))
    sc5 = MapScene([(0, 60, 33, 40), (14.5, 59, 33, 34)],
                   highlights={"IRN": ((130, 28, 34), 2.0), "UZB": ((30, 140, 160), 0.5), "TKM": ((60, 75, 100), 2.0)},
                   labels=[("O‘ZBEKISTON", 64.5, 41.8, 0.6, 64), ("TURKMANISTON", 59.5, 39.3, 2.2, 52), ("ERON", 54.5, 32.5, 2.4, 80),
                           ("Bandar-Abbos", *CITY["Bandar Abbas"], 7.5, 50, "city"), ("Chobahor", *CITY["Chabahar"], 8.5, 50, "city"),
                           ("JANUBIY DENGIZ YO‘LLARI", 61.5, 22.8, 9.5, 58)],
                   pins=[(*CITY["Tashkent"], 0.6, TEAL)],
                   routes=[([CITY["Tashkent"], CITY["Samarkand"], CITY["Ashgabat"], CITY["Mashhad"], CITY["Bandar Abbas"]], 3.2, 7.5, GOLD, False),
                           ([CITY["Mashhad"], CITY["Chabahar"]], 6.2, 8.5, GOLD, False)])
    M(266.10, 280.60, sc5, trans="flash", tdur=0.2,
      ov=[kinetic(ctx, ["3. MINTAQAVIY XAVFSIZLIK"], 0.1, 2.6, y=s(200), size=150, accent=0),
          kinetic(ctx, ["SAVDO YO‘LLARI VA INVESTITSIYA MUHITI"], 8.0, 14.5, y=s(260), size=96, sub="Urush cho‘zilgani sari noaniqlik ortadi", sub_size=62)])

    # ---------------- SCENARIOS ----------------
    V(280.60, 284.00, "v_irgc_strike", 0.5, trans="flash", tdur=0.2,
      ov=[kinetic(ctx, ["BUNDAN KEYIN", "NIMA BO‘LADI?"], 0.15, 3.4, size=240, accent=1)])
    def scen(ctx, t, dur, st, f1=scenes.scenarios_scene(focus=1, t_second=99), f2=scenes.scenarios_scene(focus=2, t_second=7.5),
             f3=scenes.scenarios_scene(focus=None, t_second=7.5)):
        if t < 7.5: return f1(ctx, t, dur, st)
        return f2(ctx, t, dur, st) if t < 13.6 else f3(ctx, t, dur, st)
    G(284.00, 297.80, scen, trans="dissolve", tdur=0.3)
    V(297.80, 302.30, "v_ford", 19.5, dark=0.08,
      ov=[kinetic(ctx, ["QAYSI BIRI?"], 0.2, 4.4, size=260, sub="Hozir hech kim aniq ayta olmaydi", sub_size=80)])
    P(302.30, 307.50, "p_kafd18", (0.4, 0.5, 1.1), (0.35, 0.45, 1.3), trans="dissolve", tdur=0.3,
      ov=info_box(ctx, "Saudiya Arabistoni", ["Husiylarga qarshi barcha zarur choralarni ko‘rish huquqini saqlab qoladi"], 0.2, 5.1, s(1900), s(560), w=1750))
    P(307.50, 311.30, "p_tehran1", (0.5, 0.5, 1.05), (0.5, 0.5, 1.2),
      ov=info_box(ctx, "Eron", ["Infratuzilmaga zarba berilsa — javob qaytaradi"], 0.2, 3.7, s(1900), s(560), w=1750))
    sc6 = MapScene([(0, 51, 26, 30), (5.3, 51, 26, 26)],
                   highlights={k: ((110, 40, 46), 0.3) for k in ["IRN", "SAU", "ARE", "QAT", "KWT", "BHR", "OMN", "IRQ"]},
                   ripples=[(*CITY["Riyadh"], 0.0, 5.0, RED, 5), (*CITY["Bandar Abbas"], 0.4, 5.0, RED, 5),
                            (*CITY["Doha"], 0.8, 5.0, RED, 4), (*CITY["Dubai"], 1.1, 5.0, RED, 4), (*CITY["Kharg"], 1.4, 5.0, RED, 4)],
                   labels=[("BUTUN KO‘RFAZGA YOYILISH XAVFI", 51.5, 20.5, 1.2, 80)])
    M(311.30, 316.60, sc6, trans="dissolve", tdur=0.3)

    # ---------------- CONCLUSION ----------------
    V(316.60, 323.30, "v_trump_major", 420.0, zoom=1.7, focus=(0.5, 0.1), dark=0.15, trans="flash", tdur=0.2,
      ov=[kinetic(ctx, ["«SHOSHILMAYAPMAN»"], 1.2, 6.6, x=s(190), y=s(500), size=150, align="left", anim="slide"),
          kinetic(ctx, ["ZARBA EHTIMOLI", "ORTMOQDA"], 3.5, 6.6, x=s(2200), y=s(1250), size=150, align="left", accent=1, anim="slide")])
    V(323.30, 325.20, "v_b1", 37.0, ov=[kinetic(ctx, ["9-OY"], 0.1, 1.9, size=400)])
    V(325.20, 328.70, "v_strikes1", 22.5, ov=[kinetic(ctx, ["FRONT CHIZIG‘I"], 0.2, 3.4, x=s(190), y=s(1450), size=140, align="left", anim="slide")])
    P(328.70, 330.60, "p_fuel_th", (0.3, 0.5, 1.2), (0.35, 0.5, 1.35),
      ov=[kinetic(ctx, ["YOQILG‘I NAVBATI"], 0.1, 1.9, x=s(190), y=s(1450), size=140, align="left", anim="slide")])
    P(330.60, 333.60, "p_grounded", (0.7, 0.5, 1.2), (0.65, 0.5, 1.35),
      ov=[kinetic(ctx, ["AEROPORT"], 0.1, 3.0, x=s(190), y=s(1450), size=140, align="left", anim="slide")])
    V(333.60, 342.00, "v_kc135", 20.5, dark=0.1, trans="dissolve", tdur=0.4,
      ov=[kinetic(ctx, ["YANGI YIL YAQIN SHARQQA", "TINCHLIK OLIB KELADIMI?"], 0.2, 4.3, size=170),
          kinetic(ctx, ["YOKI BU BO‘RON OLDIDAN", "SUKUNATMI?"], 4.5, 8.4, size=170, accent=1)])
    G(342.00, 347.90, scenes.end_card(), trans="dip", tdur=0.4, cr=None)
    return shots


def global_overlays(ctx):
    return [bug(ctx, 19.6, 341.8)]
