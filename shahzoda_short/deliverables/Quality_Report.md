# Quality Report — Final_Video.mp4

## Texnik parametrlar (ffprobe bilan tekshirilgan)

| Parametr | Natija |
|---|---|
| Format | MP4 (faststart) |
| Video | H.264, 1080×1920, 9:16, 30 fps, ~9.9 Mbit/s (CRF 17) |
| Audio | AAC 320 kbit/s, 48 kHz |
| Davomiylik | 32.00 s (ovoz 31.6 s + 0.4 s musiqa fade-out) |
| Loudness | −13.7 LUFS integrated, true peak −1.0 dBFS (Shorts/Reels/TikTok uchun normal) |

## Avtomatik tekshiruvlar

- **Qora kadrlar** (`blackdetect`, ≥0.05 s): topilmadi.
- **Qotib qolgan kadrlar** (`freezedetect`, ≥0.6 s): topilmadi.
- **Ovoz/musiqa balansi:** pauzalarda musiqa ovozdan ~10 dB past (−27.6 dB / −24.2 dB, nutqda esa −16.6 dB). Nutq vaqtida musiqa avtomatik pasaytiriladi (ducking).
- **Klip takrori:** 18 ta turli stock klip. Faqat 11942 ikki marta ishlatilgan, ikkalasida ham faylning boshqa qismi, biri xiralashtirilgan fon sifatida.

## 10 bandli tekshiruv

| # | Savol | Natija |
|---|---|---|
| 1 | Footage audio mazmuniga mosmi? | ✅ Har bir sahna aytilayotgan gapga bogʻlangan (Storyboard.md). Ism «Zilola» soʻzi aytilgan kadrda (8.46 s) ochiladi, «emas» soʻzida (25.80 s) chizib tashlanadi. |
| 2 | Subtitr timing toʻgʻrimi? | ✅ Whisper large-v3 soʻz vaqtlari asosida. ⚠️ Aniqligi taxminan ±0.1–0.2 s, qoʻlda bitta tuzatish kiritildi («Sizningcha» boshlanishi). |
| 3 | Motion graphics silliqmi? | ✅ Spring/easing animatsiyalar, kadr-kadr interpolyatsiya. |
| 4 | Keraksiz qora ekranlar yoʻqmi? | ✅ blackdetect: yoʻq. |
| 5 | Ovoz va musiqa balansi | ✅ Yuqoridagi oʻlchovlarga qarang. |
| 6 | Vizual ritm | ✅ Har 0.6–2.6 s da yangi kadr yoki grafika. Eng uzun sahna — split-screen (3.95 s), uning ichida ham 3 ta animatsiya hodisasi bor. |
| 7 | Takrorlanish | ✅ Yuqoridagi «Klip takrori» bandiga qarang. |
| 8 | Mobilda oʻqiladimi? | ✅ Videoga subtitr kuydirilmagan (foydalanuvchi soʻrovi). Subtitrlar alohida `Subtitles.srt` faylida, platformaga yuklasa boʻladi. Yuqoridagi progress bar ham olib tashlangan. |
| 9 | Hook kuchlimi? | ✅ 0-kadrdan Shahzodaning haqiqiy surati, zoom-slam, shake, impact SFX, «SHAHZODA» sarlavhasi; 1.56 s dan sir saqlangan ID-karta. |
| 10 | Professional darajami? | Pastdagi cheklovlarga qarang. |

## Tuzatilgan kamchiliklar (renderdan oldin)

- Subtitrda soʻzlar orasidagi boʻshliq yoʻqolib qolardi: faol soʻzning kattalashishi oraliqni yopib qoʻyardi. Endi kattalashish soʻz uzunligiga qarab cheklanadi.
- «SHAHZODA» sarlavhasi kadr chetidan chiqib ketardi: oʻlcham 168 dan 142 px ga tushirildi.
- Vinil yorligʻidagi surat notoʻgʻri kesilgan edi: yuz markazga olindi.
- Split-screen’da subtitr yuzni yopardi: subtitr ikki yarim orasidagi chiziqqa koʻchirildi.

## Ochiq qolgan masalalar — tekshirib koʻring

1. **«Jonim» guruhi** — Whisper bu joyni «canim gurukhida koshk qilagan» deb eshitdi. Men «Jonim» guruhida qoʻshiq kuylagan» deb yozdim. Guruh nomini va fe’lni (kuylagan / qilgan) tasdiqlang. Kerak boʻlsa, `src/data/timing.ts` va `Main.tsx` dagi «JONIM» matnini tuzatib, qayta render qiling.
2. **Fayl nomi** «Neytron yulduzining aql bovar qilmas ogʻirligi», lekin audioda Shahzoda haqida gapiriladi. Video audio mazmuniga qarab qilindi.
3. **Haqiqiy footage cheklangan.** Shahzodaning kliplari va konsert videolari mualliflik huquqi bilan himoyalangan. Shuning uchun undan faqat bitta CC litsenziyali surat ishlatildi, qolgan kadrlar illustrativ stock. Ikkinchi CC surat (Bishkek, 2019) Wikimedia API cheklovi tufayli yuklanmadi.
4. «Mashhurlik» grafigi va «1 000 000+» hisoblagichi illustrativ: real statistika emas, «millionlab» soʻzini vizuallashtiradi.
5. Ovoz allaqachon toza yozuv edi (−14 LUFS, LRA 2). Shuning uchun faqat yengil ishlov berildi: HPF, yengil shovqin pasaytirish, EQ, de-esser, 2.5:1 kompressiya va normalizatsiya.
6. 60 fps oʻrniga 30 fps tanlandi: render tezroq, platformalar uchun yetarli.
7. **CC BY-SA attribution:** videoning tavsifiga suratning muallifi va litsenziyasini yozing (Media_Sources.md da tayyor qator bor).
