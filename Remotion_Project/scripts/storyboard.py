"""Storyboard: one entry per spoken sentence of the original narration.

Each entry: (start, end, uzbek_text, shots, extras)
  start/end : seconds in the ORIGINAL audio (from Whisper word timestamps)
  text      : corrected Uzbek (Latin) transcript of what is said - used for subtitles
  shots     : list of shots shown while the sentence is spoken; the scene time is split evenly.
              shot = (source_id, source_start_seconds, crop, label)
              crop = None or (x, y, w, h) as fractions of the source frame (removes burned-in captions/banners)
  extras    : overlays: chapter / lower-third / counter / map / title / quote
Scenes with text=None are pauses (chapter cards). Visual scene i lasts until scene i+1 starts.
"""

T74 = (0, 0, 1, 0.74)      # cut bottom TV banner
T80 = (0, 0, 1, 0.80)
T82 = (0, 0, 1, 0.82)
NOSTK = (0.21, 0.09, 0.66, 0.73)
PHC = (0.02, 0.09, 0.88, 0.73)  # sWvd photos: cut captions + channel logo  # also cut "subscribe" sticker + channel logo
EURO = (0.18, 0.0, 0.64, 0.64)  # euronews: face, above burned subtitles
BBC_R = (0.0, 0.0, 1.0, 0.74)

AP, DIF_S, DIF_R, DIF_M = "tFZX0vsbbTw", "TKKHSc1kSiU", "wy-5WpNg5zo", "GtAS4PD_kx8"
IWF, G9, RMX, TVN, X6, PH = "IwFoyh_JpsY", "9GfrarB7YOY", "RMxj9cbCRo4", "dHbEiZ-Im0s", "6X77qiqwbz0", "sWvdYQW0Bx8"
PAR_N, PAR_E, CAN_B, CAN_C, VIZ = "_FxE8ODZUyg", "kt-EFUdcjc4", "8q8GKalkCZg", "2cM0Noskgnw", "1CXnPtoexHU"
CAT_T, CAT_A = "hxxaOYnudYE", "cDRzvf3PxtI"
VALLE, GLAC, MVD, MDZ, SCL = "dWjfEqPdwmQ", "JnckFwa5zDs", "NZ8LzY3G3k4", "BDZtDJpIsiw", "yc6qBp23Emc"
FH_FAU, FH_67, MUSEO, ANNIV, CREW = "4RyZfmtovFQ", "UWJid5np8BE", "uoXkaGZ-Cp8", "lo1T24khxXY", "FiiNBZgdhKs"
ALIVE93, STRAND, BOOK, SOCIETY = "3P5N0kd6pYY", "WNgU5Qn3fmY", "aT8QnT_lvFU", "pDak4qLyF4Q"

S = []
def sc(start, end, text, shots, **extras):
    S.append(dict(start=start, end=end, text=text, shots=shots, extras=extras))

# ---------------- HOOK ----------------
sc(0.00, 11.82, "1972-yil 13-oktabr kuni Janubiy Amerikadagi And tog'larida Urug'vay harbiy-havo kuchlariga tegishli samolyot halokatga uchradi.",
   [(PH, 100.0, NOSTK, "Fuselaj, And tog'lari, 1972"), (DIF_S, 9.5, None, "And tog'lari, 1972 (arxiv)"), (PH, 194.0, PHC, "Omon qolganlar, 1972")],
   title=dict(main="AND TOG'LARI MO'JIZASI", sub="571-reys • 13.10.1972 — 23.12.1972"))
sc(12.16, 14.82, "Samolyot bortida 45 kishi bo'lgan.",
   [(PH, 1.0, PHC, "Halokatdan oldingi so'nggi surat")], counter=dict(value=45, label="kishi bortda"))
sc(15.36, 24.14, "Ularning asosiy qismini Urug'vayning Old Christians Club regbi jamoasi a'zolari, shuningdek, ularning do'stlari va yaqinlari tashkil etgan.",
   [(CAN_B, 213.0, BBC_R, "Old Christians Club, 1972"), (VALLE, 9.3, None, "Jamoa samolyot oldida, 1972"), (CAN_B, 203.0, BBC_R, None)],
   lt=("Old Christians Club", "Montevideo, Urug'vay • regbi jamoasi"))
