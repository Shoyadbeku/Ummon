# Ko'cha shimida karavotga yotish (Zack D. Films uslubida, 40.4 s, 970 kadr, 24 fps, 9:16)

Ovoz: foydalanuvchi yuklagan wav (fayl nomi "koinotdagi ovoz, quyosh aslida qancha jarang... studio_33", mazmuni esa
**ko'cha kiyimida karavotga yotish** haqida). Whisper `large-v3`, `language="uz"`, so'z vaqtlari `words.json` da. Matn qo'lda tiklandi:

| vaqt (s) | matn |
|---|---|
| 0.00–8.70 | Ishdan yoki o'qishdan charchab kelib, ko'chadagi shimingizni almashtirmasdan to'g'ri yotog'ingiz ustiga cho'zilib yotish ko'rpangizni jamoat transporti o'rindig'iga aylantiradi. |
| 8.86–22.82 | Kun davomida avtobus, taksi, kafe yoki kasalxona o'rindiqlariga o'tirganingizda, mato tolalari o'ziga oldingi odamlardan qolgan millionlab teri qipiqlarini, ichak tayoqchalarini va hatta to'shak kanalarining ko'zga ko'rinmas tuxumlarini yopishtirib oladi. |
| 22.94–28.74 | Bundan tashqari, o'z tanangizdan kun bo'yi ajralgan ter va bakteriyalar shim matosiga chuqur botgan bo'ladi. |
| 28.74–35.44 | Siz shu kiyimda choyshab ustiga o'tirgan zahotingiz, bu mikroskopik parazitlar issiq va yumshoq yostiq-ko'rpangizga ko'chib o'tadi. |
| 35.60–40.40 | Kechasi esa, siz ularni o'z yuzingiz va tanangiz bilan isitib uxlaysiz. |

Qahramon: **Brian** (Mixamo, erkak, jinsi shim) — "shimingiz" so'zi uchun shim aniq ko'rinadigan erkak qahramon.
Fon yo'lovchilari: **Kate**, **David**, **Remy** (avtobus / kasalxona).

Dramaturgiya: **Hook** (charchagan odam ko'cha shimida karavotga yiqiladi) → **Conflict** (o'rindiqlar ko'rpaga "aylanadi")
→ **Escalation** (mikro dunyo: jinsi tolalaridagi qipiq, E. coli, kana tuxumlari, ter) → **Payoff** (parazitlar choyshabga
o'tadi, tunda yuz yonida — issiqlik kamerasi va mikrodan butun xonaga orqaga chekinish).

Olti dunyo: **kvartira** (kechqurun, yotoqxona), **avtobus salon** (protsedural, mashhur naqshli o'rindiq matosi),
**taksi / kafe / kasalxona** (tezkor 0.6 s lik kadrlar), **mikro jinsi** (1000x, ko'k twill to'qima), **mikro choyshab**
(oq paxta iplari), **tungi yotoqxona + issiqlik kamerasi**.

## Kadrlar (5 akt, 19 kesim)

| # | kadrlar | vaqt (s) | ovoz | vizual voqea | kamera | animatsiya | yorug'lik | o'tish |
|---|---|---|---|---|---|---|---|---|
| **AKT 1 — HOOK** |
| 1 | 1–46 | 0.0–1.9 | "Ishdan yoki o'qishdan charchab kelib" | Eshik ochiladi, Brian sudralib kiradi, sumkani polga tashlaydi | **past burchak 18 mm**, poldan push-in + yengil silkinish | `Sad_Walk` (inplace, root suriladi) | kechki oltin quyosh derazadan, iliq lampa | qattiq kesish, sumka "gup" |
| 2 | 47–91 | 1.9–3.8 | "ko'chadagi shimingizni almashtirmasdan" | Jinsi shim, tizzadagi kir dog'lar, krossovka | shimga **crash zoom** 35→85 mm, DOF | `Sad_Walk` → to'xtash | iliq + qizg'ish kontur | whoosh |
| 3 | 92–142 | 3.8–5.9 | "to'g'ri yotog'ingiz ustiga cho'zilib yotish" | Brian chalqancha ko'rpa ustiga yiqiladi, ko'rpa "puf" | **WIDE 28 mm**, karavot oyog'idan dolly + tepaga ko'tarilish | `Lying_Down` (tezlashtirilgan) + `Laying_3` | xona to'liq: deraza nuri + lampa | zarba "puf" |
| 4 | 143–212 | 5.9–8.8 | "ko'rpangizni jamoat transporti o'rindig'iga aylantiradi" | **MORF**: ko'rpa matosi naqshi avtobus o'rindig'i naqshiga aylanadi; kamera chekinsa — Brian avtobus o'rindig'ida yotibdi | tepadan, aylanma + orqaga chekinish | `Laying_3` | iliq xona → sovuq lyuminestsent | material "morph" qiymati, chaqnash |
| **AKT 2 — CONFLICT (o'rindiqlar)** |
| 5 | 213–254 | 8.9–10.6 | "Kun davomida avtobus" | Avtobus salonida Brian o'tiradi, yo'lovchilar chayqaladi | yo'lak bo'ylab tracking 24 mm | `Stand_To_Sit` → `Jostled_Passenger`; fon: `Sitting_Idle_4/5` | kunduzgi deraza, oqish lampa | tezkor kesish |
| 6 | 255–266 | 10.6–11.1 | "taksi" | Taksi orqa o'rindig'i, shim teriga botadi | o'rindiq darajasida, tezkor push-in | `Stand_To_Sit` | sariq "TAKSI" belgisi aksi | whip-pan |
| 7 | 267–283 | 11.1–11.8 | "kafe yoki" | Kafe stuli (yumshoq) | past burchak | `Stand_To_Sit` | iliq kafe | whip-pan |
| 8 | 284–324 | 11.8–13.5 | "kasalxona o'rindiqlariga o'tirganingizda" | Kasalxona kutish zali, plastik/mato stullar qatori, yonida yo'talayotgan bemor | **past burchak 18 mm**, yonlama siljish | `Stand_To_Sit`; bemor `Sitting_Idle_3` | sovuq yashil-oq lyuminestsent | qisqa "zum" |
| **AKT 3 — ESCALATION (mikro jinsi)** |
| 9 | 325–358 | 13.5–14.9 | "mato tolalari o'ziga" | Shim matosiga sho'ng'ish: 1x → 1000x | **crash zoom** shimga, keyin mikro | — | → mikro: qorong'i fon, kontur chiroq | oq chaqnash |
| 10 | 359–430 | 14.9–17.9 | "oldingi odamlardan qolgan millionlab teri qipiqlarini" | Ko'k twill iplari orasiga yupqa teri qipiqlari qor kabi yog'iladi va yopishadi | mikro: tepadan pastga + aylanma, DOF | qipiqlar fizik tushishi (kalitlar) | yonlama sovuq kontur | — |
| 11 | 431–460 | 18.0–19.2 | "ichak tayoqchalarini" | Tayoqchasimon bakteriyalar (E. coli, xivchinli) iplar ustida | mikro yaqin plan, yonlama | xivchinlar to'lqinlanadi | yashil-sariq kontur | tezkor kesish |
| 12 | 461–550 | 19.2–22.9 | "va hatta to'shak kanalarining ko'zga ko'rinmas tuxumlarini yopishtirib oladi" | Ip orasida marvarid-oq tuxumlar to'dasi; biridan qopqoq ochiladi — kichik kana (klop lichinkasi) chiqadi | **past burchakdan** tuxumlarga push-in, chiqqanda silkinish | tuxum qopqog'i, oyoqlar `ph` drayveri | iliq kontur + yaltiroq | qizil chaqnash |
| **AKT 4 — ESCALATION 2 (ter)** |
| 13 | 551–622 | 22.9–25.9 | "Bundan tashqari, o'z tanangizdan kun bo'yi ajralgan" | Timelapse: avtobusda Brian, quyosh tez o'tadi, peshona/bel terlaydi; **issiqlik kamerasi** ga o'tadi | yonlama dolly | `Sitting_Idle_5` | soya/quyosh tez aylanadi | — |
| 14 | 623–646 | 25.9–26.9 | "ter va bakteriyalar" | Mikro: ter tomchisi iplarga tushadi, ichida bakteriyalar | mikro crash zoom | tomchi tushishi | — | — |
| 15 | 647–690 | 26.9–28.7 | "shim matosiga chuqur botgan bo'ladi" | **Kesim**: jinsi mato ko'ndalang kesimi, bakteriyalar va ter ip ichiga chuqur singadi | kesimga push-in | bakteriyalar pastga siljiydi | — | — |
| **AKT 5 — PAYOFF** |
| 16 | 691–757 | 28.7–31.5 | "Siz shu kiyimda choyshab ustiga o'tirgan zahotingiz" | Brian karavot chetiga o'tiradi — shim choyshabga botadi | **past burchak**, choyshab darajasida, yonlama | `Stand_To_Sit` | kechki lampa | zarba |
| 17 | 758–850 | 31.6–35.4 | "bu mikroskopik parazitlar issiq va yumshoq yostiq-ko'rpangizga ko'chib o'tadi" | Mikro: ko'k jinsi iplari oq paxta iplariga tegadi; kana, bakteriya, tuxumlar "ko'prik" orqali oqga o'tadi | mikro: yonlama ergashish, oxirida orqaga chekinish | kanalar yuradi | ko'k/oq kontrast | — |
| 18 | 851–936 | 35.6–39.0 | "Kechasi esa, siz ularni o'z yuzingiz va tanangiz bilan" | Tungi yotoqxona: Brian uxlaydi; **issiqlik kamerasi**: tana va yostiq qizil-sariq | tepadan sekin aylanma → yuzga push-in | `Laying_Sleeping` / `Sleeping_Idle_2` | oy nuri ko'k + issiqlik palitrasi | — |
| 19 | 937–970 | 39.0–40.4 | "isitib uxlaysiz" | **REVEAL**: yonoq yonidagi yostiq matosidan kanalar va bakteriyalar to'dasi — kamera mikrodan butun xonaga tez orqaga chekinadi | orbit + tez pull-out | — | tungi | so'nggi zarba, qorong'ilashish |

Majburiy kadr turlari: Hook — 1 (past burchak push-in); Wide — 3, 5; Emotional close-up — 2, 18 (85 mm, DOF);
Low-angle action — 1, 8, 12, 16; Payoff/reveal — 17, 19.

## Texnik reja

- Kod: `zack_test/kiyim/kiyim.py` (sahna + kadrlar), `micro.py`/`mite.py` (yostiq/kana sahnalaridan qayta ishlatiladi: to'qilgan iplar,
  bakteriyalar, kana), yangi: jinsi twill, teri qipiqlari, E. coli, klop tuxumlari, avtobus salon, kasalxona stullari.
- Assetlar: `zack_test/tools/get_kiyim.sh` (Mixamo HF, Poly Haven CC0, BlenderKit bepul).
- Render: Cycles CPU (GPU yo'q, 4 yadro), denoise, motion blur, AgX Punchy, `use_overwrite=False` + `use_placeholder=True` (davom ettirish).
- Montaj: `montaj.sh` (ffmpeg, H.264, yuv420p, 24 fps, faststart), tovush effektlari sintez qilinadi (`sfx.py`) + foydalanuvchi ovozi.
