# Sifat hisoboti — Final_Video.mp4

## Texnik ko'rsatkichlar (ffprobe / ffmpeg bilan o'lchangan)

| Parametr | Natija |
|---|---|
| Format | MP4, H.264 (yuv420p, CRF 16, ~12 Mbit/s) + AAC 320 kbit/s, 48 kHz stereo |
| O'lcham / FPS | 1080×1920, 30 fps, 1051 kadr |
| Davomiyligi | 35.05 s (ovoz 35.02 s) |
| Ovoz balandligi | −14.2 LUFS integrated, peak −1.1 dBFS (YouTube/TikTok/Instagram me'yori) |
| Qora kadrlar | `blackdetect` (≥0.1 s) — topilmadi |
| Fayl hajmi | 53.6 MB |

## Tekshiruv ro'yxati

1. **Footage ovoz mazmuniga mosmi?** Ha. Har bir gap o'z sahnasiga ega (STORYBOARD.md), so'z vaqtlari Whisper'dan olingan.
2. **Subtitr vaqti.** Videoga subtitr kuydirilmagan (so'rov bo'yicha). Asosiy so'zlar kinetik tipografiya sifatida aytilgan paytida chiqadi. `Subtitles.srt` alohida taqdim etilgan.
3. **Motion graphics silliqmi?** Spring/easing animatsiyalari; ECG, BPM va yurak pulsatsiyasi musiqadagi urishlarga kadrma-kadr bog'langan. Xato topildi va tuzatildi: ECG/BPM avval sahnaning lokal vaqtini ishlatgan va sinxron bo'lmagan.
4. **Keraksiz qora ekran yo'qmi?** Yo'q (blackdetect). "Eng qizig'i" sahnasidagi qora fon — ataylab qilingan pattern interrupt.
5. **Ovoz va musiqa balansi.** Musiqa ovoz ostida sidechain orqali pasaytiriladi (6:1), SFX esa 2.5:1. Ovozga highpass, yengil shovqin kamaytirish, EQ, de-esser va kompressor qo'llandi. Asl yozuv allaqachon toza edi (shovqin fon −71 dB).
6. **Vizual ritm.** 20 ta sahna, 35 soniyada 25 dan ortiq kesim (har 1–1.5 s da yangilanadi).
7. **Takrorlanish.** 12 ta Mixkit klipi va 14 ta fotoning har biri bir martadan ishlatilgan. Bitta istisno: w01 (yosh Ronaldo) "15 yoshida" va "o'smirligida" sahnalarida ataylab takrorlangan. Bu bitta hikoya bo'lagi.
8. **Mobil ekranda o'qilishi.** Sarlavhalar 100–620 px Anton shriftida. Matnlar UI xavfsiz zonasida (yuqoridan 230 px, pastdan 380 px bo'sh).
9. **Hook.** 0–1.7 s: flesh + glitch + "RONALDO" slam, keyin ulkan qizil "15" va yurak urishi.
10. **Studiya darajasi.** Rang korreksiyasi, film grain, vignette, light leaks, 2.5D parallax, 3D kartalar, animatsiyali xarita.

## Ma'lum cheklovlar (ochiq aytilgan)

- **Ronaldo'ning haqiqiy video lavhalari ishlatilmagan.** O'yin va intervyu kadrlarining huquqi klublar, UEFA/FIFA va teleko'rsatuvchilarga tegishli. Shuning uchun Ronaldo litsenziyali Wikimedia fotosuratlari (Ken Burns / parallax bilan) orqali ko'rsatilgan, harakatli video esa umumiy stock footage (Mixkit).
- Pexels, Pixabay, Unsplash API kalit talab qiladi (bu muhitda yo'q). Pexels/Pixabay CDN proksi tomonidan bloklangan. Ishlatilgan manbalar: Mixkit + Wikimedia Commons.
- Musiqa sintez qilingan (numpy). U toza va huquqiy jihatdan xavfsiz, lekin professional kompozitor yozgan treklar darajasida emas. Kerak bo'lsa `public/mix.wav` ni o'zingizning litsenziyali trekingiz bilan almashtiring (`audio/mix.sh`).
- Transkripsiya Whisper large-v3 dan olingan va qo'lda tuzatilgan (o'zbek tili). "bo'landi" so'zi "bo'ldi" deb talqin qilingan.
- "Taxikardiya" yorlig'i va statistikalar (5× Ballon d'Or, 5× Chempionlar ligasi, Euro 2016) faqat ekranda ko'rsatiladi. Ular ochiq manbalarda tasdiqlangan faktlar va ovozga qo'shilmagan.
- Fayl nomi "Neytron yulduzi…" deb atalgan, lekin ovoz Ronaldo haqida. Montaj ovoz mazmuniga qarab qilingan.
