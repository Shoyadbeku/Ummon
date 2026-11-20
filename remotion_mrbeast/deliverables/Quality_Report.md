# Quality Report — Final_Video.mp4

## Texnik parametrlar (ffprobe / ebur128 bilan o‘lchandi)

| Parametr | Talab | Natija |
|---|---|---|
| Format / video kodek | MP4, H.264 | MP4, H.264 High@4.2, `+faststart` ✅ |
| O‘lcham / nisbat | 1080×1920, 9:16 | 1080×1920 ✅ |
| FPS | 30 yoki 60 | 30 ✅ |
| Piksel formati | — | yuv420p, TV range, BT.709 (barcha platformalar bilan mos) ✅ |
| Audio | AAC | AAC-LC 320 kbps, 48 kHz, stereo ✅ |
| Davomiylik | audioga mos | 38.4 s (ovoz 37.1 s + 1.3 s musiqiy outro) ✅ |
| Loudness | — | −14.0 LUFS integrated, true peak −1.5 dBTP (Shorts/Reels/TikTok standarti) ✅ |
| Hajm | — | 73.8 MB (~15.4 Mbit/s) |

## 10 bandlik tekshiruv

1. **Footage mazmunga mosmi?** — Ha. Har bir kesim aytilayotgan so‘zga bog‘langan (21 sahna, `Storyboard.md`). Masalan "456 nafar" → 456 ikonali infografika, "Koreya" → globusdan Seulga zoom, "Squid Game" → qo‘riqchilar, "qo‘g‘irchoq" savoli oldidan Young-hee.
2. **Subtitr vaqtlari to‘g‘rimi?** — Topshiriq bo‘yicha subtitrlar videoga kuydirilmadi. `Subtitles.srt` Whisper so‘z vaqtlaridan olingan, 15 ta qator, ustma-ust tushish yo‘q (≤ 46 belgi).
3. **Motion graphics silliqmi?** — Spring fizikasi, bezier easing, kadrga asoslangan interpolatsiya; still va to‘liq kadr varaqlari (har 0.5 s) ko‘rib chiqildi.
4. **Keraksiz qora ekran bormi?** — `blackdetect` (≥0.05 s): **0 ta**. `freezedetect` (≥0.6 s): **0 ta**.
5. **Ovoz/musiqa balansi** — Musiqa nutq paytida avtomatik pasayadi (ducking, 120 ms oldin). Nutq paytida ovoz −14.2 dBFS, musiqa+SFX −25.0 dBFS → **10.8 dB farq** (birinchi versiyada 7.2 dB edi — musiqa 50 %, SFX 30 % pasaytirildi). Ovoz va video orasidagi siljish: 0 ms.
6. **Vizual ritm** — o‘rtacha kesim ~1.3 s, 30 ta vizual almashuv; beatga mos yengil puls; zarbalarda kamera silkinishi.
7. **Takrorlanish** — 18 ta turli Mixkit klipi va 8 ta turli Commons rasmi; **hech bir klip ikki marta ishlatilmagan**.
8. **Mobil ekranda o‘qilishi** — sarlavhalar 110–330 px Anton shriftida, soya + kontur; asosiy matnlar y = 250…1450 px xavfsiz zonada (TikTok/Reels tugmalari va izoh qismi qoplamaydi).
9. **Hook kuchlimi?** — 0.0 s: oq flash + RGB glitch + trailer impact + kamera silkinishi, ko‘z makro kadri, "TASAVVUR QILING" kinetik matni; 0.9 s da birinchi kesim, 3.3 s da "SQUID GAME" zarbasi.
10. **Studiya darajasimi?** — Rang korreksiyasi, film grain, vinyetka, light leak, glitch, chroma key, 3D ID-karta, xarita animatsiyasi, infografika, split-screen — PowerPoint uslubidagi oddiy fade'lar ishlatilmagan.

## QC jarayonida topilib tuzatilgan kamchiliklar

- Whisper "256" deb tanigan raqam majburiy hizalash orqali tekshirildi → ovozda **456** aytilgan (haqiqiy faktga ham mos).
- Hook'dagi ko‘z kadri juda kattalashtirilgan edi → kamroq zoom qilib qayta kadrlandi.
- Bloger klipi qorong‘i burchakda qolgandi → kadrlash va yorqinlik tuzatildi.
- Split-screen yorliqlari "VS" belgisi va o‘lchagichlar bilan ustma-ust tushgan edi → qayta joylandi.
- 456-o‘yinchi panjarasi pastki interfeys zonasiga kirib ketgandi → kichraytirildi.
- 47495 klipi yashil fonli ekan → SVG chroma key bilan kesilib, brend fon ustiga joylandi.
- Mukofot hisoblagichi $455 555 da to‘xtardi (easing 1 ga yetmasdi) → aniq $456 000.
- 15.3–15.96 s da ekran bo‘sh edi → "UNDA…" qo‘shildi.
- Rendering `yuvj420p` (full range) chiqargan edi → yuv420p TV range BT.709 ga o‘tkazildi.

## Cheklovlar (ochiq aytilishi kerak)

- **Ovozni tozalash**: original yozuv deyarli shovqinsiz edi (−14.8 LUFS), shuning uchun yengil zanjir qo‘llandi: high-pass 75 Hz, afftdn (−8 dB), EQ (−2 dB @220 Hz, +2.5 dB @3.5 kHz, +1.5 dB havo), de-esser, 3:1 kompressor, limiter. Tembr saqlangan.
- **Real MrBeast / Squid Game videolari ishlatilmadi**: YouTube, X, Facebook, VK va boshqa tarmoqlardagi lavhalar mualliflik huquqi bilan himoyalangan va qayta foydalanishga ruxsat yo‘q. Ularning o‘rnida ochiq litsenziyali (CC BY / CC BY-SA / CC0) MrBeast fotolari, Squid Game kosplay/promo suratlari va Mixkit B-roll ishlatildi. Pexels/Pixabay API kalit talab qilgani uchun ishlatilmadi.
- Musiqa va SFX'ni men eshitib tanlay olmayman; ular nomi, janri va energiya egri chizig‘i (RMS tahlili) bo‘yicha tanlandi, tempo avtomatik aniqlandi (~103 BPM). Yakuniy versiyani bir marta quloqchinda eshitib ko‘rish tavsiya etiladi.
- Fayl nomi "Neytron yulduzining aql bovar qilmas og‘irligi" bo‘lsa-da, ovoz mazmuni MrBeast'ning Squid Game loyihasi haqida — video ovoz mazmuni asosida qurildi.