sc(24.14, 32.34, "Halokatdan keyin yo'lovchilar dengiz sathidan taxminan 3 500 metr balandlikdagi muzlik hududida qolib ketishgan.",
   [(VALLE, 0.5, None, "Halokat joyi koordinatalari"), (GLAC, 20.0, None, "Ko'z yoshlari vodiysi muzligi")],
   counter=dict(value=3500, label="metr balandlik", suffix=" m"))
sc(33.18, 41.64, "Ular oziq-ovqat yetishmasligi, kuchli sovuq, jarohatlar va tashqi dunyo bilan aloqa yo'qligi sharoitida yashashga majbur bo'lgan.",
   [(PH, 20.0, PHC, "Omon qolganlar, 1972-yil noyabr"), (PH, 66.0, PHC, None)])
sc(42.44, 48.16, "Qidiruv ishlari to'xtatilganiga qaramay, omon qolganlar mustaqil ravishda qutulish yo'lini izlashgan.",
   [(ANNIV, 40.5, None, "\"Harbiy samolyotni qidirish rasman bekor qilindi\" — 1972"), (PH, 260.0, PHC, None)])
sc(48.16, 54.78, "72 kun davom etgan favqulodda vaziyat yakunida 16 kishi qutqarilgan.",
   [(AP, 33.0, None, "Los Maytenes, 1972-yil dekabr"), (AP, 41.0, None, None)], counter=dict(value=16, label="kishi qutqarildi", pre="72 kun"))
sc(55.58, 62.00, "Tarixda ushbu hodisa \"And tog'lari mo'jizasi\", ya'ni \"Miracle of the Andes\" nomi bilan tanilgan.",
   [(CAT_A, 57.0, None, "1972-yil gazetalari: \"Mo'jiza! Tirik qolganlar bor\""), (ANNIV, 13.6, None, None)],
   quote="\"Miracle of the Andes\"")
sc(62.76, 76.86, "Bu voqea aviatsiya xavfsizligi, inson organizmining ekstremal sharoitlarga moslashuvi, guruh bo'lib omon qolish va favqulodda vaziyatlarda qaror qabul qilish masalalarini o'rganishda muhim tarixiy saboqlardan biri hisoblanadi.",
   [(MUSEO, 70.2, None, "Museo Andes 1972, Montevideo"), (MUSEO, 59.4, None, None), (ANNIV, 10.2, None, None), (MUSEO, 16.2, None, None)])

# ---------------- CHAPTER 1 ----------------
sc(76.86, 80.56, "Samolyot halokatining asosiy sabablari.",
   [(FH_FAU, 8.0, None, None)], chapter=("I", "SAMOLYOT HALOKATINING ASOSIY SABABLARI"))
sc(81.44, 88.82, "571-reys Fairchild FH-227D rusumli ikki dvigatelli samolyotda amalga oshirilgan.",
   [(FH_FAU, 9.0, None, "Urug'vay HHK FH-227 samolyoti (bir xil turdagi)"), (FH_67, 26.0, None, "Fairchild FH-227, 1967")],
   lt=("Fairchild FH-227D", "571-reys • ikki dvigatelli turbovintli samolyot"))
sc(89.52, 95.10, "Parvoz Urug'vay poytaxti Montevideodan Chilining Santyago shahriga rejalashtirilgan.",
   [(MVD, 30.0, None, "Montevideo, Urug'vay")], map="route")
sc(95.68, 104.00, "Noqulay ob-havo sababli samolyot Argentina hududidagi Mendosa shahrida to'xtagan va safarini ertasi kuni davom ettirgan.",
   [(MDZ, 1.0, None, "Mendosa, Argentina"), (ANNIV, 30.8, None, "\"Mendosadagi so'nggi suratlar\" — 1972 gazetasi"), (CAN_C, 299.0, None, "\"Uruguay samolyoti Mendosadan uchdi\" — 1972")])
sc(104.00, 111.18, "13-oktabr kuni And tog'lari ustidan uchish vaqtida ekipaj navigatsiya xatosiga yo'l qo'ygan.",
   [(DIF_S, 28.5, None, "Kabina, 1972 (arxiv)"), (DIF_S, 3.0, None, None)], map="error")
sc(112.06, 125.74, "Samolyot boshqa yo'nalishda bo'lgan; ikkinchi uchuvchi tog' tizmasidan o'tib bo'lingan, deb hisoblagan. Aslida esa samolyot hali ham xavfli tog'li hududda bo'lgan. Ko'rish imkoniyati bulutlar sababli cheklangan.",
   [(DIF_S, 14.0, None, None), (DIF_S, 36.0, None, None), (DIF_S, 6.0, None, None)], map="error")
