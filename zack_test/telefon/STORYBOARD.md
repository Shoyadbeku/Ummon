# Bir ko'z bilan telefon — Zack D. Films uslubida (41.4 s, 9:16, 24 fps, 994 kadr)

Ovoz: foydalanuvchi yuklagan wav (`koinotdagi_ovoz_quyosh_aslida_qancha_jarang_studio_31.wav`, 41.4 s, 48 kHz mono).
Fayl nomi koinot/quyosh haqida, lekin Whisper (`large-v3`, `language="uz"`, so'z vaqtlari) bilan o'girilganda matn
**qorong'uda bir ko'z bilan telefonga qarash -> vaqtincha "smartfon ko'rligi"** haqida chiqdi (CLAUDE.md ogohlantirgandek).
Sahna ovoz matniga qarab quriladi, har kesish so'z vaqtiga bog'langan (`words.json`). Subtitr yo'q.

Matn: «Kechasi chiroqni o'chirib, qorong'uda yostiq ustida, bir ko'zingiz yostiqqa botgan holda, faqat bitta ko'z bilan
telefonga tikilib yotish ko'rish qobiliyatini vaqtincha o'chirib qo'yadi. Zimziyo xonada ko'z qorachig'i ko'proq yorug'lik
yig'ish uchun maksimal darajada kengaytiriladi. Bu holatda telefon ekranidan chiqayotgan o'tkir ko'k nur to'g'ridan-to'g'ri
kengaygan qorachiq orqali ko'z tubidagi fotoretseptorlarga xuddi lazer nuridek zarba beradi. Bir ko'zingiz yostiqqa yopilib
qorong'ulikka moslashgan, ikkinchisi esa yorug'likdan kuygan paytda miyada signal chalkashuvi yuz beradi. Telefonni
o'chirgan zahotingiz, ekranni ko'rgan ko'zingiz 15 daqiqagacha hech narsani ko'rmay, butunlay qorong'u bo'lib qoladi.»

Tuzilma (Hook -> Conflict -> Escalation -> Payoff) 5 ta majburiy kadr turini 15 ta tez kesishga bo'ladi
(Zack D. ritmi: har 1.5–4 s da kesish, kamera hech qachon qotib turmaydi).
Dunyolar: **yotoqxona** (tun, Megan yonboshlab yotgan), **rentgen bosh** (shaffof Megan, bosh suyagi, ko'z olmalari,
ko'rish nervlari, xiazma, miya), **makro ko'z** (`yelim/eye.py`), **ko'z kesimi** (10x: shox parda, qorachiq, gavhar,
to'r parda), **mikro to'r parda** (tayoqcha/kolbochkalar "o'rmoni"), **POV** (ikki ko'zning ko'rinishi).

| # | Kadrlar | Timecode | Ovoz | Visual Action | Camera | Animation | Lighting | Transition |
|---|---------|----------|------|---------------|--------|-----------|----------|------------|
| 1 | 1–36 | 0.00–1.50 | "Kechasi chiroqni o'chirib" | **HOOK**: tungi lampa "chirt" o'chadi, xona qorong'ilashadi, faqat telefon ekrani yonib qoladi | Tumbochka sathidan 20 mm, lampa yonidan Megan yuziga tez push-in | `Laying_Sleeping` + o'ng qo'l IK (telefon) | Iliq lampa -> 3 kadrda o'chadi; ekran ko'k emissiyasi; derazadan oy (sovuq ko'k) | Qattiq kesish, "whoosh" |
| 2 | 37–74 | 1.50–3.10 | "qorong'uda yostiq ustida" | **WIDE ESTABLISHING**: qorong'u yotoqxona, karavotda yonboshlagan Megan, yuzini telefon ko'k nuri yoritadi | 24 mm, tepa-yondan sekin dolly + biroz pastga tushish | `Laying_Sleeping`, bosh barmoq ekranni suradi | Oy nuri + ekran ko'k nuri, hajmli yengil tuman | Kesish (harakat davomida) |
| 3 | 75–126 | 3.10–5.28 | "bir ko'zingiz yostiqqa botgan holda" | **EMOTIONAL CLOSE-UP**: yuzning yarmi yostiqqa botgan, pastki ko'z ko'rinmaydi, yuqori ko'z ochiq | 85 mm, f/2, yostiq sathida, yuz bo'ylab sekin yonlama siljish, fon xira | Bosh yostiqqa botgan (yostiq "dip" shape key) | Ekran nuri yuzning bir tomonida, qolgani qorong'u (chiaroscuro) | Kesish |
| 4 | 127–191 | 5.28–7.98 | "faqat bitta ko'z bilan telefonga tikilib yotish" | Telefon ortidan (OTS): ochiq ko'zda ekran aksi; kamera ochiq ko'zga yaqinlashadi | 50 mm, telefon yelkasi ortidan push-in ko'zga, DOF | Bosh barmoq surish | Ekran — yagona yorug'lik manbai | Oq chaqnash |
| 5 | 192–247 | 7.98–10.30 | "ko'rish qobiliyatini vaqtincha o'chirib qo'yadi" | **Rentgen**: shaffof bosh, ikki ko'z olmasi; "o'chirib" da ekran tarafdagi ko'z va uning nervi so'nib qoraydi | Rentgen bosh atrofida aylanma (orbit) | `Laying_Sleeping` (rentgen nusxa) | Ko'k rentgen fresnel; ko'z so'nishida qizil chaqnash | Kesish + "bass hit" |
| 6 | 248–334 | 10.30–13.90 | "Zimziyo xonada ko'z qorachig'i ko'proq yorug'lik yig'ish uchun" | **Makro ko'z** qorong'uda: qorachiq sekin kengayadi | 50 mm makro, sekin push-in | Qorachiq o'lchami kalitlanadi | Juda past, sovuq ko'k rim | Kesish |
| 7 | 335–382 | 13.90–15.92 | "maksimal darajada kengaytiriladi" | Qorachiq birdan maksimal kengayadi (rangdor parda ingichka halqa bo'lib qoladi) | Crash zoom + silkinish | Qorachiq 2.5 -> 7.5 mm | Shu | Kesish |
| 8 | 383–463 | 15.92–19.28 | "Bu holatda telefon ekranidan chiqayotgan o'tkir ko'k nur" | **LOW-ANGLE ACTION**: ekrandan o'tkir ko'k nur dastasi yuzga otiladi | 18 mm, matras sathidan telefon yonida, nur bo'ylab yuzga uchish | Telefon qo'lda | Hajmli ko'k nur konusi (glow) + ekran | Nur ichiga sho'ng'ish |
| 9 | 464–521 | 19.28–21.72 | "to'g'ridan-to'g'ri kengaygan qorachiq orqali" | **Ko'z kesimi** (10x): ko'k nur keng qorachiqdan, gavhardan o'tib, ko'z tubida nuqtaga yig'iladi | Yondan, nur bo'ylab tracking | Nur oldinga "yuguradi" (emissiya maskasi) | Ko'k nur, qorong'u studiya, ko'z ichki qizg'ish | Kesish |
| 10 | 522–619 | 21.72–25.78 | "ko'z tubidagi fotoretseptorlarga xuddi lazer nuridek zarba beradi" | **Mikro to'r parda**: tayoqcha/kolbochkalar o'rmoni; ko'k "lazer" uradi — ular oq qizib, chaqnaydi | Past burchak, o'rmon ichida, "zarba"da crash zoom + silkinish | Retseptorlar emissiyasi to'lqin bo'lib tarqaladi | Ko'k lazer, qizil-to'q sariq chaqnash | Oq chaqnash |
| 11 | 620–693 | 25.78–28.86 | "Bir ko'zingiz yostiqqa yopilib qorong'ulikka moslashgan" | Rentgen bosh, yostiq tomondagi ko'z: tinch, to'q ko'k, keng qorachiq | Pastdan sekin aylanma | Rentgen | Sovuq ko'k (moslashgan ko'z) | Yonlama "whip" |
| 12 | 694–746 | 28.86–31.08 | "ikkinchisi esa yorug'likdan kuygan paytda" | Ekran tomondagi ko'z: to'r parda to'q sariq "kuygan", qorachiq kichik | Whip pan bilan kirish, push-in | Rentgen | Issiq to'q sariq/qizil | Kesish |
| 13 | 747–800 | 31.08–33.32 | "miyada signal chalkashuvi yuz beradi" | Ikki nerv bo'ylab har xil rangli impulslar (ko'k va to'q sariq) xiazmada to'qnashadi, miya qizil miltillaydi | Rentgen boshga crash zoom + silkinish | Impuls "poyezd" materiali | Ko'k + to'q sariq + qizil miltillash | Qora kadr (1 kadr) |
| 14 | 801–882 | 33.32–36.72 | "Telefonni o'chirgan zahotingiz, ekranni ko'rgan ko'zingiz" | Bosh barmoq tugmani bosadi, ekran o'chadi, xona zimziyo; Megan boshini ko'taradi, ikki ko'zini ochadi | Telefon yonidan yuzga push-in | IK: bosh barmoq; bosh ko'tarilishi (Head kalitlari) | Faqat oy nuri | Kesish |
| 15 | 883–994 | 36.72–41.40 | "15 daqiqagacha hech narsani ko'rmay, butunlay qorong'u bo'lib qoladi" | **PAYOFF / REVEAL**: Megan POV — kadr ikkiga bo'linadi: chap yarmi (moslashgan ko'z) xonani ko'radi, o'ng yarmi butunlay qora; soat 23:47 -> 00:02 ga o'tadi; oxirida kamera chekinadi, yuzning yarmi qorong'ilikka singadi -> qora | POV sekin chayqalish, so'ng tez orqaga zoom | Bosh sekin buriladi | Oy nuri; o'ng yarmi 0 | Qora, past "drone" bilan tugaydi |

## Manbalar (hammasi bepul, login kerak emas)

- Mixamo (HF `Linzhan/Mixamo-Animations-Characters`): qahramon **Megan**; harakatlar `Laying_Sleeping` (asos, yonboshlab),
  `Laying_Idle`; qo'l/telefon — IK (`chotka.py` dagi usul).
- Poly Haven (CC0): HDRI `kloofendal_48d_partly_cloudy_puresky` (deraza tashqarisi, tunga to'g'rilangan), teksturalar
  `laminate_floor_02`, `painted_plaster_wall`; modellar `GothicBed_01`, `ClassicNightstand_01`, `alarm_clock_01`,
  `potted_plant_01`, `Shelf_01`, `book_encyclopedia_set_01` (yostiq sahnasidan), lampa `desk_lamp_arm_01`.
- BlenderKit (bepul): ayol bosh suyagi `49c13194` (rentgen, `ishqalash` dan).
- Telefon, nur, ko'z kesimi, to'r parda, impulslar: Python kodi bilan (procedural).
- Tovush effektlari: sintez qilinadi (`sfx.py`, litsenziya muammosi yo'q).
