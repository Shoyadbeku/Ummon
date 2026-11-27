# -*- coding: utf-8 -*-
"""
STORYBOARD — «Ormuz inqirozi» (audio: 339.62 s)
Har bir kadr: (tugash_vaqti, manba_kodi, manba_boshlanishi, rejim, izoh)
Boshlanish vaqti = oldingi kadrning tugash vaqti. Vaqtlar ovoz transkripsiyasidan (Whisper large-v3, so‘z darajasi) olingan.
rejim: fill | blur (vertikal/kvadrat video, xira fon bilan) | crop:x,y,w,h (ulushlarda) | cropblur:x,y,w,h
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- MANBALAR (fayl, ekrandagi kredit, asl havola) -------------------------
SRC = {
 # X (Twitter) — foydalanuvchi bergan postlar
 "xa":  ("x_footage/aprajitanefes_2126327071958028288_11.mp4", "VIDEO: @aprajitanefes / X  •  IRGC tarqatgan kadr", "https://x.com/aprajitanefes/status/2126327133517885738"),
 "xp":  ("x_footage/PressTV_2126276138691375104_01.mp4", "VIDEO: @PressTV / X  •  IRGC kadri", "https://x.com/PressTV/status/2126276172296139225"),
 "xdc": ("x_footage/DC_Global_News_2126340400600215552_08.mp4", "VIDEO: @DC_Global_News / X  •  IRGC kadri", "https://x.com/DC_Global_News/status/2126340435454906605"),
 "xd2": ("x_footage/Danale_2126357713894383617_02.mp4", "VIDEO: @Danale / X  •  IRGC kadri (F-16)", "https://x.com/Danale/status/2126357809659011190"),
 "xf15":("x_footage/DefendtheFieldx_2125392157330567168_15.mp4", "VIDEO: @DefendtheFieldx / X  •  IRGC kadri", "https://x.com/DefendtheFieldx/status/2125392244689551509"),
 "xf16":("x_footage/DefendtheFieldx_2125392157343137792_16.mp4", "VIDEO: @DefendtheFieldx / X", "https://x.com/DefendtheFieldx/status/2125392244689551509"),
 "xf18":("x_footage/DefendtheFieldx_2125392157338955776_18.mp4", "VIDEO: @DefendtheFieldx / X  •  IRGC kadri", "https://x.com/DefendtheFieldx/status/2125392244689551509"),
 "xdt": ("x_footage/Detektor0000_2125620145464705024_13.mp4", "VIDEO: @Detektor0000 / X  •  IRGC kadri", "https://x.com/Detektor0000/status/2125620213873881377"),
 "xef": ("x_footage/EnglishFars_2124106057509208064_14.mp4", "VIDEO: @EnglishFars / X  •  IRGC kadri", "https://x.com/EnglishFars/status/2124106094901449170"),
 "xcl": ("x_footage/clashreport_2126351505179496448_19.mp4", "VIDEO: @clashreport / X  •  LaPresse", "https://x.com/clashreport/status/2126351558002561429"),
 "xdd": ("x_footage/DD_Recon_2126352264344322048_12.mp4", "VIDEO: @DD_Recon / X", "https://x.com/DD_Recon/status/2126352304387285153"),
 "xad": ("x_footage/AdriansCryptoo_2126343699554562048_22.mp4", "VIDEO: @AdriansCryptoo / X", "https://x.com/AdriansCryptoo/status/2126343744974660031"),
 # YouTube — snapyt.app orqali yuklab olingan
 "y01": ("youtube_footage/Y01_AlJazeera_two_tankers_mines.mp4", "FOOTAGE: Al Jazeera English / YouTube", "https://www.youtube.com/watch?v=sprwU_cYFvo"),
 "y02": ("youtube_footage/Y02_AlJazeera_three_tankers_mines.mp4", "FOOTAGE: Al Jazeera English / YouTube", "https://www.youtube.com/watch?v=JO-rxaBlbOk"),
 "y03": ("youtube_footage/Y03_NYPost_violating_tankers.mp4", "FOOTAGE: New York Post / YouTube", "https://www.youtube.com/watch?v=NNlqFk8Vy1U"),
 "y04": ("youtube_footage/Y04_AlJazeera_how_hormuz_works.mp4", "FOOTAGE: Al Jazeera English / YouTube", "https://www.youtube.com/watch?v=tW3degbCJBA"),
 "y05": ("youtube_footage/Y05_BBC_US_Israel_attack_Feb28.mp4", "ARXIV: BBC News / YouTube  •  28.02.2026", "https://www.youtube.com/watch?v=Ks13eyBeW7w"),
 "y06": ("youtube_footage/Y06_AlJazeera_US_blockade_explained.mp4", "ARXIV: Al Jazeera English / YouTube", "https://www.youtube.com/watch?v=poEZJ4SOkvU"),
 "y07": ("youtube_footage/Y07_Arirang_MOU_blockade_lift.mp4", "ARXIV: Arirang News / YouTube", "https://www.youtube.com/watch?v=nR2hTvHvFOY"),
 "y08": ("youtube_footage/Y08_CBS_Iran_end_blockade.mp4", "FOOTAGE: CBS News / YouTube", "https://www.youtube.com/watch?v=JhrdkTUYgak"),
 "y09": ("youtube_footage/Y09_BBC_Kuwait_drone_italians.mp4", "FOOTAGE: BBC News / YouTube", "https://www.youtube.com/watch?v=MpEcr0JLRTU"),
 "y11": ("youtube_footage/Y11_France24_Kuwait_italians.mp4", "FOOTAGE: FRANCE 24 English / YouTube", "https://www.youtube.com/watch?v=Bzh3VlSkD2Y"),
 "y13": ("youtube_footage/Y13_AlJazeera_Qatar_mediation.mp4", "FOOTAGE: Al Jazeera English / YouTube", "https://www.youtube.com/watch?v=49kTbCXVT6g"),
 "y14": ("youtube_footage/Y14_Trump_whenever_I_want.mp4", "VIDEO: YouTube / Jordan Rachel (qayta joylangan)", "https://www.youtube.com/watch?v=cs9RqADhfvw"),
 "y15": ("youtube_footage/Y15_Israel_ready_strike_without_US.mp4", "VIDEO: YouTube / Viral Desk", "https://www.youtube.com/watch?v=qwSE-0ZIfC8"),
 "y16": ("youtube_footage/Y16_AFP_Bandar_Abbas.mp4", "ARXIV: AFP News Agency / YouTube", "https://www.youtube.com/watch?v=-LFqajqjpRY"),
 "y17": ("youtube_footage/Y17_euronews_Uzbekistan_transport.mp4", "FOOTAGE: euronews / YouTube", "https://www.youtube.com/watch?v=A3KHabrBvXI"),
 "y18": ("youtube_footage/Y18_AlJazeera_oil_prices_surge.mp4", "ARXIV: Al Jazeera English / YouTube", "https://www.youtube.com/watch?v=cj8yVm4RtI4"),
 "y21": ("youtube_footage/Y21_NBC_blockade_in_effect.mp4", "ARXIV: NBC News / YouTube", "https://www.youtube.com/watch?v=W_Kj8JOCzGM"),
 "y22": ("youtube_footage/Y22_africanews_Iran_denies_Kuwait.mp4", "FOOTAGE: africanews / YouTube", "https://www.youtube.com/watch?v=4Pvrg0MdLJw"),
 "y24": ("youtube_footage/Y24_AlJazeera_Araghchi_presser_archive.mp4", "ARXIV: Al Jazeera English / YouTube", "https://www.youtube.com/watch?v=uYdVBltkZmo"),
}

# ---- KADRLAR -----------------------------------------------------------------
# (tugash, manba, manba_ss, rejim, audio/izoh)
SHOTS = [
 # HOOK 0–17.3
 (1.60,  "xef", 7.0,  "fill", "Dunyodagi eng muhim dengiz yoʻlida..."),
 (2.70,  "xf15",8.0,  "blur", "...neft tankeri"),
 (4.10,  "xp",  0.3,  "fill", "...minaga urilib portladi."),
 (6.20,  "xa",  9.0,  "fill", "Bu xabarni bugun IRGCning oʻzi eʼlon qildi."),
 (8.40,  "xd2", 8.0,  "fill", "(IRGC: F-16 kadri)"),
 (10.60, "y18", 1.0,  "fill", "Shu hafta boshida ... neft narxi"),
 (13.90, "y04", 137.0,"fill", "...yana tez koʻtarila boshladi."),
 (17.30, "y09", 16.5, "fill", "Kuvaytda ikki nafar Yevropa fuqarosi halok boʻldi."),
 # SAVOLLAR 17.3–30
 (21.90, "GFX", 0,    "map_uz", "Ormuzda nima boʻlyapti? Bu joy Oʻzbekistondan minglab km uzoqda."),
 (24.50, "y17", 9.0,  "fill", "Unda nega bizning hamyonimizga taʼsir qilishi mumkin?"),
 (27.80, "xf18",12.0, "fill", "Va eng asosiy savol: bu urush qachon tugaydi?"),
 (30.00, "y04", 188.0,"fill", "Keling, tartib bilan koʻrib chiqamiz. [SARLAVHA]"),
 # 1-QISM: TANKER VA MINA 30–57.6
 (34.70, "xa",  1.0,  "fill", "Bugun 27-noyabr kuni IRGC bayonot tarqatdi."),
 (39.00, "xa",  7.8,  "fill", "Ormuzda neft tankeri dengiz minasiga urilib portlagan."),
 (42.60, "xdc", 6.0,  "cropblur:0.5,0,0.5,1", "Bu maʼlumot Eron tomonidan berildi..."),
 (45.00, "y01", 8.0,  "fill", "...mustaqil manbalar uni tasdiqlagani yoʻq."),
 (47.10, "xf18",67.0, "fill", "Lekin bu yagona holat emas."),
 (51.20, "xdt", 6.0,  "fill", "Shu hafta davomida Eron bir necha marta xabar qildi."),
 (55.40, "y02", 6.0,  "fill", "Al Jazeera maʼlumotiga koʻra..."),
 (57.60, "xf16",0.5,  "blur", "...25 tadan ortiq tanker hujumga uchragan."),
 # RAQAMLAR 57.6–77.3
 (59.00, "y04", 15.0, "fill", "Endi raqamlarga qarang."),
 (64.00, "y03", 111.0,"fill", "Urushdan oldin har kuni 125–140 ta kema oʻtardi."),
 (68.40, "y03", 118.0,"fill", "Noyabr boshidagi bir haftada 226 ta kema."),
 (72.90, "y21", 13.0, "fill", "17–23-noyabr: 125 ta."),
 (77.30, "y06", 59.0, "fill", "Harakat 40 foizdan koʻproq qisqardi."),
 # TARIX 77.3–126.5
 (79.50, "y04", 25.0, "fill", "Bu vaziyat qanday paydo boʻldi?"),
 (86.00, "y05", 12.0,  "fill", "2026-yil 28-fevral: AQSh va Isroil Eronga zarba berdi."),
 (89.60, "y07", 39.5, "fill", "Eron raketa va dronlar bilan javob qaytardi."),
 (93.80, "y05", 31.0, "fill", "AQSh bazalari joylashgan Fors koʻrfazi davlatlari ham nishonga aylandi."),
 (97.50, "y06", 33.0, "fill", "Aprel: AQSh dengiz blokadasi."),
 (102.0, "y07", 23.0, "fill", "Iyul: anglashuv memorandumi, blokada bekor qilindi."),
 (104.1, "y07", 56.0, "fill", "Lekin bu kelishuv uzoq yashamadi."),
 (108.9, "y16", 2.0,  "blur", "Bir necha hafta oʻtib u barbod boʻldi."),
 (113.2, "y21", 442.0,"fill", "Blokada Eron neft eksportini deyarli toʻxtatib qoʻygan."),
 (115.8, "y03", 135.5,"fill", "Tehron bunga Ormuz orqali javob bermoqda."),
 (118.2, "y08", 9.0,  "fill", "Boʻgʻoz talablar bajarilmaguncha ochilmaydi."),
 (120.4, "y04", 20.0, "fill", ""),
 (126.5, "y07", 99.0, "fill", "Talablar uchta. [GRAFIKA]"),
 # KUVAYT 126.5–152.8
 (129.9, "y11", 4.0,  "fill", "26-noyabr: keskinlik yangi darajaga chiqdi."),
 (132.6, "y11", 64.0, "fill", "Kuvaytdagi harbiy obyektlarga dronlar hujum qildi."),
 (136.2, "y09", 90.0, "fill", "Antonio Tayani parlamentga maʼlum qildi..."),
 (141.3, "xcl", 3.0,  "fill", "...ikki italiyalik mutaxassis halok boʻldi."),
 (145.1, "xdd", 1.0,  "fill", "Kuvayt armiyasi: raketa parchalaridan halok boʻlgan..."),
 (147.6, "y22", 19.0, "fill", "...voqeani Eron agressiyasi deb atadi."),
 (152.8, "GFX", 0,    "map_gulf", "Saudiya, Bahrayn, Qatar va BAA hujumni qoraladi."),
 # ERON RAD ETADI 152.8–167.6
 (155.1, "y24", 22.0, "crop:0.08,0,0.84,0.84", "Eron ayblovni butunlay rad etdi."),
 (159.0, "y24", 64.0, "crop:0.08,0,0.84,0.84", "TIV Abbos Araqchi voqeani shubhali deb atadi."),
 (163.7, "y24", 205.0,"crop:0.08,0,0.84,0.84", "«...urush uchun oldindan tayyorlab qoʻyilgan retsept»"),
 (167.6, "xcl", 23.5, "fill", "Tehron Italiya va Kuvayt bilan birga tergov oʻtkazishni taklif qildi."),
 # NEGA MUHIM 167.6–178.6
 (170.2, "y04", 189.0,"fill", "Xoʻsh, bularning barchasi nega muhim?"),
 (172.8, "y04", 31.0, "fill", "Chunki Ormuz oddiy boʻgʻoz emas."),
 (178.6, "y07", 46.0, "fill", "Dunyo neftining qariyb beshdan bir qismi... [GRAFIKA]"),
 # NEFT NARXI 178.6–199.7
 (180.4, "y18", 5.0,  "fill", "Bozor darhol javob berdi."),
 (192.2, "GFX", 0,    "oil_chart", "24-noyabr: ~$88 ... Bugun: $96–97"),
 (196.9, "y04", 137.5,"fill", "Oktabrda neft har kuni 100 dollardan qimmat turgan."),
 (199.7, "y04", 147.0,"fill", "Oy oxirida 114 dollarga yetgan edi."),
 # OʻZBEKISTON 199.7–245.4
 (202.3, "y17", 7.0,  "fill", "Bu Oʻzbekistonga qanday aloqador?"),
 (204.8, "y17", 270.0,"fill", "Urush chegaralarimizga yetib kelgani yoʻq."),
 (208.6, "y17", 165.0,"fill", "Lekin taʼsiri bilvosita boʻlishi aytilgan edi."),
 (214.5, "y17", 232.0,"fill", "Kun.uz tahlili (mart). [GRAFIKA]"),
 (218.5, "y17", 112.0,"fill", "Energiya narxlari, yuk tashish, sugʻurta. [GRAFIKA]"),
 (224.4, "GFX", 0,    "map_route", "Bandar Abbos porti ~90% yuklarni qabul qiladi."),
 (229.8, "y17", 187.0,"fill", "Dengizga chiqish yoʻli boʻlmagan Oʻzbekiston uchun..."),
 (233.1, "y04", 169.0,"fill", "Yoqilgʻi qimmatlashsa..."),
 (238.9, "y17", 150.0,"fill", "...yuk tashish va import narxi. [GRAFIKA]"),
 (241.4, "y03", 44.0, "fill", "Ormuzdagi har bir mina..."),
 (245.4, "y17", 127.0,"fill", "...oddiy xaridor uchun ham ogohlantirish."),
 # KEYIN NIMA? 245.4–268.3
 (248.7, "y21", 86.0, "fill", "Bundan keyin nima boʻladi?"),
 (254.4, "y14", 0.0,  "blur", "Tramp PBSga: gʻalaba yaqin."),
 (260.0, "y14", 6.0,  "blur", "«Ochigʻini aytsam, qachon xohlasam, oʻshanda.»"),
 (264.0, "y05", 140.0,"fill", "Vashington Eronga har qanday imkoniyat bermoqda..."),
 (268.3, "y14", 14.0, "blur", "...lekin Tehron rozi boʻlishiga ishonchi komil emas."),
 # ISROIL 268.3–277
 (273.4, "y15", 0.3,  "blur", "Effi Defrin: Isroil istalgan daqiqada..."),
 (277.0, "y15", 13.5, "blur", "...hatto AQShsiz ham zarba berishga tayyor."),
 # QATAR 277–290.6
 (280.4, "y13", 12.0, "blur", "Diplomatiya toʻxtagani yoʻq."),
 (284.5, "y13", 29.0, "blur", "Qatar tinchlik muzokaralarini tiklashga harakat qilmoqda."),
 (290.6, "y08", 108.0,"crop:0,0.03,0.66,0.74", "Doha: Kuvaytga hujumlar diplomatiyaga zarar yetkazishi mumkin."),
 # SSENARIYLAR 290.6–308.5
 (302.5, "y21", 319.0,"fill", "Oldinda bir necha yoʻl bor. [GRAFIKA]"),
 (305.0, "y18", 11.0, "fill", "Aniq boʻlgan bitta narsa bor:"),
 (308.5, "xad", 0.0,  "fill", "bozorlar har bir yangi xabarga keskin javob bermoqda."),
 # XULOSA 308.5–339.62
 (312.3, "xf18",72.0, "cropblur:0.28,0,0.44,1", "Urush yana Ormuz boʻgʻoziga qaytdi."),
 (314.1, "xef", 18.0, "fill", "Tankerlar minaga urilmoqda."),
 (317.7, "y03", 122.0,"fill", "Kemalar soni keskin kamaydi."),
 (319.5, "y18", 0.0,  "fill", "Neft narxi yana koʻtarildi."),
 (323.6, "y17", 190.0,"fill", "Bu voqealar bizdan minglab km uzoqda..."),
 (326.9, "y17", 2.0,  "fill", "...lekin taʼsiri har bir mamlakat iqtisodiyotiga yetib boradi."),
 (333.0, "y04", 190.0,"fill", "Savol: Ormuzdagi inqiroz Oʻzbekistondagi narxlarga taʼsir qiladimi? [GRAFIKA]"),
 (339.62,"y04", 15.5, "fill", "Fikringizni izohlarda yozing. [YAKUNIY KARTA]"),
]

# ---- GRAFIKA QATLAMLARI (vaqt bo‘yicha) ----------------------------------------
# type, start, end, props
OVERLAYS = [
 ("hook_title", 0.25, 4.0, {"kicker": "SHOSHILINCH", "title": "ORMUZ BOʻGʻOZI", "sub": "Neft tankeri minaga urilib portladi"}),
 ("lower_third", 4.3, 8.3, {"name": "IRGC bayonoti", "role": "Eron Islom inqilobi qoʻriqchilari korpusi  •  27-noyabr 2026"}),
 ("price_tag", 10.8, 13.9, {"label": "BRENT", "from": "$88", "to": "$96–97", "note": "24–27-noyabr"}),
 ("lower_third", 14.1, 17.2, {"name": "Kuvayt", "role": "Dron hujumi: 2 nafar Italiya fuqarosi halok boʻldi"}),
 ("title_card", 27.9, 30.0, {"title": "ORMUZ INQIROZI", "sub": "Minalar, neft va bizning hamyonimiz"}),
 ("date_stamp", 30.2, 34.6, {"date": "27-NOYABR 2026", "text": "IRGC bayonoti"}),
 ("location", 34.8, 38.9, {"place": "Gʻanam oroli shimoli", "region": "Ormuz boʻgʻozi"}),
 ("warning", 39.1, 45.0, {"title": "TASDIQLANMAGAN", "text": "Maʼlumot manbasi — IRGC. Mustaqil tasdiq hozircha yoʻq."}),
 ("big_number", 51.4, 57.5, {"value": 25, "suffix": "+", "label": "tanker hujumga uchragan", "note": "24-noyabrgacha bir hafta  •  Manba: Al Jazeera"}),
 ("traffic_chart", 59.0, 77.3, {}),
 ("timeline", 79.6, 120.3, {}),
 ("demands", 120.4, 126.5, {}),
 ("date_stamp", 126.6, 129.8, {"date": "26-NOYABR 2026", "text": "Kuvayt"}),
 ("lower_third", 132.8, 136.1, {"name": "Antonio Tayani", "role": "Italiya Tashqi ishlar vaziri"}),
 ("stat_line", 136.4, 141.2, {"value": "2", "text": "italiyalik mutaxassis halok boʻldi", "note": "Havo hujumidan mudofaa radar markazi"}),
 ("lower_third", 155.3, 158.9, {"name": "Abbos Araqchi", "role": "Eron Tashqi ishlar vaziri  •  ARXIV KADR"}),
 ("quote", 159.0, 163.6, {"text": "Bu urush uchun oldindan tayyorlab qoʻyilgan retseptga oʻxshaydi.", "who": "Abbos Araqchi, Eron TIV"}),
 ("share_fifth", 172.9, 178.5, {}),
 ("oil_chart", 180.4, 192.2, {}),
 ("price_tag", 192.4, 196.8, {"label": "OKTABR", "from": "", "to": "> $100", "note": "har kuni"}),
 ("price_tag", 197.0, 199.6, {"label": "OKTABR OXIRI", "from": "", "to": "$114", "note": "barrel"}),
 ("source_card", 208.8, 214.4, {"kicker": "TAHLIL", "title": "Mutaxassislar uch yoʻnalishni koʻrsatgan", "source": "Manba: Kun.uz, mart 2026"}),
 ("three_dirs", 214.5, 218.4, {}),
 ("chain", 233.2, 238.8, {}),
 ("kinetic", 245.6, 248.6, {"text": "BUNDAN KEYIN NIMA BOʻLADI?"}),
 ("lower_third", 248.9, 254.2, {"name": "Donald Tramp", "role": "AQSh prezidenti  •  PBS intervyusidan"}),
 ("quote", 254.5, 259.9, {"text": "Ochigʻini aytsam — qachon xohlasam, oʻshanda.", "who": "Donald Tramp, PBS"}),
 ("lower_third", 268.5, 273.3, {"name": "Effi Defrin", "role": "Isroil armiyasi matbuot kotibi"}),
 ("quote", 273.5, 276.9, {"text": "Isroil Eronga istalgan daqiqada, hatto AQSh kuchlarisiz ham zarba berishga tayyor.", "who": "Effi Defrin"}),
 ("lower_third", 280.6, 284.4, {"name": "Shayx Muhammad bin Abdurahmon Ol Soniy", "role": "Qatar Bosh vaziri va TIV"}),
 ("scenarios", 290.7, 302.4, {}),
 ("recap", 308.6, 319.4, {}),
 ("question", 327.0, 333.0, {"text": "Ormuzdagi inqiroz Oʻzbekistondagi narxlarga taʼsir qiladimi?"}),
 ("end_card", 333.0, 339.62, {}),
]

# ---- SFX (vaqt, fayl, balandlik dB) ------------------------------------------
SFX = [
 (0.00, "impact", -4), (1.58, "whoosh", -12), (2.68, "hit", -10), (4.05, "whoosh", -14),
 (8.38, "whoosh", -15), (13.85, "whoosh", -15), (17.25, "riser", -18), (21.85, "whoosh", -15),
 (26.0, "riser", -16), (27.9, "impact", -8), (30.0, "whoosh", -14), (39.05, "glitch", -14),
 (51.4, "tick", -12), (59.0, "whoosh", -15), (77.3, "glitch", -14), (79.6, "hit", -12),
 (93.8, "tick", -14), (97.5, "tick", -14), (104.1, "tick", -14), (126.5, "impact", -12),
 (152.8, "whoosh", -15), (159.0, "hit", -14), (167.6, "whoosh", -15), (178.6, "whoosh", -15),
 (199.7, "whoosh", -15), (224.4, "whoosh", -15), (245.4, "riser", -20), (248.6, "hit", -12),
 (290.6, "whoosh", -15), (308.5, "impact", -12), (327.0, "hit", -14), (333.0, "whoosh", -14),
]

FPS = 30
DURATION = 339.62

def build():
    shots = []; t0 = 0.0
    for (t1, src, ss, mode, note) in SHOTS:
        assert t1 > t0, (t1, t0)
        sid = f"s{len(shots)+1:03d}"
        shot = {"id": sid, "start": round(t0, 3), "end": round(t1, 3), "src": src, "ss": ss, "mode": mode, "note": note}
        if src != "GFX":
            f, credit, url = SRC[src]
            shot.update({"file": f, "credit": credit, "url": url})
        shots.append(shot); t0 = t1
    assert abs(t0 - DURATION) < 0.01
    ov = [{"type": a, "start": b, "end": c, "props": d} for (a, b, c, d) in OVERLAYS]
    data = {"fps": FPS, "duration": DURATION, "shots": shots, "overlays": ov,
            "sfx": [{"t": t, "name": n, "db": db} for (t, n, db) in SFX]}
    os.makedirs(os.path.join(ROOT, "src", "data"), exist_ok=True)
    json.dump(data, open(os.path.join(ROOT, "src", "data", "storyboard.json"), "w"), ensure_ascii=False, indent=1)
    return data

if __name__ == "__main__":
    d = build()
    print(len(d["shots"]), "kadr;", len(d["overlays"]), "grafika;", len(d["sfx"]), "SFX")