sc(126.40, 129.86, "Ekipaj pasayishni boshlaganida samolyot toqqa urilgan.",
   [(DIF_S, 48.0, None, "And tog'lari, 1972 (arxiv)")])
sc(130.68, 134.52, "Zarba natijasida samolyotning qanotlari va dum qismi ajralib ketgan.",
   [(PH, 143.0, PHC, "Samolyotning dum qismi, 1972")])
sc(135.18, 139.72, "Asosiy korpus esa qorli yonbag'ir bo'ylab sirpanib, muzlikda to'xtagan.",
   [(PH, 120.0, PHC, "Fuselaj muzlikda, 1972"), (IWF, 42.0, (0, 0, 1, 0.8), None)])
sc(139.72, 150.02, "Halokat vaqtida 12 kishi vafot etgan. Keyingi kunlarda yana 5 kishi olgan jarohatlari oqibatida hayotdan ko'z yumgan.",
   [(VALLE, 62.5, None, "Halokat qurbonlari xotirasiga yodgorlik"), (VALLE, 66.0, None, None)],
   counter=dict(value=12, label="kishi halokatda vafot etdi", then=dict(value=5, label="keyingi kunlarda")))
sc(150.66, 163.76, "Dastlabki zarbadan omon qolganlar orasida tibbiy yordam ko'rsatish imkoniyatiga ega bo'lganlar ham bor edi. Tibbiyot talabasi Roberto Kanessa va boshqa yo'lovchilar jarohatlanganlarga yordam berishga harakat qilgan.",
   [(PH, 160.0, PHC, None), (CAN_C, 322.5, None, "Roberto Kanessa (o'ngda), 1970-yillar"), (MUSEO, 30.0, None, None)],
   lts=[None, ("Roberto Kanessa", "tibbiyot talabasi, 19 yosh (1972)"), ("Roberto Kanessa", "bugun — shifokor")])
sc(164.30, 171.80, "Biroq professional tibbiy jihozlar, dori-darmon va zarur sharoitlarning yetishmasligi vaziyatni murakkablashtirgan.",
   [(PH, 160.0, PHC, "Omon qolganlar fuselaj ichida, 1972")])

# ---------------- CHAPTER 2 ----------------
sc(172.26, 176.50, "Muzlikda omon qolish sharoitlari.",
   [(GLAC, 40.0, None, None)], chapter=("II", "MUZLIKDA OMON QOLISH SHAROITLARI"))
sc(176.86, 181.54, "Halokat joyi Argentina hududidagi baland tog'li muzlikda joylashgan edi.",
   [(VALLE, 47.0, None, "Ko'z yoshlari vodiysi, Argentina (bugun)"), (VALLE, 53.0, None, None)])
sc(182.24, 192.66, "Bunday hududlarda havo harorati keskin pasayishi, kuchli shamollar, qor bo'ronlari va kislorod bosimining pastligi inson organizmi uchun jiddiy xavf tug'diradi.",
   [(GLAC, 0.5, None, "Muzlik, halokat hududi"), (GLAC, 62.0, None, None), (GLAC, 112.0, None, None)],
   info=["Harorat: −30 °C gacha", "Kuchli shamol va qor bo'ronlari", "Kislorod bosimi past"])
sc(193.34, 203.74, "Samolyot yo'lovchilari tog'larda uzoq muddat yashash uchun zarur jihozlar bilan ta'minlanmagan. Ularning kiyimlari asosan oddiy sayohat va sport mashg'ulotlariga mos bo'lgan.",
   [(PH, 48.0, PHC, "Old Christians o'yinchilari fuselaj yonida, 1972"), (PH, 28.0, PHC, None)])
sc(204.14, 217.90, "Omon qolganlar samolyotning asosiy korpusidan vaqtinchalik boshpana sifatida foydalanishgan. Ular samolyot o'rindiqlari va boshqa materiallar yordamida ochiq qismlarni yopishga, sovuq havoning kirishini kamaytirishga urinishgan.",
   [(PH, 103.0, NOSTK, "Fuselaj — vaqtinchalik boshpana, 1972"), (PH, 176.0, PHC, None), (PH, 70.0, PHC, None)])
