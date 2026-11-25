# Topilmagan haqiqiy footage va uning o‘rniga ishlatilgan halol yechimlar

## Asosiy cheklov — nega videoda YouTube kadrlari yo‘q
1. **YouTube yuklab olishni bloklagan.** Qidiruv ishladi (15 ta mos video topildi, `YouTube_Footage_Report.csv`). Lekin har qanday videoni ochishga urinishda YouTube bu bulut serveridan "Sign in to confirm you’re not a bot" va HTTP 429 qaytardi. Bu texnik himoya. Uni chetlab o‘tish (cookie, proksi, snapyt.app kabi uchinchi tomon yuklovchilar) qilinmadi. Prompt ham buni taqiqlaydi.
2. **snapyt.app:** sayt mavjudligi tekshirildi (javob berdi). Lekin u orqali yuklanmadi: (a) yuqoridagi blokni chetlab o‘tish bo‘lardi; (b) topilgan videolarning birortasi CC litsenziyali emas, ya’ni ularni yuklab olib ishlatishga ruxsat yo‘q.
3. **Rasm serverlari ham cheklagan.** Wikimedia Commons (HTTP 429) va Flickr ("CIDR range blocked") bulut IP’larini cheklaydi. Rasmlar sekin, qayta urinishlar bilan bittalab olindi. Rejadagi rasmlarning bir qismi muddatida kelmadi (pastga qarang).
4. **Yandex Images / Pexels / Unsplash:** Pexels 403, Unsplash javob bermadi. Yandex qidiruv natijalari rasmning litsenziyasini bildirmaydi, shuning uchun u yerdan rasm olinmadi.

## Har bir mavzu bo‘yicha

| Audiodagi mavzu (vaqt) | Ideal footage | Topildimi | Ishlatilgan halol yechim |
|---|---|---|---|
| Qonunchilik palatasining 24.11.2026 dagi majlisi (00:03, 00:31) | Majlis zalidan video | Rasmiy kanal ("Oliy Majlis - online") topildi, lekin 24-noyabr yozuvi qidiruvda chiqmadi; yuklab olish bloklangan | Oliy Majlis binosining real CC fotosuratlari + sana/o‘qish/Senat grafik kartasi |
| Parlament muhokamasi, deputatlar (01:57, 03:21) | Majlisdan kadrlar, deputatlarning yuzi | Gazeta.uz dagi "Qonunchilik palatasi efiridan kadr"lar — mualliflik huquqi bilan himoyalangan | Qonunchilik palatasi zalining CC surati, **"ARXIV, 22.10.2026"** yorlig‘i bilan; deputatlar uchun faqat ism + lavozim lower-third (yuz tasviri yo‘q) |
| Sardor Rajabov e’loni, 2025-yil sentyabr (01:23) | UZREPORT TV / O‘zbekiston 24 dan intervyu | Topildi (7WDwfYU9imA), litsenziyasiz, yuklab olinmadi | Vaqt chizig‘i grafikasi + lower-third |
| Prezident raisligidagi yig‘ilish (01:19) | Prezident matbuot xizmati kadrlari | Ochiq litsenziyali mos kadr topilmadi. Oq uydagi C5 sammiti (06.11.2025) rasmlari bor, lekin bu **boshqa voqea** | Faqat matnli vaqt chizig‘i ("Sentyabr 2025 — Prezident raisligida yig‘ilish"). Boshqa voqea surati ishlatilmadi |
| Olti yoshli bolalar, tayyorlov guruhlari (00:17, 00:44, 03:11) | Tayyorlov guruhidagi mashg‘ulot | YouTube’da DMTT kanallari topildi (litsenziyasiz); CC foto topilmadi | Oila surati (CC BY-SA), bog‘cha binosi (CC BY-SA) va grafikalar; tayyorlov guruhi tarbiyalanuvchilari sifatida hech kim ko‘rsatilmagan |
| Bog‘chalar (00:57, 03:11) | Bog‘cha ichki ko‘rinishi | Faqat bino surati (37-son bog‘cha) | Bino surati + "Bog‘cha / Maktab" grafikasi |
| Uzoq hududlar, ijtimoiy muassasalar (01:01) | Qishloq ijtimoiy muassasasi | Tog‘li qishloq surati (CC BY-SA, "O‘ZBEKISTON QISHLOG‘I" yorlig‘i) | Shu surat + O‘zbekiston xaritasi konturi (hech qanday nuqta belgilanmagan) |
| Xususiy bog‘cha va maktablar (01:05) | Xususiy maktab | Toshkentdagi xususiy maktab (DIS) majlislar zali — CC BY 4.0 | Shu surat + matnli karta; xususiy bog‘chaning CC surati topilmadi |
| 2017-yilgacha kollej/litsey tizimi (01:38) | Kollej/litsey arxiv kadri | Farg‘onada o‘quv yurtiga hujjat topshirish navbati (CC BY-SA 2.0, Adam Jones) | Shu surat **"FARG‘ONA, ARXIV"** yorlig‘i bilan + tarix grafikasi |
| Xorijiy universitetlar, "foundation" (02:52) | Xorijiy kampus | Ataylab qidirilmadi: audioda aniq universitet aytilmagan | Jarayon grafikasi |
| Sinfxona, o‘qituvchi mehnati (05:07) | Haqiqiy O‘zbekiston sinfxonasi | "Climate Box" CC0 rasmlari Tailandda olingani aniqlanib **rad etildi**; "Dehibolo school" joylashuvi tasdiqlanmadi; Samarqand o‘quvchilari surati (CC BY) server cheklovi sababli kelmadi | Grafik kompozitsiya |

## Rad etilgan materiallar (autentiklik tekshiruvi)
- `Climate Box Closing Ceremony, Uzbekistan 01/02.jpg` (CC0): nomida "Uzbekistan" bor, lekin ekrandagi yozuvga ko‘ra tadbir Tailandda bo‘lgan. O‘zbekiston sinfxonasi sifatida ishlatish noto‘g‘ri bo‘lardi.
- `White House visit by C5 Central Asian leaders, 06.11.2025` (jamoat mulki): boshqa voqea. 2025-yil sentyabridagi yig‘ilish o‘rnida ishlatilmadi.
- NASA neytron yulduz animatsiyalari: audio fayl nomi "Neytron yulduzining…" bo‘lgani uchun dastlab yuklab olingan. Transkripsiyadan keyin audio 12 yillik ta’lim haqida ekani aniqlanib, o‘chirildi.
- `Lining Up for a School Inscription - Fergana`: olti yoshli bolalar kadri sifatida **ishlatilmadi**, chunki unda o‘smirlar bor. Faqat 2017-yilgacha bo‘lgan tizim haqidagi qismda ishlatildi.

## Videoni kuchaytirish uchun tavsiyalar
1. Qonunchilik palatasi matbuot xizmatidan (t.me/qonunchilikpalatasi) 24-noyabr majlisining foto/videosini so‘rang. Ko‘pincha OAV uchun ochiq beriladi, ruxsatni yozma oling.
2. Mahalliy bog‘chadan tayyorlov guruhi mashg‘ulotini o‘zingiz suratga oling (muassasa va ota-onalarning yozma roziligi bilan). Bu eng autentik va xavfsiz B-roll bo‘ladi.
3. `YouTube_Footage_Report.csv` dagi telekanallardan litsenziya so‘rasangiz, 3–5 soniyalik parchalarni tavsiya etilgan vaqt kodlariga qo‘yish oson. Loyiha shunga tayyor (`Editable_Project/README.md`).
