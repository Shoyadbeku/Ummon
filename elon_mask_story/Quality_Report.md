# Sifat hisoboti — Final_Video.mp4 (Ilon Mask: ofisdan raketalargacha)

## Texnik ko'rsatkichlar (ffprobe/ebur128 bilan o'lchandi)
| Parametr | Talab | Natija |
|---|---|---|
| Format / o'lcham | 16:9 | ✅ 1920×1080 (16:9) — foydalanuvchi talabiga ko'ra; tepada progress chizig'i yo'q |
| FPS | 30 yoki 60 | ✅ 30 fps |
| Kodek | H.264 + AAC | ✅ H.264 High (CRF 18–19, ~5.9 Mbit/s) + AAC-LC 48 kHz 256 kbit/s |
| Davomiylik | audio uzunligi | ✅ 8:08.27 (audio 8:08.12) |
| Ovoz balandligi | platforma standarti | ✅ −14.1 LUFS, true peak −1.4 dBFS |
| Hajm | — | 365 MB, `+faststart` |
| Qora kadrlar | yo'q | ✅ `blackdetect` — 0 ta |
| Jimlik (>0.5 s, −45 dB) | yo'q | ✅ 0 ta |

## 10 bandlik tekshiruv
1. **Lavhalar mazmunga mosmi?** ✅ 184 ta kadr, har biri o'sha paytdagi gapga bog'langan (`Storyboard.md`). Yillar, summalar, yosh, nomlar aytilgan lahzada ekranga chiqadi. QC'da 1999-yil sahnasidagi bitkoinli pul lavhasi davrga mos emasligi sababli almashtirildi.
2. **Subtitr** — talabga ko'ra videoga yozilmadi. `Subtitles.srt` (112 qism) alohida beriladi. Ovozsiz ko'rganda mazmun 250+ kinetik sarlavha, raqam va grafika orqali tushuniladi.
3. **Motion graphics silliqmi?** ✅ Spring/easing animatsiyalar; 59 + 30 nazorat kadri ko'rib chiqildi.
4. **Keraksiz qora ekran?** ✅ Yo'q. Har bir kadr keyingisi ostida 8 kadr qoladi. QC'da 45–47 s dagi lampochka lavhasi boshidagi 1.5 s qora qismi kesib tashlandi; split ekranlarning (dush/sport, kun/tun, xavfsiz/xavfli, SpaceX/Tesla) bo'sh yarmi tuzatildi.
5. **Ovoz/musiqa balansi** ✅ Ovoz tozalandi (highpass, denoise, EQ, de-esser, kompressor), −16 LUFS. Musiqa 5 bob bo'yicha 5 trek, 2.5 s crossfade, ovoz ostida sidechain ducking (~14 LU past).
6. **Vizual ritm** ✅ O'rtacha har 2,65 s yangi kadr, ustiga sarlavha/grafika qatlamlari.
7. **Takrorlanish** ✅ 137 ta turli Mixkit + 14 ta NASA + 21 ta rasm. Faqat 3 ta ataylab qilingan oq-qora flashback qayta ishlatilgan (ofisda uxlash, sport zal — hikoyadagi "callback").
8. **Matn aniq ko'rinadimi?** ✅ Anton 80–300 px, Montserrat 900. Portret rasmlar (Mask, Kimbal, Hoover minorasi) va past o'lchamli rasmlar kesilmaydi — xira fon ustida to'liq ko'rsatiladi. Split ekranlar chap/o'ng.
9. **Hook** ✅ 0:00 — oq flash + shake + impact + "TASAVVUR QILING / UYINGIZ YO'Q", 2.4 s ichida 3 ta kesim.
10. **Studiya darajasi** — baho: yuqori sifatli hujjatli ijtimoiy tarmoq montaji. Cheklovlar quyida.

## Halol cheklovlar
- **Ijtimoiy tarmoqlar** (X, Facebook, VK, YouTube, Rutube, Mover.uz, Reddit) dan video olinmadi — huquqni tekshirib bo'lmaydi. Pexels/Pixabay bu muhitda 403 berdi. Manbalar: NASA (PD), Mixkit (free license), Wikimedia Commons (CC/PD).
- **Haqiqiy arxiv kadrlari yo'q**: 1995-yilgi Zip2 ofisi, Maskning yoshlikdagi videolari, Falcon 1 parvoz videosi ochiq litsenziyada topilmadi — o'rniga mos stock lavhalar, Falcon 1 fotosi va original grafikalar ishlatildi.
- **Tarpenning** surati ochiq litsenziyada topilmadi — kartochkada siluet.
- **Format**: 16:9 gorizontal — YouTube uchun ideal. Shorts/Reels/TikTok vertikal formatni afzal ko'radi; kerak bo'lsa alohida 9:16 versiya (birinchi render) mavjud.
- **Musiqa** quloq bilan emas, loudness tahlili bilan tanlandi — e'lon qilishdan oldin bir marta tinglang.
- **Transkripsiya** Whisper + qo'lda tuzatish. Ovozdagi faktlar tekshirildi (Zip2 1995/1999, $307 mln, ~$22 mln, X.com, eBay $1.5 mlrd 2002, Falcon 1 4-urinish 2008, Tesla 2003 Eberhard/Tarpenning, Mask 2004) — ovoz bilan mos.
- **Atribut**: CC BY / CC BY-SA rasmlar uchun post tavsifiga `Media_Sources.md` dagi atribut qatorini qo'shing.
- **Hajm**: 365 MB fayl GitHub cheklovidan (100 MB) katta — repoga qo'shilmadi, alohida yuborildi. Qayta yaratish: `remotion/` + `tools_*.py`.