sc(218.72, 227.78, "Ichimlik suvi masalasi qor eritish orqali hal qilingan. Samolyot qoldiqlaridagi metall buyumlar quyosh nuri yordamida qor eritish uchun ishlatilgan.",
   [(ANNIV, 71.4, None, "Fuselaj maketi, Museo Andes 1972"), (PH, 67.0, PHC, None)])
sc(228.48, 240.80, "Ammo oziq-ovqat masalasi ancha murakkab bo'lgan. Samolyotda faqat oz miqdorda shokolad, shirinlik va boshqa yeguliklar mavjud edi. Ushbu zaxiralar uzoq vaqtga yetmagan.",
   [(PH, 36.0, PHC, None), (ANNIV, 75.0, None, "Museo Andes 1972")],
   info=["Shokolad", "Shirinliklar", "Oz miqdordagi yeguliklar"])
sc(240.80, 268.04, "Inson organizmi sovuq sharoitda tana haroratini saqlash uchun qo'shimcha energiya sarflaydi. Oziq-ovqat yetishmaganda organizm avval energiya zaxiralaridan, keyin esa yog' va mushak to'qimalaridan foydalanadi. Bu jarayon uzoq davom etsa, jismoniy kuch kamayadi. Immunitet zaiflashadi va ichki a'zolar faoliyati izdan chiqishi mumkin. And tog'laridagi yo'lovchilar aynan shunday sharoitga duch kelgan.",
   [(GLAC, 25.0, None, None), (GLAC, 90.0, None, None), (PH, 163.0, PHC, None), (PH, 23.0, PHC, None)],
   body=True)

# ---------------- search ----------------
sc(268.84, 280.48, "Qidiruv ishlarining to'xtatilishi. Samolyot yo'qolgach, Chili va Argentina qutqaruv xizmatlari uni izlashga kirishgan. Qidiruv samolyotlari And tog'larining katta hududini tekshirgan.",
   [(DIF_S, 9.0, None, "Qidiruv parvozi, 1972-yil oktabr"), (DIF_S, 19.0, None, None), (DIF_S, 64.0, None, "Qidiruv guruhi, 1972")],
   sub_chapter="QIDIRUV ISHLARINING TO'XTATILISHI")
sc(281.20, 294.56, "Biroq samolyotning oq rangli korpusi qor bilan qoplangan hududda deyarli sezilmagan. Bundan tashqari, ekipajning navigatsiya xatosi sababli samolyotning taxminiy joylashuvi noto'g'ri baholangan.",
   [(TVN, 1256.0, None, "Fuselaj qor ichida — havodan ko'rinish, 1972"), (TVN, 1047.0, None, None)], map="search")
sc(295.38, 302.48, "Halokatdan keyingi o'n birinchi kuni omon qolganlar radiodan qidiruv ishlari to'xtatilgani haqidagi xabarni eshitishgan.",
   [(ANNIV, 40.8, None, "\"Qidiruv rasman bekor qilindi\" — 1972"), (ANNIV, 42.5, None, None)])
sc(302.86, 310.80, "Rasmiy qidiruv xizmatlari bunday balandlik va sovuqda odamlarning uzoq vaqt tirik qolish ehtimolini juda past deb hisoblagan.",
   [(DIF_S, 52.0, None, None), (DIF_S, 84.0, None, None)])
sc(311.56, 319.18, "Shundan so'ng omon qolganlar tashqi yordamga tayanish imkoniyati cheklanganini tushunib, mustaqil chiqish yo'llarini izlay boshlagan.",
   [(PH, 194.0, PHC, None), (PH, 198.0, PHC, None)])

# ---------------- CHAPTER 3 ----------------
sc(319.86, 333.50, "Ochlik va eng og'ir qaror. Mazkur hodisaning eng ko'p muhokama qilingan jihatlaridan biri — omon qolganlarning oziq-ovqat yetishmasligi sharoitida qabul qilgan qaroridir.",
   [(GLAC, 70.0, None, None), (PH, 160.0, PHC, None)], chapter=("III", "OCHLIK VA ENG OG'IR QAROR"), chapter_len=4.0)
sc(334.25, 344.90, "Tog'li muzlikda o'simliklar, hayvonlar yoki boshqa oziq-ovqat manbalari mavjud bo'lmagan. Uzoq davom etgan ochlik natijasida yo'lovchilarning jismoniy ahvoli yomonlashgan.",
   [(GLAC, 4.0, None, None), (GLAC, 120.0, None, None)])
