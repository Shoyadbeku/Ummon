# Quality Report — Final_Professional_News_Documentary.mp4

## 1. Eksport natijalari (o‘lchangan)
| Parametr | Natija | Talab |
|---|---|---|
| O‘lcham | 1920×1080, 16:9, landshaft | 4K yoki Full HD ✓ (izoh pastda) |
| Kadr tezligi | 25 fps, butun video bo‘ylab bir xil | 25/30 ✓ |
| Kadrlar soni | 8404 (336.16 s) | — |
| Video | H.264 High, yuv420p, CRF 20, keyint 50, ~2.1 Mbit/s | H.264 ✓ |
| Audio | AAC 256 kbit/s, 48 kHz, stereo | AAC ✓ |
| Balandlik | −14.1 LUFS integrated, true peak −2.3 dBTP | YouTube: −14 LUFS, ≤ −1 dBTP ✓ |
| Fayl | 86.5 MB, MP4 (+faststart) | GitHub < 100 MB ✓ |
| Davomiylik | 5:28.17 audio + 8 s yakuniy titrlar = 5:36.16 | Audio davomiyligi ✓ (+ manbalar titri) |
| Dekodlash testi | `ffmpeg -f null` xatosiz | ✓ |

**Nega 4K emas:** barcha vizual manbalar fotosuratlar. Ularning ko‘pi 1920–3840 px, Ken Burns uchun yana 25% zaxira kerak. 4K ga sun’iy kattalashtirish sifat qo‘shmaydi, faqat hajmni 4 barobar oshiradi. Prompt ruxsat bergan Full HD fallback tanlandi. Loyiha `W, H` ni o‘zgartirib 4K da render qilishga tayyor.

## 2. Audio–video sinxronizatsiyasi
- Transkripsiya: Whisper large-v3, **so‘z darajasidagi vaqt belgilari** bilan. Barcha grafik voqealar shu vaqtlarga bog‘langan: masalan, "12" raqami 2.02 s da (so‘z aytilgan lahza), "11→12" hisoblagichi 54.06 s da, 1+4+5+2 tuzilmasi har bir son aytilganda (90.86 / 92.16 / 93.80 / 95.16 s), "78%" 122.78 s, "98%" 128.66 s, "600 000" 220.68 s.
- Video bo‘laklari (4+3 ta parallel render) kadrma-kadr ulangan, chegaralar tekshirildi (84.0/84.08 s, 168.0/168.08 s) — sakrash yo‘q.
- Audio oqimi videodan 11 ms qisqa (AAC freymlash) — sezilmaydi.

## 3. Ovoz va musiqa
- Asl ovoz saqlandi, sun’iy ovoz yo‘q. Ishlov: high-pass 70 Hz, de-esser, yumshoq kompressor (2.5:1). Og‘ir shovqin tozalash qo‘llanmadi: asl yozuvning shovqin darajasi −71 dB, ya’ni allaqachon toza.
- Musiqa: original sintez (A minor, 92 BPM). Ovoz kelganda sidechain orqali pasayadi. Nutq paytida mix RMS −16.6 dB, faqat musiqa (titrlar) −24.2 dB.
- SFX: 9 whoosh (bo‘lim bumperlari), 4 impact (hook "12", "BEPUL", "MUHOKAMA", "2027"), 10 tick (hisoblagichlar).

