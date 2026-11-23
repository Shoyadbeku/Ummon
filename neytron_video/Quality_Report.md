# Quality Report — "Saudiya shahzodasining qorong‘i sirlari"

## Texnik ko'rsatkichlar (ffprobe / ebur128 / blackdetect bilan o'lchangan)

| Parametr | Natija | Talab |
|---|---|---|
| Format | 1920×1080, 16:9, gorizontal | ✅ |
| FPS | 30 | ✅ |
| Video kodek | H.264, ~7.8 Mbit/s, CRF 18 | ✅ |
| Audio kodek | AAC, 48 kHz, stereo, 320 kbit/s | ✅ |
| Konteyner | MP4 (718 MB) | ✅ |
| Davomiylik | 11:45.56 (asl audio 11:45.49) | ✅ |
| Balandlik | −13.9 LUFS integrated, True Peak −1.5 dBFS | ✅ YouTube (−14 LUFS) |
| Qora kadrlar (>0.3 s) | Topilmadi | ✅ |

## Audio

- Asl ovoz saqlandi: so'zlar o'zgartirilmagan, sun'iy ovoz qo'shilmagan, tembr tabiiy.
- Ishlov berish: high-pass 70 Hz, yengil shovqin kamaytirish, EQ (250 Hz −1.5 dB, 3.5 kHz +2 dB), de-esser, kompressor 2.5:1, normalizatsiya.
- Fon musiqasi va effektlar **ffmpeg'da noldan sintez qilingan**: mualliflik huquqi muammosi yo'q. Musiqa nutq paytida sidechain bilan avtomatik pasayadi. 8 ta qism boshida whoosh va bass zarbasi bor.

## Autentiklik

- 115 sahna. Har bir vizual material faqat audioda tilga olingan shaxs, joy yoki hujjatga tegishli.
- Begona odamlar va aloqasiz stock footage ishlatilmadi. AI bilan yaratilgan realistik tasvir yoki rekonstruksiya yo'q.
- Ishlatilgan materiallar: 1 ta video (DVIDS, Pentagon 2018), 33 ta foto (Kremlin.ru, AQSh Davlat departamenti, AQSh Energetika vazirligi, Oq uy, VOA, NASA, Wikimedia Commons), 2 bet ODNI hujjati. To'liq ro'yxat `Authentic_Media_Sources.csv` faylida.
- Har bir kadrda ekranda manba va litsenziya ko'rsatiladi (CC BY / BY-SA atributsiya talabi bajarilgan).
- Asl kadri topilmagan holatlar original infografika yoki matnli karta bilan yopilgan. Ular `Missing_Authentic_Footage.md` faylida.

## Subtitrlar

- Whisper large-v3 bilan so'z darajasidagi vaqtlar olindi, keyin matn qo'lda to'g'ri o'zbek lotin imlosiga tuzatildi (343 qator).
- Shubhali bitta joy (09:43) qayta transkripsiya bilan tekshirildi: "javobsiz savollarni ko'rsatadi". Audioda yo'q so'z qo'shilmagan.
- Ekranda so'zma-so'z karaoke-highlight. `Subtitles.srt` YouTube uchun alohida berilgan.

## Faktlar (audio bilan solishtirildi)

1985-yil 31-avgust (tug'ilgan sana), 2015 (Salmon qirol bo'ldi), 2017-yil iyun (valiahd), 2017-yil 4-noyabr (qo'mita), $100 mlrd+ (hukumat raqami sifatida belgilangan), 2018-yil 2-oktabr, 15 kishilik guruh, 2019 BMT surishtiruvi, 2021-yil 26-fevral ODNI. Hujjat muqovasida "Declassified by DNI Haines, 25 February 2021" yozuvi bor, e'lon sanasi esa 26-fevral, ya'ni audiodagi bilan bir xil.

Audioda aytilmagan qo'shimcha faktlar ekranga chiqarilgan joylar: "2018-yil iyun" (ayollarga haydovchilik huquqi), "Jamol Xashoggi (1958–2018)". Ikkalasi ham ochiq manbalarda tasdiqlangan.

## Ma'lum kamchiliklar va tavsiyalar

1. **00:06.7–00:13.5**: ovozda "YouTube documentary. 7–8 daqiqa jurnalistik surishtiruv. Sirli va kinematografik uslub. Ovozga tayyor matn" degan ssenariy ko'rsatmalari o'qilgan. Ular audioda qoldirildi (asl audio o'zgartirilmasin degan talab bo'yicha), lekin ekranda subtitr qilinmadi, o'rniga sarlavha kartasi turibdi. **Tavsiya:** bu ~7 soniyani kesish. Kerak bo'lsa qayta render qilib beraman.
2. Muhammad bin Salmonning ochiq litsenziyali videosi faqat bitta (DVIDS). Unda DoD'ning ingliz tilidagi yozuvlari ichiga yozilgan. Qolgan sahnalar haqiqiy fotolardan 2.5D harakat bilan qurilgan.
3. YouTube va telekanal arxivlaridagi kadrlar litsenziya yo'qligi va bot-blok sababli ishlatilmadi.
4. Video pixel formati `yuvj420p` (full range). YouTube buni to'g'ri qabul qiladi.