sc(345.44, 357.04, "Ular oxir-oqibat halokatda vafot etgan insonlarning jasadlaridan oziq sifatida foydalanish qaroriga kelishgan. Bu qaror diniy, axloqiy va ruhiy jihatdan juda og'ir bo'lgan.",
   [(CAT_T, 141.0, T80, "1972-yil gazetasi"), (VALLE, 63.0, None, "Yodgorlik, Ko'z yoshlari vodiysi")])
sc(357.62, 365.34, "Omon qolganlarning aksariyati katolik oilalarda tarbiyalangan va vafot etgan insonlar ularning do'stlari yoki yaqinlari bo'lgan.",
   [(CAN_B, 202.0, BBC_R, "Old Christians jamoasi, 1972")])
sc(366.32, 385.48, "Keyinchalik berilgan intervyularda ular bu qaror zavq yoki istak bilan emas, balki hayotni saqlab qolish zarurati tufayli qabul qilinganini ta'kidlagan. Ushbu holat favqulodda vaziyatlarda insonlarning axloqiy qarorlari va biologik omon qolish ehtiyoji o'rtasidagi murakkab munosabatni ko'rsatadi.",
   [(CAN_B, 101.5, BBC_R, None), (PAR_E, 160.0, EURO, None), (VIZ, 47.0, None, None)],
   lts=[("Roberto Kanessa", "omon qolgan (BBC intervyusi)"), ("Fernando Parrado", "omon qolgan (euronews intervyusi)"), ("Antonio Vizintin", "omon qolgan (El País intervyusi)")])

# ---------------- avalanche ----------------
sc(385.74, 396.60, "29-oktabrdagi qor ko'chkisi. Halokatdan 16 kun o'tib, 29-oktabr kuni omon qolganlar yana bir tabiiy ofatga duch kelgan.",
   [(GLAC, 10.0, None, None), (GLAC, 100.0, None, None)], sub_chapter="29-OKTABR: QOR KO'CHKISI")
sc(397.20, 404.98, "Katta qor ko'chkisi samolyotning boshpana sifatida foydalanilayotgan korpusini bosib qolgan. Natijada 8 kishi vafot etgan.",
   [(PH, 120.0, PHC, None), (IWF, 44.0, (0, 0, 1, 0.8), None)], counter=dict(value=8, label="kishi qor ko'chkisida halok bo'ldi"))
sc(405.74, 420.92, "Tirik qolganlar esa qor ostida qolgan samolyot ichida bir necha kun davomida qamalib qolgan. Ular qor ostidan chiqish yo'lini topishgan.",
   [(GLAC, 130.0, None, None), (PH, 104.0, NOSTK, None), (X6, 88.0, None, None)])
sc(421.22, 431.90, "Noyabrda yana ikki kishi, 11-dekabrda esa yana bir kishi vafot etgan. Natijada 45 kishidan 16 nafari tirik qolgan.",
   [(PH, 133.0, PHC, None)], timeline=True)
sc(432.58, 440.88, "Ular orasida jismoniy jihatdan nisbatan kuchliroq bo'lgan kishilar yordam izlash uchun tog'lardan o'tish rejasini ishlab chiqqan.",
   [(PH, 260.0, PHC, "\"G'arbdagi cho'qqi\" — uch kishi oshib o'tgan tog'")])

# ---------------- CHAPTER 4 ----------------
sc(443.98, 451.30, "Qutqaruv yo'lini izlash. Omon qolganlar avval samolyot atrofidagi hududni o'rganishga urinishgan.",
   [(PH, 147.0, PHC, None)], chapter=("IV", "QUTQARUV YO'LINI IZLASH"))
sc(451.72, 465.44, "15-noyabrda amalga oshirilgan ekspeditsiya davomida samolyotning ajralib ketgan dum qismi topilgan. U yerdan ayrim oziq-ovqat va foydali buyumlar olingan. Ammo bu ekspeditsiya yordam topishga olib kelmagan.",
   [(PH, 143.0, PHC, "Samolyotning dum qismi, 1972-yil noyabr"), (PH, 21.0, PHC, None)])
sc(466.02, 476.94, "Keyinchalik uzoq masofaga yurish uchun maxsus tayyorgarlik boshlangan. Samolyotning izolyatsiya materiallaridan foydalanib, sovuqda tunash imkonini beradigan uyqu qopi tayyorlangan.",
   [(ANNIV, 75.5, None, "Museo Andes 1972 ekspozitsiyasi"), (ANNIV, 10.2, None, None)])