## 4. Faktlar tekshiruvi
| Audiodagi da’vo | Holat | Manba |
|---|---|---|
| 24-noyabr, Qonunchilik palatasi, 3-o‘qish, Senatga yuborildi | ✓ | Kun.uz, Gazeta.uz 25.11.2026 |
| Tayyorlov — majburiy umumiy o‘rta ta’limning 1-bosqichi | ✓ | Gazeta.uz 18/25.11 |
| Bog‘cha / maktab / ijtimoiy muassasa / xususiy | ✓ | Gazeta.uz, Ta’lim xabarlari |
| Sardor Rajabov, 2025-yil sentyabr | ✓ (vazir o‘rinbosari) | Gazeta.uz EN 09.09.2025 |
| Tuzilma 1+4+5+2 | ✓ — 2025-yildagi **taklif**. Ekranda "2025-yil sentyabrda e’lon qilingan taklif" deb yozilgan | Gazeta.uz EN |
| 78% / 98% / 4000+ / 191 maktab, 246 guruh / ~800 guruh, ~20 000 o‘rin | ✓ (deputat Sayyora Imomova) | Gazeta.uz 25.11 |
| 2027 — 100% qamrov | ✓ (PF-242) | Gazeta.uz, Ta’lim xabarlari |
| Davlat muassasalarida bepul | ✓ | Gazeta.uz, Ta’lim xabarlari |
| ~600 000 ota-ona (Erkin Murodov) | ✓ | Gazeta.uz 25.11 |
| Saydullo Azimov savollari | ✓ | Gazeta.uz 18/25.11 |
| **Senatning navbatdagi yalpi majlisi 27-noyabr** | ⚠ **o‘qilgan manbalarda topilmadi**. Ovozda bor, o‘zgartirilmadi. Ekranda bu sana grafika sifatida **chiqarilmagan** | — |
| 2017-yilgacha 9+3 tizimi | ✓ (umumiy ma’lum fakt) | — |

## 5. ⚠ Muallif tekshirishi kerak bo‘lgan joy
- **03:04 (184.3 s):** Whisper ikki marta, ikki tilda tekshirilganda ham **"Islohot *muxoliflari*"** deb eshitdi. Gap mazmuni ("12 yillik tizim bu to‘siqni kamaytiradi va chet elda o‘qishni osonlashtiradi") islohot **tarafdorlari/mualliflari** fikri. Subtitr va grafikada **"mualliflari"** yozildi. Agar ovozda haqiqatan "muxoliflari" deyilgan bo‘lsa, bu faktik xato. Shu jumlani qayta yozib olish tavsiya etiladi.
- Audio fayl nomi ("Neytron_yulduzining_aql_bovar_qilmas_og‘irligi_SadoStudio 5.wav") mazmunga mos emas. Noto‘g‘ri fayl yuborilmaganini tekshiring.

## 6. Autentiklik nazorati (prompt §15)
| # | Savol | Javob |
|---|---|---|
| 1–3 | Begona inson/voqea asl sifatida ko‘rsatilmaganmi? | ✓ Deputatlarning yuzi yo‘q (portret topilmadi). Zal surati "ARXIV, 22.10.2026" deb belgilangan. Boshqa voqea rasmlari (C5 sammiti, Tailand) **rad etilgan** |
| 4–5 | Materiallar haqiqiy, manbalar tekshirilgan | ✓ har bir rasm ko‘zdan kechirildi (joy, mazmun) |
| 6 | Huquq baholangan | ✓ `Fair_Use_Assessment.md` |
| 7 | YouTube’dan qisqa parchalar | ✗ YouTube yuklashni bloklagan, topilganlar CC emas — `Missing_Footage_Report.md` |
| 8–9 | Manba ekranda, URL saqlangan | ✓ har bir foto kadrida pastki o‘ng burchakda; URL’lar CSV va tavsifda |
| 10 | Aloqasiz stock yo‘q | ✓ stock ishlatilmagan |
| 11 | Sinxron | ✓ (2-bo‘lim) |
| 12–13 | Subtitr va imlo | ✓ o‘zbek lotin imlosi (o‘, g‘, ’) qo‘lda tuzatildi, ismlar manbalardan tekshirildi. ⚠ 5-bo‘limga qarang |
| 14 | Ovoz/musiqa balansi | ✓ |
| 15 | 16:9 | ✓ |
| 17 | YouTube qidiruvi chuqurligi | 12 so‘rov (o‘zbek, rus, ism-familiyalar, rasmiy kanal), 15 mos video ro‘yxatga olindi |
| 18 | snapyt.app | Sayt tekshirildi, ishlatilmadi (sabab — `Missing_Footage_Report.md`) |

## 7. Ma’lum cheklovlar
- Videoning ~60% motion graphics, ~40% fotosurat. Harakatlanuvchi haqiqiy video kadr yo‘q (sabab yuqorida).
- Subtitrlar videoga "kuydirilmagan" — `Subtitles.srt` ni YouTube’ga alohida yuklang (CC tugmasi).
- Pastki tasmadagi (ticker) yorliq "TA’LIM" — kanal brendi qo‘shilmagan. Kerak bo‘lsa `render.py` dagi `TICKER` / `draw_chrome()` da o‘zgartiring.
