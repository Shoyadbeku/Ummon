# Quality Report — Final_Video.mp4

## Texnik parametrlar (ffprobe / ebur128 bilan o‘lchangan)

| Parametr | Talab | Natija |
|---|---|---|
| Aspect / o‘lcham | 9:16, 1080×1920 | ✅ 1080×1920 |
| FPS | 30 yoki 60 | ✅ 30 fps |
| Konteyner / kodek | MP4, H.264, AAC | ✅ MP4 (faststart), H.264 High@4.2, yuv420p, BT.709 TV-range · AAC-LC 320 kbps 48 kHz stereo |
| Davomiylik | audioga mos | ✅ 35.00 s (ovoz 34.51 s + 0.5 s musiqa dumi) |
| Ovoz balandligi | platforma standarti | ✅ −14.0 LUFS integrated, true peak −1.1 dBFS, LRA 1.7 LU |
| Qora kadrlar | yo‘q | ✅ blackdetect: 0 |
| Muzlagan kadrlar | yo‘q | ✅ freezedetect (>0.5 s): 0 |
| Fayl hajmi | — | 45 MB (~10.3 Mbit/s) |

## Ovoz / musiqa balansi

Ovoz miksdan ayirib o‘lchandi (har 2 soniyada ovoz va fon RMS farqi):

`0–2s +9.7 · 2–4 +11.6 · 4–6 +13.4 · 6–8 +10.4 · 8–10 +9.3 · 10–12 +8.7 · 12–14 +13.2 · 14–16 +15.9 · 16–18 +12.5 · 18–20 +11.2 · 20–22 +11.8 · 22–24 +18.9 · 24–26 +16.8 · 26–28 +12.1 · 28–30 +15.5 · 30–32 +12.9 · 32–34 +15.3 dB`

Ovoz hamma joyda fondan kamida 8.7 dB baland. Birinchi qoralamada boshidagi trailer-impakt "Bugun Toshkentda" so‘zlarini bosib ketgan (−8 dB), 26–28 s dagi drop esa +0.9 dB edi. Ikkalasi ham tuzatildi.

Ovozni tozalash zanjiri: HPF 75 Hz → yengil FFT shovqin kamaytirish → 280 Hz "loyqalik" −2.5 dB → 3.2 kHz aniqlik +2 dB → havo shelf → de-esser → 2.5:1 kompressor → −16 LUFS. Ovoz boshidanoq toza edi (shovqin darajasi < −60 dB), shuning uchun tembrni saqlash maqsadida denoise ataylab yengil qilindi.

## Prompt'dagi QC ro‘yxati

1. **Footage audioga mosmi?** ✅ 22 sahnaning har biri aytilayotgan gapga bog‘langan (Storyboard.md). Haqiqiy joylar: Tashkent City, Sharqshunoslik instituti binosi, Tsukuba kampusi, Toshkentdagi osmono‘par qurilishi.
2. **Subtitr vaqti** ✅ Videoga subtitr yoqib yozilmagan (talab bo‘yicha). Ekrandagi kalit so‘zlar so‘z darajasidagi vaqtlarga ±0.1 s aniqlikda bog‘langan. `Subtitles.srt` alohida berildi.
3. **Motion graphics silliqmi?** ✅ Spring/easing animatsiyalar, motion-blur kirishlar; kalit kadrlar bo‘yicha qoralama tekshirildi.
4. **Keraksiz qora ekran yo‘qmi?** ✅ 0 ta.
5. **Ovoz/musiqa balansi** ✅ yuqoriga qarang. Musiqa drop'i 26.0 s ga ("Katta biznes…") tushirilgan.
6. **Vizual ritm** ✅ o‘rtacha kadr uzunligi 1.6 s; emotsional nuqtada (otasidan ayrilgan) ataylab sekinlashtirilgan.
7. **Takrorlanish** ✅ har bir stok lavha bitta asosiy sahnada ishlatilgan; yakuniy split-screen — ataylab qilingan recap.
8. **Mobil o‘qiluvchanlik** ✅ asosiy matn ≥ 64 px, matn orqasida qorong‘i gradient (scrim), matnlar safe-zone ichida (y 300–1440, o‘ngda 110 px bo‘sh).
9. **Hook** ✅ 0-kadr tiniq va yorqin (Tashkent City kechasi), 0.12 s da TOSHKENT slam + shake + impakt, 4–6 s da "?" pattern interrupt.
10. **Studiya darajasi** — color grade (teal/orange, vintage, oq-qora), grain, light leaks, 2.5D globus va uchish animatsiyasi, kinetik tipografiya.

QC jarayonida tuzatilganlar: 1) birinchi kadr blur'i olib tashlandi; 2) oxirgi sahnada "2 BILIM" karta ostida qolgan edi, karta qayta joylashtirildi; 3) Tsukuba kadrida osmon juda och edi, yuqoriga scrim qo‘shildi; 4) SFX darajalari pasaytirildi; 5) full-range yuvj420p → standart yuv420p BT.709 (Instagram/TikTok'da ranglar yuvilib ketmasligi uchun).

## Bajarilmagan / cheklangan narsalar (ochiq aytilgan)

- **Ijtimoiy tarmoqlardagi videolar** (YouTube, X, Facebook, VK, Rutube, Mover.uz, Reddit) ishlatilmadi: ularda qayta foydalanish uchun ochiq litsenziya yo‘q. **Pexels/Pixabay** API kalitsiz bu muhitda yopiq edi. Manbalar: Mixkit (bepul litsenziya) va Wikimedia Commons (CC).
- **Murod Nazarovning o‘z surati/videosi yo‘q**: ochiq litsenziyali materiali topilmadi. Uni boshqa odam deb ko‘rsatmaslik uchun stok aktyor ishlatilmadi. Agar sizda huquqi bor fotosuratlar bo‘lsa, ularni 3- va 16-sahnaga qo‘shish tavsiya etiladi.
- **Murad Buildings logotipi** ishlatilmadi (savdo belgisi). Nomi faqat tipografiya bilan berildi.
- Musiqa va effektlarni quloq bilan tinglab bo‘lmadi: balans RMS/LUFS o‘lchovlari va to‘lqin shakli tahlili orqali qilindi. Trek tanlovi janr (Film Score), energiya egri chizig‘i va drop joyiga qarab qilindi. Yuklashdan oldin bir marta eshitib ko‘ring.
- Toshkentda haqiqiy qurilish videosi (ochiq litsenziyali) topilmadi, shuning uchun 2/14/15-sahnalardagi qurilish lavhalari umumiy stok kadrlar. Toshkentga xoslik haqiqiy Toshkent fotolari (1, 6, 16-sahnalar) orqali berildi.
- Fayl nomi "Neytron yulduzining aql bovar qilmas og‘irligi" bo‘lsa-da, audioning ichida Murod Nazarov haqida gap ketadi. Video audio mazmuniga qurildi.