sc(477.48, 491.70, "1972-yil 12-dekabr kuni Fernando Parrado, Roberto Kanessa va Antonio Vizintin yordam izlash uchun yo'lga chiqqan. Ular tog'lar orqali Chili tomon harakat qilishni rejalashtirgan.",
   [(PAR_N, 83.0, None, None), (CAN_C, 347.5, None, None), (VIZ, 92.0, None, None), (PH, 264.0, PHC, None)],
   lts=[("Fernando Parrado", "ekspeditsiya a'zosi, 22 yosh (1972)"), ("Roberto Kanessa", "ekspeditsiya a'zosi, 19 yosh (1972)"), ("Antonio Vizintin", "ekspeditsiya a'zosi, 19 yosh (1972)"), None],
   map="trek")
sc(492.12, 503.68, "Uch kunlik yurishdan keyin Antonio Vizintin qolgan ikki kishiga oziq-ovqat zaxirasini qoldirib, samolyotga qaytgan. Parrado va Kanessa ekspeditsiyani davom ettirgan.",
   [(VIZ, 140.0, None, None), (PAR_N, 112.0, None, None)],
   lts=[("Antonio Vizintin", "3 kundan so'ng fuselajga qaytdi"), None], map="trek")
sc(504.26, 522.72, "Ular qorli cho'qqilar, baland tog' yo'llari va murakkab relyef orqali harakatlangan. Yo'nalish xaritasi va zamonaviy navigatsiya qurollari mavjud bo'lmagan. Bundan tashqari, ikkala insonning organizmi ham ikki oydan ortiq davom etgan ochlik va sovuq tufayli zaiflashgan edi.",
   [(DIF_S, 37.0, None, None), (VALLE, 75.0, None, "And tog'lari, halokat hududi (bugun)"), (GLAC, 35.0, None, None), (DIF_S, 50.0, None, None)])
sc(523.38, 528.12, "Shunga qaramay, ular tog' tizmasidan o'tib, pastroq hududlarga yetib borgan.",
   [(VALLE, 80.0, None, None)])
sc(528.96, 541.64, "Birinchi aloqa. 1972-yil 20-dekabr kuni Fernando Parrado va Roberto Kanessa Chili hududida mahalliy cho'pon Serxio Katalanni uchratgan.",
   [(TVN, 896.0, None, "Los Maytenes, Chili, 1972-yil dekabr"), (TVN, 899.0, None, None), (TVN, 906.0, None, None)],
   sub_chapter="BIRINCHI ALOQA • 20-DEKABR 1972", lt=("Serxio Katalan", "chililik cho'pon (arriero), 1972"))
sc(542.28, 547.76, "Ular daryoning qarama-qarshi tomonlarida bo'lgan sababli ovoz orqali muloqot qilish qiyin kechgan.",
   [(DIF_M, 24.0, None, "Arrierolar, Los Maytenes, 1972"), (G9, 0.5, None, None)])
sc(548.18, 559.52, "Shundan so'ng yozma xabar yordamida aloqa o'rnatilgan. Xabarda ular Urug'vay samolyoti halokatidan omon qolganini va tog'larda yana 14 kishi qolganini bildirgan.",
   [(X6, 132.6, (0.2, 0.0, 0.6, 0.82), "Omon qolganlar yordam so'rab yozgan xatlardan biri, 1972", "freeze"), (PH, 209.0, PHC, "Parrado va Kanessa, Serxio Katalan bilan"), (DIF_M, 7.0, None, "Los Maytenes, 1972")],
   quote="\"...tog'larda yana 14 kishi qoldi\"")
sc(560.52, 569.48, "Serxio Katalan mahalliy hokimiyat va qutqaruv xizmatlariga xabar bergan. Bu ma'lumot dastlab katta hayrat bilan qabul qilingan.",
   [(TVN, 910.0, None, None), (TVN, 952.0, None, None)], lt=("Serxio Katalan", "TVN intervyusi, 1972"))
sc(569.94, 577.22, "Chunki 571-reys yo'lovchilari ikki oydan ortiq vaqt davomida bedarak yo'qolgan deb hisoblangan.",
   [(VALLE, 24.8, None, "\"Yo'qolgan samolyotdan iz yo'q\" — 1972"), (ANNIV, 14.0, None, "\"16 kishi tirik\" — La Nación, 1972")])
