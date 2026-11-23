# Sifat hisoboti — “Kreml sukut saqlaydigan savollar”

## Texnik ko‘rsatkichlar (ffprobe / ebur128 bilan o‘lchangan)
| Ko‘rsatkich | Natija |
|---|---|
| Format | MP4, H.264 (yuv420p, CRF 18) + AAC 320 kbit/s, 48 kHz stereo |
| O‘lcham | 1920×1080, 16:9 gorizontal, 30 fps |
| Davomiylik | 9:05.0 (asl audio 9:00.86 va 4 soniyalik yakuniy karta) |
| O‘rtacha bitreyt | 7,25 Mbit/s, fayl hajmi 494 MB |
| Ovoz balandligi | −16,2 LUFS integrated (YouTube uchun mos) |
| Qora ekran | `blackdetect` (≥0,5 s) hech narsa topmadi |

## Audio
- Asl ovoz almashtirilmagan, qisqartirilmagan va vaqti surilmagan. Faqat tozalangan: 75 Hz highpass, `afftdn` shovqin kamaytirish, EQ (−2 dB / 250 Hz, +2 dB / 3,2 kHz), de-esser, 3:1 kompressor, loudnorm −16 LUFS.
- Fon musiqasi ffmpeg bilan sintez qilingan original dron (D minor akkord va pushti shovqin). Uchinchi tomon litsenziyasi yo‘q. Nutq paytida musiqa ~0,28 ga, pauzalarda 0,55 ga tushiriladi.
- Effektlar ham sintez qilingan: bob kartalarida whoosh, muhim sanalarda past chastotali impact.

## Subtitrlar
- Whisper large-v3 so‘z darajasidagi vaqtlari bo‘yicha 124 jumla, 180 subtitr bloki (har biri ≤ 64 belgi).
- Matn asl ovozga qarab qo‘lda tuzatilgan (o‘zbek lotin yozuvi). Ovozda yo‘q so‘z qo‘shilmagan.
- Videoga kuydirilgan, alohida `Subtitles.srt` ham bor (YouTube’ga yuklash uchun).
- Aniqlik bo‘yicha eslatma: “ommalda da” → “omma oldida”, “aprishti” → “gapirishda” kabi bir nechta noaniq joylar kontekst bo‘yicha tiklangan. Yuklashdan oldin SRT’ni bir marta ko‘zdan kechirish tavsiya etiladi.

## Autentiklik tekshiruvi
| Savol | Natija |
|---|---|
| Ko‘rsatilgan odam audioda tilga olingan odammi? | Ha. Putin (Kremlin.ru videolari), Lyudmila (Kreml arxivi), Kabayeva (kremlin.ru izohida nomi yozilgan), Peskov (kremlin.ru izohida nomi yozilgan, kadr faqat u qoladigan qilib kesilgan), Tixonova (Commons toifasi + forum hisoboti). |
| Begona odam asosiy qahramon sifatida chiqmaydimi? | Kliplar sahna o‘zgarishlari bo‘yicha tekshirildi (`select=scene`), faqat Putin yoki zalning umumiy plani bor qismlar ishlatildi. Jurnalistlar faqat umumiy planda, “jurnalistlar/matbuot” deyilgan jumlalarda. |
| Boshqa voqea asl voqea sifatida ko‘rsatilmadimi? | 2012-yilgi inauguratsiya surati ajrashuv sahnasida turibdi, lekin ekranda “Surat: 7-may 2012” deb aniq yozilgan. Sidney-2000 surati ekranda “Sidney-2000” deb belgilangan. Kreml zallari “Moskva Kremli” deb belgilangan, aniq zal nomi da’vo qilinmagan. |
| Stock footage | Ishlatilmagan. |
| AI bilan yaratilgan yuz yoki odam | Yo‘q. |
| Voyaga yetmaganlar | Hech qanday tasvir yo‘q, faqat matn. |
| Faktlarning holati | Har bir da’vo rangli belgi bilan: yashil — rasmiy fakt, sariq — jurnalistik surishtiruv, qizil — tasdiqlanmagan. |
| Manbalar va litsenziya | `Authentic_Media_Sources.csv`: har bir fayl, URL, litsenziya va ishlatilgan vaqt. Har bir kadrda yuqori o‘ng burchakda kredit yozuvi. |

## Faktlar tekshiruvi (audiodagi da’volar)
- 1983-yilgi nikoh, 2013-yil iyunidagi ajrashuv e’loni, qizlarning ismlari, Kabayevaning Afina-2004 oltin medali, NMG rahbarligi — umumiy ma’lum faktlar.
- Putinning 2008-yildagi rad javobi Kremlin.ru stenogrammasidan olindi (18.04.2008).
- 2022-yilgi AQSH sanksiyalari: treasury.gov JY0705 (06.04.2022), asl matn ekranda ko‘rsatilgan.
- Dossier Center (04.09.2024) va RFE/RL “Sistema” (28.05.2026) nashrlari mavjudligi tasdiqlandi.
- “Proyekt” (2020) va Peskovning rad javobi keng xabar qilingan. Proekt sayti bu muhitdan ochilmadi, shuning uchun to‘g‘ridan-to‘g‘ri tekshirilmadi.
- Videoga audioda yo‘q bir nechta aniqlik qo‘shildi: qizlarning tug‘ilgan yillari (1985 va 1986), rasmiy ajrashuv 2014-yilda, Kabayeva 1983-yilda Toshkentda tug‘ilgan, gazeta tez orada yopilgan, Duma 2007–2014. Bular ekrandagi matnda, ovoz o‘zgartirilmagan.

## Ma’lum cheklovlar
- Wikimedia Commons bu muhitdan so‘rovlarni cheklagani (HTTP 429) uchun 4 ta litsenziyali surat yuklanmadi. Ularning o‘rniga nima qo‘yilgani `Missing_Authentic_Footage.md` da.
- Kreml arxividagi eski suratlar past aniqlikda (300–500 px). Ular “arxiv nusxasi” ramkasida, xira fon ustida ko‘rsatildi.
- Hujjatli film darajasidagi litsenziyali musiqa kutubxonasi yo‘q edi, original sintez musiqa ishlatildi.
- Fayl nomi “Neytron yulduzining… og‘irligi” deb atalgan, lekin audio mazmuni Putinning shaxsiy hayoti haqida. Video audio mazmuniga qarab qurildi.
