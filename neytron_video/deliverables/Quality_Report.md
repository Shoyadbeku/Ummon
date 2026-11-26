# Quality Report — Final_YouTube_Video_16x9.mp4

## Texnik ko‘rsatkichlar (ffprobe / ffmpeg bilan o‘lchangan)
| Parametr | Natija |
|---|---|
| Format | MP4, H.264 High, yuvj420p |
| O‘lcham / nisbat | 1920×1080, 16:9 (gorizontal) |
| Kadr tezligi | 30 fps |
| Davomiylik | 10:49.28 (ovoz 10:26.71 + 0.5 s kirish + 22 s manbalar titri) |
| Bitreyt | ~8.1 Mbit/s (CRF 18) |
| Audio | AAC-LC, 48 kHz, stereo |
| Integral balandlik | **−14.0 LUFS** (YouTube me’yori), LRA 2.2 LU |
| Qora kadrlar (blackdetect ≥0.3 s) | **Yo‘q** (birinchi renderda 3 ta topilib, tuzatildi) |

## Audio
- Original ovoz saqlangan: so‘zlar o‘zgartirilmagan, sun’iy ovoz qo‘shilmagan.
- Ishlov: highpass 70 Hz, yengil shovqin kamaytirish, EQ, de-esser, 2.5:1 kompressiya, loudnorm. Yozuv dastlab toza bo‘lgani uchun (sukut −120 dB) ishlov minimal.
- Musiqa — original sintez (D-minor drone/pad, taranglik "yurak urishi" hujum bo‘limlarida, 8 ta impact, 42 ta whoosh). Ovoz paytida avtomatik ducking; fon ovozdan ~18 dB past.

## Subtitrlar
- 1331 so‘z, 223 ta cue; har bir so‘z original ovoz vaqtiga bog‘langan (Whisper large-v3 so‘z vaqtlari).
- Matn qo‘lda o‘zbek lotin imlosiga tuzatilgan; noaniq joylar (1:27, 1:51) audio qayta tahlil qilinib tekshirilgan. Muallif aytgan so‘zlar o‘zgartirilmagan (masalan, "Shimoliy Koreya prezidenti").
- Ismlar ikki cue orasida bo‘linmaydi. Joriy so‘z sariq rangda ajratiladi.
- `Subtitles.srt` videodagi vaqtga (+0.5 s) moslangan.

## Autentiklik tekshiruvi (vizual)
Har bir rasm yuklangandan keyin ko‘z bilan tekshirildi. Natijalar:
- ✅ Kim Chen In, Kim Chen Ir, Kim Ir Sen, Kim Yo Jong — barcha kadrlarda aynan shu shaxslar.
- ❌ Rad etilgan: Kremlin 2019 galereyasi (6 ta rasm — faqat Putin), Kremlin Vostochniy galereyasidagi 14 ta rasm (Kim yo‘q), "Kim/Trump impersonators" (soxta shaxslar), "Kim Yong-nam"/"Kim Chol Nam" (boshqa odamlar), ikki "Siti Aisyah" rasmi (ismdosh boshqa ayollar), "2018 inter-Korean summit 05" (chiroq shousi), Shoh Olam sudi rasmlari (boshqa ish), "Former residence of Kim Jong-Nam" (joyi tasdiqlanmagan).
- Begona odam asosiy qahramon sifatida ko‘rsatilmagan. Tramp va Putin faqat Kim Chen In bilan rasmiy uchrashuv kadrlarida, matn "davlat rahbarlarining rasmiy uchrashuvlari" haqida bo‘lganda (9:37–9:50) yoki Kim yuzi markazda bo‘lgan qirqimda.
- Litsenziyali material topilmagan holatlar → grafika (Missing_Authentic_Footage.md).

## 22 savollik QC ro‘yxati
1–2. Inson va voqea mosligi — ✅ (yuqoriga qarang). 3. Joy/sana — ✅ (KLIA2, Tokio, Makao, Pxenyan, Gaaga; sanalar audio bilan bir xil). 4–5. Haqiqiylik, manba ishonchliligi — ✅ (rasmiy nashriyotchilar, Commons tavsiflari). 6. Foydalanish huquqi — ✅ (PD / CC; Fair_Use_Assessment.md). 7. Begona inson — ✅ yo‘q. 8. Aloqasiz stock — ✅ yo‘q. 9. Jumlaga moslik — ✅ (Storyboard.csv har sahna uchun). 10. Subtitr sinxroni — ✅. 11. Animatsiyalar — ✅ spring/interpolatsiya, 10 kadrli dissolve. 12. Ovoz/musiqa balansi — ✅. 13. 16:9 — ✅. 14. Sifat — ✅ (rasmlar 2400 px gacha, cover/contain + blur fon, cho‘zilmagan). 15. Qora ekranlar — ✅ yo‘q. 16. Hujjatli uslub — ✅. 17. YouTube’dan faqat qisqa parchalar — ✅ (faqat bitta-bitta kadr, Commons orqali). 18. Fair Use bahosi — ✅ (kerak emas, barchasi PD/CC). 19. Ekranda manba — ✅ har bir uchinchi tomon materialida + oila daraxtida. 20. Manba/URL to‘g‘riligi — ✅ (CSV’larda). 21. YouTube qidiruvi chuqurligi — ⚠️ YouTube’ga to‘g‘ridan-to‘g‘ri kirish o‘rniga uning ochiq litsenziyali nusxalari ishlatildi. 22. snapyt.app huquqiy holati — ⚠️ ishlatilmadi (YouTube ToS).

## Ma’lum cheklovlar
- **Harakatlanuvchi video kliplar yo‘q.** Tasdiqlangan PD/CC videolar topildi, lekin `upload.wikimedia.org` bu muhitni 3+ soat davomida HTTP 429 bilan blokladi; o‘rniga shu videolardan tekshirilgan kadrlar Ken Burns harakati bilan ishlatildi va ekranda "video kadri" deb belgilandi. Loyiha video sahnalarni qo‘llab-quvvatlaydi; fayllar olinsa, `storyboard.ts` da `kind: 'video'` qilib almashtirish mumkin (vaqtlar Missing_Authentic_Footage.md da).
- Kim Chen Nam’ning litsenziyali tasviri mavjud emasligi sababli u faqat ism/siluet bilan ko‘rsatilgan.
- Hujum lahzasi faqat "GRAFIK REKONSTRUKSIYA" sifatida; soatdagi "~09:00" taxminiy (rekonstruksiya ekanligi belgilangan).
- Fayl hajmi 658 MB (yuqori sifat, film grain sababli); YouTube uchun muammo emas.