sc(578.32, 582.68, "Xabar tasdiqlangach, qutqaruv operatsiyasiga tayyorgarlik boshlangan.",
   [(TVN, 600.0, None, "Chili rasmiylari bayonoti, 1972")])

# ---------------- CHAPTER 5 ----------------
sc(583.88, 594.32, "22–23-dekabr: qutqaruv operatsiyasi. Chili qutqaruv xizmatlari samolyot qoldiqlari joylashgan hududga vertolyotlar yuborgan.",
   [(AP, 16.0, None, "Chili HHK vertolyoti, 1972-yil dekabr"), (TVN, 975.0, None, None), (AP, 20.0, None, None)],
   chapter=("V", "QUTQARUV OPERATSIYASI • 22–23 DEKABR"))
sc(595.06, 601.90, "Baland tog'li hudud, kuchli shamol va qo'nish uchun qulay joylarning kamligi operatsiyani murakkablashtirgan.",
   [(TVN, 1222.0, None, None), (TVN, 984.0, None, None)])
sc(602.90, 607.30, "Fernando Parrado qutqaruvchilarga halokat joyini aniqlashda yordam bergan.",
   [(PH, 227.0, PHC, "Parrado va Kanessa, 1972"), (TVN, 1230.0, None, None)], lt=("Fernando Parrado", "vertolyotda yo'l ko'rsatdi"))
sc(608.30, 617.30, "22-dekabr kuni samolyot korpusida qolgan kishilarning birinchi guruhi olib chiqilgan. Qolganlar 23-dekabr kuni qutqarilgan.",
   [(X6, 143.0, None, "Qutqaruv, halokat joyi, 1972-yil dekabr"), (PH, 320.0, PHC, "Qutqaruv vertolyotlari, 1972"), (AP, 36.0, None, None)])
sc(618.18, 633.12, "Shu tariqa 1972-yil 13-oktabrda boshlangan favqulodda vaziyat 23-dekabr kuni yakunlangan. Jami 45 kishidan 16 nafari tirik qolgan, 29 kishi halok bo'lgan.",
   [(AP, 69.0, None, None), (AP, 75.0, None, None), (AP, 84.0, None, None)],
   stats=[(45, "bortda"), (16, "tirik qoldi"), (29, "halok bo'ldi")])
sc(633.72, 646.44, "Omon qolganlarning 14 nafari samolyot joylashgan hududdan vertolyot orqali evakuatsiya qilingan. Qolgan ikki kishi — Parrado va Kanessa — yordam izlab tog'lardan mustaqil chiqib ketgan edi.",
   [(RMX, 370.0, None, "Evakuatsiya, 1972"), (DIF_M, 3.0, None, "Parrado va Kanessa, Los Maytenes"), (TVN, 856.0, None, None)])

# ---------------- CHAPTER 6 ----------------
sc(647.78, 649.74, "Voqeadan keyingi hayot.",
   [(RMX, 80.0, None, None)], chapter=("VI", "VOQEADAN KEYINGI HAYOT"))
sc(650.60, 662.44, "Qutqaruvdan so'ng omon qolganlar tibbiy ko'rikdan o'tkazilgan. Ularda uzoq davom etgan ochlik, vazn yo'qotish, sovuq ta'siri va jismoniy zaiflik oqibatlari kuzatilgan.",
   [(TVN, 1137.0, None, "Tibbiy yordam, 1972"), (RMX, 1.0, None, None), (PH, 338.0, PHC, "Kasalxonada, 1972")])
sc(663.16, 675.40, "Ularning hayot uchun kurashi xalqaro ommaviy axborot vositalarida keng yoritilgan. Ayniqsa, oziq-ovqat yetishmasligi sharoitida qabul qilingan qarorlar katta muhokamalarga sabab bo'lgan.",
   [(CAT_A, 57.5, None, "1972-yil gazetalari"), (RMX, 100.0, None, "Matbuot, 1972-yil dekabr"), (CAT_T, 141.5, T80, None)])
sc(676.46, 684.14, "Keyingi yillarda omon qolganlar o'z xotiralarini kitoblar, intervyular va hujjatli filmlar orqali ommaga taqdim etgan.",
   [(CAT_A, 92.5, None, None), (CAN_C, 1.0, None, None)], lt=("Roberto Kanessa", "CGTN intervyusi"))
