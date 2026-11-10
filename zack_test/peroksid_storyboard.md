# "Kesilgan joyga peroksid" — kadr rejasi (storyboard)

Ovoz: foydalanuvchi bergan wav (36.72 s). 24 fps, 882 kadr, vertikal 9:16 (1080x1920). Subtitr yo'q.
Matn: "Qo'lingizni kesib olganingizda ustiga peroksid quysangiz, u vishillab oq ko'pik chiqaradi va ko'pchilik
buni mikroblar o'lyapti deb o'ylaydi. Lekin aslida siz shu lahzada o'z teringizning tirik hujayralarini yoqib
yuborayotgan bo'lasiz. Peroksid juda kuchli kimyoviy oksidlovchi bo'lib, u bakteriya bilan sog'lom to'qimaning
farqiga bormaydi. Siz ko'rayotgan oq ko'pik — bu jarohatni bitirishi kerak bo'lgan yangi nozik hujayralarning va
qon tanachalarining parchalanib, erib ketishidir. Natijada peroksid quyilgan yara ikki barobar sekinroq bitadi va
o'rnida xunuk chandiq qolish ehtimoli keskin oshadi. Shifokorlar allaqachon bu usuldan voz kechgan."

Qahramonlar: **Megan** (Mixamo, oshxonada), **Josh** (shifokor: oq xalat rangi + stetoskop kod bilan).
Joy: oshxona (Poly Haven: `marble_01` stol usti, `kitchen_wood` shkaflar, `long_white_tiles` devor, `fish_knife`,
`lemon`, `medical_box`, `potted_plant_01`, HDRI `comfy_cafe`), shifoxona (HDRI `hospital_room`).
Mikro olam: protsedur (teri hujayralari, bakteriyalar, H₂O₂ molekulalari, eritrotsitlar, ko'pik pufakchalari).
Qo'llar IK bilan pichoq/shisha/stolga bog'lanadi. Sahna: `zack_test/scene_peroksid.py`.

| # | Vaqt (s) | Kadrlar | Matn | Kadr va kamera | Harakat |
|---|----------|---------|------|----------------|---------|
| 1 | 0.0–1.75 | 1–42 | "Qo'lingizni kesib olganingizda" | **HOOK:** taxta sathidan makro, 35 mm f/2: pichoq limonni kesayotib sirpanadi va barmoqni kesadi, qon tomchisi; kamera keskin silkinadi | Breathing_Idle + IK (pichoq) |
| 2 | 1.75–3.7 | 43–89 | "ustiga peroksid quysangiz, u vishillab" | Yondan 50 mm: jigarrang shisha egiladi, oqim barmoqqa tushadi, "vishillab"da birinchi pufakchalar | IK (shisha) |
| 3 | 3.7–5.5 | 90–132 | "oq ko'pik chiqaradi va ko'pchilik" | Ekstremal makro, 85 mm f/2.8: oq ko'pik shishib chiqadi, kamera yoy bo'ylab aylanadi | — |
| 4 | 5.5–7.2 | 133–172 | "buni mikroblar o'lyapti deb o'ylaydi" | Pastdan keng, 22 mm, DOF: Megan barmog'iga qarab mamnun bosh irg'aydi, orqada oshxona xira | Head_Nod_Yes + IK (qo'l ko'tarilgan) |
| 5 | 7.2–8.5 | 173–204 | "Lekin aslida siz" | Yaraga sho'ng'ish: kamera ko'pik ichiga tez kiradi (dolly + lens 50→120 mm) | — |
| 6 | 8.5–12.6 | 205–302 | "shu lahzada o'z teringizning tirik hujayralarini yoqib yuborayotgan" | **Mikro:** pushti teri hujayralari ustidan uchish; "yoqib"da oksidlanish chaqnaydi, hujayralar qorayib, burishib, pufakka aylanadi | — |
| 7 | 12.6–15.3 | 303–367 | "Peroksid juda kuchli kimyoviy oksidlovchi bo'lib" | Mikro: H₂O₂ molekulalari (2 qizil O, 2 oq H) kameraga uchib keladi, past burchak, 24 mm | — |
| 8 | 15.3–18.1 | 368–434 | "u bakteriya bilan sog'lom to'qimaning farqiga bormaydi" | Mikro, aylanma kamera: yashil tayoqcha bakteriya va pushti hujayra yonma-yon; molekulalar ikkalasini ham yoradi | — |
| 9 | 18.1–20.1 | 435–482 | "Siz ko'rayotgan oq ko'pik" | Real olam, makro: barmoqdagi ko'pik, sekin orbit, 70 mm f/2 | — |
| 10 | 20.1–23.3 | 483–560 | "bu jarohatni bitirishi kerak bo'lgan yangi nozik hujayralarning" | Mikro: yara chetlari orasida yangi nozik hujayralar ko'prik quradi → eriydi, pufakchalar | — |
| 11 | 23.3–26.0 | 561–624 | "va qon tanachalarining parchalanib, erib ketishidir" | Mikro: qizil eritrotsitlar aylanib suzadi, "parchalanib"da yorilib eriydi | — |
| 12 | 26.0–30.0 | 625–721 | "Natijada peroksid quyilgan yara ikki barobar sekinroq bitadi" | Tepadan: ikki qo'l stolda, ikkalasida yara; vaqt tez o'tadi (soya suriladi). O'ng (suv) yara tez bitadi, chap (peroksid) qizilligicha qoladi | Breathing_Idle + IK (ikki qo'l stolda) |
| 13 | 30.0–33.6 | 722–807 | "va o'rnida xunuk chandiq qolish ehtimoli keskin oshadi" | Barmoqqa makro push-in: yara bo'rtgan oqish chandiqqa aylanadi; "keskin"da tez zoom | — |
| 14 | 33.6–36.72 | 808–882 | "Shifokorlar allaqachon bu usuldan voz kechgan." | Shifoxona, pastdan keng 20 mm: shifokor bosh chayqaydi va qo'li bilan "yo'q" ishorasini qiladi; oldinda peroksid shishasi xira | Shaking_Head_No → Dismissing_Gesture_2 |

Uslub: har 1.5–4 soniyada kesma, kamera doim harakatda (dolly/orbit + qo'l silkinishi), DOF, motion blur,
Cycles, AgX Punchy. Real olam iliq oshxona yorug'ida, mikro olam to'q qizil-pushti "tana ichi" fonida.
