# Muzqaymoq "miyani muzlatadi" — Zack D. Films uslubida (40 s, 9:16, 24 fps, 960 kadr)

Ovoz: foydalanuvchi yuklagan mp3 (fayl nomi "ElevenLabs ... Jeremy", matni muzqaymoqdan bosh og'rishi haqida).
Whisper (`medium`, `language="uz"`) bilan matnga o'girilib, kadrlar so'z vaqtlariga bog'langan.

Matn: «Muzqaymoqni tez yesangiz, peshonangizda keskin og'riq paydo bo'ladi. Qizig'i shundaki, miyangiz umuman
muzlamaydi. Sovuq narsa tanglayingizga tekkanda, u yerdagi qon tomirlar birdan torayadi. Bir necha soniyadan keyin
tana issiqlikni qaytarish uchun ularni keskin kengaytirib yuboradi. Bu tez o'zgarishni yuzdagi katta asab sezib qoladi
va xavf signalini miyaga yuboradi. Lekin miya signal qayerdan kelganini adashtirib, og'riqni peshonada his qiladi.
Shuning uchun bunday paytda tilingizni tanglayingizga bosing. Uning issiqligi tomirlarni tinchlantiradi va og'riq
tezroq o'tib ketadi.»

Zack D. montaji: 16 ta kadr, har 1.4–3.5 s da kesish, kamera hech qachon bir joyda turmaydi (push-in, crash zoom,
aylanma, silkinish), rentgen va "og'iz ichi" kesimi, past burchakdan keng ob'ektiv, DOF, motion blur, AgX Punchy.

| # | Kadrlar | Vaqt | Ovoz | Kadr / kamera | Sahna |
|---|---------|------|------|---------------|-------|
| 1 | 1–46 | 0.0–1.9 | "Muzqaymoqni tez yesangiz" | **ILGAK**: pastdan, muzqaymoqqa juda yaqin, qiz katta tishlaydi; tez push-in | Ko'cha, Megan `Drinking` |
| 2 | 47–81 | 1.9–3.4 | "peshonangizda keskin" | Yuzga crash zoom, qiz boshini changallaydi, silkinish | `Agony` |
| 3 | 82–124 | 3.4–5.2 | "og'riq paydo bo'ladi" | **Rentgen**: shaffof bosh, peshonada qizil og'riq chaqnaydi | Megan (rentgen nusxa) |
| 4 | 125–208 | 5.2–8.7 | "Qizig'i shundaki, miyangiz umuman muzlamaydi" | Miya qorong'i fonda aylanadi, ustini muz qoplaydi -> muz sinib, parchalanib ketadi | Miya (procedural) |
| 5 | 209–265 | 8.7–11.1 | "Sovuq narsa tanglayingizga tekkanda" | **Og'iz ichi** (makro): muzqaymoq tanglayga yopishadi, ko'k qirov yoyiladi | Tanglay (procedural) |
| 6 | 266–334 | 11.1–13.9 | "u yerdagi qon tomirlar birdan torayadi" | Tanglay shaffoflashadi: qizil tomirlar ingichkalab ko'karadi | Tanglay rentgen |
| 7 | 335–412 | 13.9–17.2 | "Bir necha soniyadan keyin tana issiqlikni qaytarish uchun" | Tomirlar bo'ylab issiq (to'q sariq) qon to'lqini yuguradi, kamera ergashadi | Tanglay rentgen |
| 8 | 413–478 | 17.2–19.9 | "ularni keskin kengaytirib yuboradi" | Tomirlar keskin shishadi, qizarib urib turadi; silkinish | Tanglay rentgen |
| 9 | 479–559 | 19.9–23.3 | "Bu tez o'zgarishni yuzdagi katta asab sezib qoladi" | Rentgen yuz: uch shoxli asab (sariq) tanglaydan yonadi | Megan (rentgen) |
| 10 | 560–621 | 23.3–25.9 | "va xavf signalini miyaga yuboradi" | Signal asab bo'ylab miyaga yuguradi, miya chaqnaydi | Megan (rentgen) |
| 11 | 622–697 | 25.9–29.0 | "Lekin miya signal qayerdan kelganini adashtirib" | Miya atrofida aylanma kamera: signal shoxlarda adashib yuradi | Miya |
| 12 | 698–754 | 29.0–31.4 | "og'riqni peshonada his qiladi" | Pastdan keng plan: qiz peshonasini changallab egiladi, qizil chaqnash | Ko'cha, `Agony` |
| 13 | 755–788 | 31.4–32.8 | "Shuning uchun bunday paytda" | Yuzga yaqin plan (DOF), sekin push-in | Ko'cha |
| 14 | 789–843 | 32.8–35.1 | "tilingizni tanglayingizga bosing" | Og'iz ichi: til ko'tarilib tanglayga bosiladi | Tanglay |
| 15 | 844–908 | 35.1–37.8 | "Uning issiqligi tomirlarni tinchlantiradi" | Rentgen: tildan issiq nur tarqaladi, tomirlar tinchlanadi, qirov eriydi | Tanglay rentgen |
| 16 | 909–960 | 37.8–40.0 | "va og'riq tezroq o'tib ketadi." | Qiz yengil tortadi, kamera orqaga va yuqoriga chekinadi, qorong'ilik | Ko'cha, `Focus` |

Manbalar: Mixamo (HF `Linzhan/Mixamo-Animations-Characters`): Megan; harakatlar `Drinking`, `Agony`, `Focus`, `Breathing_Idle`.
Poly Haven (CC0): HDRI `kloofendal_48d_partly_cloudy_puresky`, teksturalar `concrete_pavement`, `asphalt_02`, modellar `potted_plant_01`.
BlenderKit (bepul): Audi e-tron GT (c3c28d91) orqa fonda.
Muzqaymoq, tanglay, til, tishlar, tomirlar, asab, miya, muz parchalari: Python kodi bilan (procedural, `burish/parts.py` dan).
Subtitr yo'q. Render 540x960 (50%), ffmpeg bilan 1080x1920 ga kattalashtiriladi.
