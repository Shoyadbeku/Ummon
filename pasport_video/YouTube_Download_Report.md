# YouTube Download Report

## 1. Audio tahlili natijasi (muhim)
iCloud havolasidagi fayl nomi: `Neytron_yulduzining_aql_bovar_qilmas_og‘irligi_SadoStudio 10.wav` (7:11, WAV, 44.1 kHz, mono).
**Lekin audio mazmuni neytron yulduzlar haqida emas.** U O‘zbekiston pasporti va viza rejimlari haqida (Henley Passport Index 2026, Shengen, migratsiya, Qozog‘iston/Qirg‘iziston/Singapur bilan taqqoslash).
Shuning uchun footage faqat **audio mazmuniga** qarab qidirildi. Fayl nomi bo‘yicha boshlangan NASA qidiruvi va yuklab olingan bitta NASA videosi tashlab yuborildi va o‘chirildi.

## 2. Qidiruv
- **Vosita:** YouTube qidiruvi (`yt-dlp --flat-playlist`, faqat metama’lumot uchun; video yuklab olish uchun ishlatilmagan).
- **Tillar:** o‘zbek (lotin/kirill), rus, ingliz.
- **So‘rovlar soni:** 40 dan ortiq. Masalan: *Henley Passport Index 2026*, *O‘zbekiston pasporti reyting*, *Узбекистан паспорт рейтинг Henley*, *Toshkent xalqaro aeroporti*, *US Embassy Tashkent visa*, *Шенгенская виза Ташкент*, *Kazakhstan passport Henley index*, *Кыргызстан паспорт*, *European Commission visa suspension mechanism*, *EES entry exit system*, *O‘zbek mehnat muhojirlari*, *Mirziyoyev Tokayev meeting*, *Singapore passport most powerful*, *Schengen 90 180 rule*.
- **Ko‘rib chiqilgan nomzodlar:** ≈300 ta natija.
- **Tanlangan va yuklab olingan:** 35 ta video.

## 3. Yuklab olish — snapyt.app
- Har bir video **https://www.snapyt.app** orqali yuklab olindi: brauzer avtomatlashtirildi (Playwright/Chromium). YouTube havolasi saytning `#video-url` maydoniga kiritildi, “Download” bosildi, sifat tanlandi va saytning o‘z “Download Video” tugmasi bosildi.
- Afzal ko‘rilgan sifat: 1080p MP4, keyin 1080p WEBM, keyin 720p.
- **Natija:** 35/35 muvaffaqiyatli.
  - 1080p: 16 ta.
  - 720p: 3 ta.
  - 480p va undan past: 16 ta. Bu videolar uchun snapyt.app yuqoriroq sifat taklif qilmadi; ikkinchi urinishda ham natija bir xil bo‘ldi. Bu saytning cheklovi (ba’zi videolar faqat progressiv formatlarda berilgan).
- snapyt.app’ni chetlab o‘tadigan boshqa yuklab olish vositasi ishlatilmadi.
- Metadata so‘rovlarida YouTube keyinroq `HTTP 429 / bot tekshiruvi` qaytardi. Shuning uchun kanal nomlari snapyt.app sahifasidan va qidiruv natijalaridan olindi. Yuklash sanalari olinmadi.

## 4. Autentiklikni tekshirish
Har bir videodan 20 kadrli kontakt-varaq (vaqt kodi bilan) yaratildi va vizual ko‘rib chiqildi. Shaxslar ekrandagi titr bo‘yicha tasdiqlandi (Shavkat Mirziyoyev, Qasim-Jomart To‘qayev, Magnus Brunner, Christian H. Kaelin, George Krol). Joylar yozuvlar bo‘yicha tasdiqlandi (“Tashkent International Airport”, Uzbekistan Airways bortlari, Berlaymont, Shengen chegara belgilari).
Keyin montajdagi har bir parchaning o‘rta kadri alohida tekshirildi. Mos kelmagan 5 ta parcha soniyama-soniya ko‘rib chiqilib, to‘g‘ri vaqtga ko‘chirildi:
- Xukda pasport o‘rniga MDH logotipi chiqayotgan edi.
- Shengen xaritasi o‘rnida bino ko‘rinayotgan edi.
- Chegara posti o‘rnida avtomagistral ko‘rinayotgan edi.
- Dollar o‘rnida poezd ko‘rinayotgan edi.
- Xarita o‘rnida boshlovchi ko‘rinayotgan edi.

## 5. Rad etilgan videolar
| Video | Sabab |
|---|---|
| 4hFRn25ImAM (Sarvar Rakhmanov) | AI-generatsiya grafikalar va telefon raqamli reklama; haqiqiy elchixona kadri yo‘q |
| w0yh-qS_MLU (VIZABOR) | Studiyadagi suhbat; vizual jihatdan mavzuni ko‘rsatmaydi |
| KzvJlQ4jAuI (Новости сегодня 24) | Statik stok rasm, 240p |
| dkG816UCKsU (Migratsiya agentligi) | Multfilm-infografika, 360p |
| -z-ggJjZOn0 | 240p, eskirgan ma’lumot |
| qVl0uJaJq84 (Ylva Johansson) | Sobiq komissar; 2026-yil haqidagi jumlaga noto‘g‘ri kontekst berishi mumkin edi |

## 6. Montajda ishlatilgan segmentlar
Har bir parchaning asl va yakuniy vaqt kodi: `YouTube_Footage_Sources.csv`.
