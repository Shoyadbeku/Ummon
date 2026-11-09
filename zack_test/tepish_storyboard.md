# "Uyqudagi tepish" (gipnik silkinish) — kadr rejasi (storyboard)

Ovoz: foydalanuvchi bergan wav (43.84 s). 24 fps, 1053 kadr, vertikal 9:16 (1080x1920).
Qahramon: **Megan** (Mixamo). Joy: tungi yotoqxona (Poly Haven laminat pol, suvoq devor, tumbochka, budilnik,
BlenderKit karavot va stol chirog'i), oyna ortida tungi osmon (Poly Haven `rogland_clear_night`).
Tush sahnalari: tungi osmonda qulash; kunduzi daraxtdan (Poly Haven `jacaranda_tree`) yiqilish.
Rentgen: BlenderKit bosh suyagi (49c13194), miya (1d697a0b), yurak (652dce3c). Sahna: `zack_test/scene_tepish.py`.

| # | Vaqt (s) | Kadrlar | Matn | Kadr va kamera | Harakat (Mixamo) |
|---|----------|---------|------|----------------|------------------|
| 1 | 0.0–2.9 | 1–70 | "Ko'zingiz endi uyquga ketayotgan paytda" | **HOOK:** tepadan pastga yuzga yaqin plan, 50 mm f/2, tez push-in; tungi chiroqning iliq nuri | Laying_Sleeping |
| 2 | 2.9–5.45 | 71–131 | "to'satdan balandlikdan qulab tushayotgandek bo'lib" | **Tush:** karavot yo'qoladi, Megan tungi osmonda chalqancha qulaydi; pastdan 16 mm, kamera aylanadi | Falling_2 |
| 3 | 5.45–8.6 | 132–206 | "butun tanangiz qattiq silkinib uyg'onib ketganmisiz?" | Karavot oyog'i tomondan past burchak, 18 mm: butun tana keskin silkinadi, kamera tebranadi | Laying_Seizure (bo'lak) → Laying_Idle |
| 4 | 8.6–11.55 | 207–277 | "Bu tasodif emas, balki miyangiz" | Keng plan: oy nuri tushgan xona, sekin dolly; "miyangiz" so'zida **rentgen o'tishi** | Laying_Sleeping |
| 5 | 11.55–15.0 | 278–360 | "sizni o'lib qoldi deb o'ylaganidan ... mudofaa reaksiyasidir" | Rentgen, profil: bosh suyagi va miya, bodomsimon tana qizil chaqnaydi, kamera yoy bo'ylab | Laying_Sleeping |
| 6 | 15.0–17.8 | 361–427 | "Siz juda charchaganingizda, yurak urishingiz" | Rentgen, ko'krak tepasidan: yurak urishi sekinlashadi (pulsatsiya) | Laying_3 |
| 7 | 17.8–21.3 | 428–511 | "va nafas olishingiz odatdagidan ancha tez sekinlashadi" | Oddiy ko'rinish, yondan past burchak: ko'krak sekin ko'tarilib tushadi, oy nuri | Laying_3 |
| 8 | 21.3–23.6 | 512–566 | "Mushaklaringiz esa bir zumda bo'shashadi." | Pol sathidan: qo'l karavot chetidan shalvirab tushadi, 24 mm, DOF | Laying_Idle + qo'lni kod bilan tushirish |
| 9 | 23.6–28.1 | 567–674 | "Miyangizning qadimgi omon qolish markazi bu keskin o'zgarishni uyqu emas" | Rentgen: miya atrofida aylanma kamera, bodomsimon tana qizil pulsatsiya | Laying_Sleeping |
| 10 | 28.1–32.7 | 675–785 | "balki o'limga ketyapti yoki daraxtdan yiqilyapti deb noto'g'ri tushunadi" | **Tush:** Megan daraxt shoxiga osilgan, "daraxtdan" so'zida qo'li sirg'alib qulaydi; pastdan 16 mm | Hanging_Idle_2 → Falling_2 |
| 11 | 32.7–36.0 | 786–864 | "Sizni qutqarib qolish uchun miya yashin tezligida" | Rentgen, tepadan butun gavda: amigdala chaqnaydi, "yashin" so'zida birinchi qizil yashin | Laying_Sleeping |
| 12 | 36.0–40.0 | 865–960 | "asab tizimiga kuchli elektr razryadi va adrenalin oqimini otadi" | Rentgen, oyoq tomondan past burchak: yashinlar umurtqa bo'ylab oyoqlarga, sariq adrenalin oqimi | Laying_Sleeping |
| 13 | 40.0–42.6 | 961–1023 | "Natijada oyog'ingiz o'z-o'zidan tepib," | Oddiy ko'rinish, oyoqlarga yaqin plan: "tepib" so'zida oyoq keskin tepadi, ko'rpa sakraydi | Laying_Idle + tepish (kod) |
| 14 | 42.6–43.84 | 1024–1053 | "cho'chib ko'zingiz ochiladi." | Yuzga makro plan: bosh keskin ko'tariladi, ko'zlar ochiladi, kamera silkinadi (yakun) | Laying_Seizure (boshi) |

Uslub: har 2–4 soniyada kesma, kamera doim harakatda (dolly/orbit + qo'l silkinishi), DOF, motion blur,
Cycles, AgX Punchy. Subtitr yo'q. Tush kadrlari (2, 10) iliq-ko'k "tush" rangida, rentgen — to'q ko'k fonda.