sc(685.18, 690.06, "1974-yilda Pirs Pol Ridning \"Alive\" kitobi nashr etilgan.",
   [(BOOK, 37.7, None, "Piers Paul Read — \"Alive\" (1974)")], year="1974")
sc(691.26, 696.64, "1993-yilda shu kitob asosida \"Alive\" badiiy filmi ekranlarga chiqqan.",
   [(CAT_A, 99.5, None, "Film afishalari"), (ALIVE93, 10.0, None, "\"Alive\" (1993) treyleri")], year="1993")
sc(697.40, 704.84, "2007-yilda \"Stranded: I've Come from a Plane that Crashed on the Mountains\" hujjatli filmi yaratilgan.",
   [(STRAND, 12.5, None, "\"Stranded\" (2007) treyleri"), (STRAND, 62.0, None, None)], year="2007")
sc(705.08, 724.72, "2023-yilda esa ispaniyalik rejissyor Xuan Antonio Bayona tomonidan \"Society of the Snow\" filmi suratga olingan. Mazkur asarlar voqeaning turli qatlamlarini, jumladan omon qolganlarning ruhiy holati, guruh ichidagi hamkorlik va qutqaruv jarayonini yoritgan.",
   [(VALLE, 51.8, None, "J. A. Bayona, \"La sociedad de la nieve\" premyerasi"), (SOCIETY, 131.0, None, "\"Society of the Snow\" (2023) treyleri"), (SOCIETY, 100.0, None, None), (CAT_A, 101.0, None, None)],
   year="2023")

# ---------------- CHAPTER 7 ----------------
sc(725.20, 736.96, "Tarixiy ahamiyat va xulosa. 1972-yildagi And tog'lari halokati bir nechta jihatdan tarixiy ahamiyatga ega.",
   [(MUSEO, 66.0, None, None), (MUSEO, 70.5, None, None)], chapter=("VII", "TARIXIY AHAMIYAT VA XULOSA"))
sc(737.48, 746.10, "Birinchidan, hodisa murakkab tog'li hududlarda aviatsiya navigatsiyasi va parvoz xavfsizligining naqadar muhimligini ko'rsatgan.",
   [(FH_67, 14.0, None, None), (DIF_S, 30.0, None, None)], point=1)
sc(746.80, 757.26, "Ikkinchidan, favqulodda vaziyatlarda jamoaviy hamkorlik va mavjud resurslardan oqilona foydalanish omon qolish imkoniyatini oshirishi mumkinligini namoyish etgan.",
   [(PH, 50.0, PHC, None), (PH, 133.0, PHC, None)], point=2)
sc(757.80, 770.58, "Uchinchidan, uzoq muddatli ochlik, sovuq va ruhiy bosim inson organizmi hamda qaror qabul qilish jarayoniga qanday ta'sir ko'rsatishini o'rganish uchun muhim tarixiy misol bo'lib qolgan.",
   [(GLAC, 45.0, None, None), (PH, 260.0, PHC, None)], point=3)
sc(771.20, 782.26, "To'rtinchidan, Fernando Parrado va Roberto Kanessaning ekspeditsiyasi favqulodda sharoitda tashabbus ko'rsatish va yordam izlashning hal qiluvchi ahamiyatini namoyon etgan.",
   [(PAR_N, 222.0, None, None), (CAN_C, 254.0, None, None), (CREW, 87.5, None, "Qutqaruvchilar taqdirlanishi, Santyago")], point=4,
   lts=[("Fernando Parrado", "omon qolgan"), ("Roberto Kanessa", "omon qolgan, shifokor"), None])
sc(783.04, 794.02, "And tog'laridagi ushbu hodisa bugungi kunda ham insonning ekstremal sharoitlarda omon qolish imkoniyatlari haqidagi eng mashhur tarixiy voqealardan biri sifatida o'rganiladi.",
   [(MUSEO, 64.8, None, "Museo Andes 1972, Montevideo"), (ANNIV, 64.6, None, None)])
sc(794.76, 813.31, "1972-yil 13-oktabrda 45 kishi bilan boshlangan parvoz 23-dekabr kuni 16 kishining qutqarilishi bilan yakunlangan. Bu hodisa tarixda 72 kun davom etgan omon qolish kurashi va \"And tog'lari mo'jizasi\" nomi bilan saqlanib qolgan.",
   [(VALLE, 103.0 - 40.0, None, None), (PH, 194.0, PHC, None), (AP, 87.0, None, None), (VALLE, 69.0, None, None)],
   end_title=True)
