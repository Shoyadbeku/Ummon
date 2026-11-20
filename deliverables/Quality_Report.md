# Sifat hisoboti (Quality Report)

**Yakuniy fayl:** `Final_Video.mp4` — 1920×1080 (16:9), 30 fps, H.264 High (CRF 22, ≤9 Mbps), AAC 256 kbps, 10:14.47, ~342 MB.
(Master render: CRF 18, ~961 MB — talab qilinsa alohida beriladi.)

| # | Tekshiruv | Natija |
|---|---|---|
| 1 | Footage audio mazmuniga mosmi? | ✅ 206 kadr har bir gap/so'zga qo'lda tanlangan (Storyboard.md). 196 noyob klip, takror **0**. Kontakt varaqlarda tekshirildi; yashil fonli (chroma key) va mos kelmagan 2 klip almashtirildi. |
| 2 | Subtitr vaqti | ✅ Whisper large-v3 so'z vaqtlari + qo'lda to'g'rilangan o'zbek imlosi. So'zma-so'z highlight, bir vaqtda faqat bitta faol so'z. |
| 3 | Motion graphics silliqmi? | ✅ Spring/easing animatsiyalar; 23 xil grafika turi still kadrlar orqali tekshirildi, kesilgan SVG xatosi tuzatildi. |
| 4 | Keraksiz qora ekran | ✅ `blackdetect` (≥0.2 s) — **0** ta topildi. Faqat oxirgi 0.5 s ataylab fade-out. |
| 5 | Ovoz va musiqa balansi | ✅ Ovoz: highpass, shovqin kamaytirish, EQ, de-esser, kompressor. Musiqa ovoz ostida sidechain ducking bilan pasayadi. Yakuniy: **-14.0 LUFS**, true peak **-1.9 dBTP**. |
| 6 | Vizual ritm | ✅ O'rtacha kadr ~3 s; har kesmada ken burns + 4 xil kirish effekti; 7 ta bo'lim kartasi. |
| 7 | Takroriy lavhalar | ✅ Bir xil klip ikki marta ishlatilmagan. |
| 8 | Matn o'qilishi | ✅ Montserrat 900, qora kontur + soya, past qismda xavfsiz zona; kalit so'zlar rangli. |
| 9 | Hook | ✅ 0–2.7 s: Yer + "DUNYONI ASLIDA KIM BOSHQARADI?" (ovozdagi ibora), impact + whoosh, tez kesmalar. |
| 10 | Studiya darajasi | Professional, ammo cheklovlar bor ↓ |

## Ochiq aytilishi kerak bo'lgan cheklovlar
- **Footage manbasi:** faqat Mixkit (bepul litsenziya). Bepul versiya 720p, shuning uchun kliplar 1080p ga kattalashtirilgan (lanczos + sharpen + grain). Wikimedia Commons API so'rovlarni cheklab qo'ydi (429), Pexels/Pixabay API kalit talab qiladi. YouTube/X/Facebook kabi ijtimoiy tarmoqlardan litsenziyasi aniq bo'lmagan material ataylab olinmadi.
- **Haqiqiy shaxslar va tashkilotlar:** AQSh prezidenti, Federal Rezerv, BlackRock va Bilderberg uchun haqiqiy arxiv footage yo'q. Ularning o'rnida mavzuga mos stock kadrlar va grafikalar ishlatilgan; logotiplar qo'yilmagan.
- **Transkripsiya:** o'zbek tili uchun Whisper xatolarini qo'lda tuzatdim, lekin 1–2 so'z noaniq eshitilgan bo'lishi mumkin (masalan "ishga ketdingiz"). `data/transcript_uz.txt` faylidan tekshirib, kerak bo'lsa to'g'rilang.
- **Fayl nomi va mazmun:** fayl "Neytron yulduzi…" deb nomlangan, ammo ovozdagi mavzu "Dunyoni aslida kim boshqaradi?". Montaj ovoz mazmuniga qurilgan.
