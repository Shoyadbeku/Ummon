# Muzdek gazli ichimlik — Zack D. Films uslubida (43.6 s, 9:16, 24 fps, 1048 kadr)

Ovoz: foydalanuvchi yuklagan wav. Fayl nomi "Koinotdagi ovoz: Quyosh aslida qancha jarang" bo'lsa ham,
Whisper matni **shirin gazli ichimlik ichgandan keyin tanada nima bo'lishi** haqida. Kadrlar so'z vaqtlariga bog'langan.

Zack D. montaji: 24 ta kesish (har 1.3–2.7 s), hech bir kadr bir joyda turmaydi (doim dolly / orbit / crash zoom),
ilgak (hook) bilan boshlanadi: muzdek banka makrosi. Rentgen kesimlari, makro ko'z, qon tomiri ichida uchish.
Qahramon: Megan (Mixamo). Xona: Poly Haven (Sofa_01, modern_coffee_table_01, potted_plant_01, fancy_picture_frame_01,
laminate_floor_02, painted_plaster_wall, kloofendal HDRI). Cycles, AgX Punchy, motion blur, DOF.

| # | Kadrlar | Ovoz | Kadr / kamera | Harakat |
|---|---------|------|---------------|---------|
| 1 | 1–24 | "Muzdek," | **ILGAK. Makro**: stol ustida terlagan qizil banka, tomchilar, past burchakdan tez yaqinlashish, orqa fon xira | — |
| 2 | 25–52 | "shakarli, gazli" | **Past burchak, 16 mm keng**: Megan bankani og'ziga ko'taradi | `Drinking` |
| 3 | 53–86 | "ichimlikni bir ko'tarishda ichib" | **Yuzga yaqin, 55 mm f/2**, orqa fon xira, sekin dolly | `Drinking` |
| 4 | 87–118 | "yuborganingizdan keyin." | **Rentgen**: shaffof ko'k tana, ichimlik qizilo'ngachdan oshqozonga oqadi | `Drinking` |
| 5 | 119–168 | "Dastlabki 10 daqiqada tanangizga" | Rentgen torso, oshqozon jigarrang ichimlik bilan to'ladi, orbit | `Breathing_Idle` |
| 6 | 169–220 | "10 qoshiqqa yaqin shakar zarbasi tushadi." | **Studiya makro**: kola stakaniga 10 ta qand birin-ketin tushadi, sachraydi, past burchak | — |
| 7 | 221–268 | "Odatda bu shakar miqdari oshqozonni" | Rentgen: oshqozon qizil yonib-o'chadi (xavf), tez yaqinlashish | — |
| 8 | 269–318 | "bezovta qilib qusturib yuborishi kerak." | O'rta plan, past burchak: Megan qornini changallab egiladi, kamera silkinadi | `Big_Stomach_Hit` (sekin) |
| 9 | 319–374 | "Lekin ichimlik tarkibidagi" | **Ichimlik ichida**: pufakchalar ko'tariladi, qandlar cho'kadi, kamera suzadi | — |
| 10 | 375–416 | "fosfor kislotasi bu o'ta shirin ta'mni" | Yashil kislota zarralari qandlarni o'rab, eritib yuboradi | — |
| 11 | 417–470 | "vaqtincha yutib, oshqozonning" | Rentgen oshqozon: qizildan tinch ko'kka o'tadi, yashil zarralar | `Breathing_Idle` |
| 12 | 471–518 | "himoya refleksini aldab qo'yadi." | Yuzga yaqin: Megan o'zini yaxshi his qiladi, sekin itarish | `Breathing_Idle` |
| 13 | 519–584 | "40 daqiqaga kelib, qondagi qand keskin ko'tariladi." | **Qon tomiri ichida uchish**: eritrotsitlar, oq qand kristallari ko'payadi | — |
| 14 | 585–620 | "Ko'z qorachig'i" | **Makro ko'z**, sekin yaqinlashish | — |
| 15 | 621–650 | "kengayadi" | Makro ko'z: qorachiq kengayadi, crash zoom | — |
| 16 | 651–682 | "va qon bosimi oshadi." | Tomir devori urib kengayadi, kamera silkinadi | — |
| 17 | 683–740 | "60-daqiqada esa oshqozon osti bezi vahimaga tushib," | Rentgen torso: oshqozon osti bezi qizil miltillaydi, tez itarish | `Breathing_Idle` |
| 18 | 741–780 | "ortiqcha shakarni darhol" | **Makro bez**: qizil signal nuri, orbit | — |
| 19 | 781–818 | "yo'qotish uchun insulinni" | Bezdan oltin rang insulin zarralari otilib chiqadi | — |
| 20 | 819–862 | "ommaviy ravishda qonga otadi." | Qon tomiri: oltin insulin to'dasi qand kristallarini yo'q qiladi | — |
| 21 | 863–918 | "Keyin esa qand birdan tushib, o'zingizni" | Keng, past burchak: Megan boshi aylanib chayqaladi, sovuq rang | `Dizzy_Idle` |
| 22 | 919–966 | "holsiz, asabiy" | Yuzga yaqin: asabiy bosh chayqash | `Annoyed_Head_Shake` |
| 23 | 967–1010 | "va yana nimadir shirinlik yegingiz keladigan" | Oldinda stol ustidagi yangi banka (fokus), orqada Megan unga qo'l cho'zadi | `Picking_Up_Object` |
| 24 | 1011–1048 | "holatga tushib qolasiz." | Banka makrosiga crash zoom → keskin qorong'ilik | — |

Tovush: `sfx.py` (sintez): banka ochilishi (pss), ho'plash, qand tushishi, pufakchalar, yurak urishi,
signal (bez), kesishlarda "vush", oxirida zarba. Effektlar ovoz ostida avtomatik pasayadi (sidechain).
Subtitr yo'q. Render 540x960 (50%), ffmpeg bilan 1080x1920 ga kattalashtiriladi.
