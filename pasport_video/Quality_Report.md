# Quality Report

## Texnik ko‘rsatkichlar (ffprobe / ebur128 bilan o‘lchangan)
| Parametr | Natija |
|---|---|
| Format | MP4 (faststart) |
| Video | H.264 High, 1920×1080, **16:9**, 30 fps, yuv420p, ≈12 Mbit/s |
| Audio | AAC-LC, 48 kHz, stereo, 320 kbit/s |
| Davomiylik | 7:26.7 = asl audio 7:11.6 + 15 s manbalar titri |
| Balandlik | **−15.3 LUFS** integrated, LRA 2.2 LU, true-peak −3.0 dBFS (YouTube normalizatsiyasiga mos) |
| Qora kadrlar (blackdetect, ≥0.25 s) | 0 ta |
| Sukunat bo‘shliqlari (≥1.2 s, −45 dB) | 0 ta |
| Vertikal yoki 9:16 element | Yo‘q |

## Audio
- Asl ovoz o‘zgartirilmagan: so‘z qo‘shilmagan yoki olib tashlanmagan, sun’iy ovoz ishlatilmagan. Davomiyligi va ritmi saqlangan.
- Ovozga ishlov berish (ffmpeg): `highpass 70 Hz → afftdn (shovqin kamaytirish) → EQ (−2 dB @250 Hz, +2 dB @3.5 kHz) → deesser → kompressor 3:1 → loudnorm −15 LUFS`.
- Musiqa: original sintez qilingan ambient fon (litsenziya muammosi yo‘q). U nutqdan ≈15 LU pastda, titrlarda kuchayadi.
- SFX (whoosh, impact, riser): original sintez. Faqat grafik va bo‘lim almashuvlarida ishlatilgan.
- YouTube kadrlarining asl audiosi butunlay o‘chirilgan.

## Subtitrlar
- Whisper large-v3 so‘z darajasidagi vaqt kodlari bilan ishlatildi. Matn qo‘lda adabiy o‘zbek lotin yozuviga keltirildi (207 segment → 114 ta subtitr).
- **Raqamlar qayta tekshirildi:** Whisper avval “52” deb eshitgan joylar audio bo‘laklarini o‘zbek, qozoq va turk modellari bilan qayta tanib, **57** (O‘zbekiston) va **59** (Qirg‘iziston) ekani aniqlandi. Subtitr va grafikalar shu raqamlarga moslandi.
- Tekshirish kerak bo‘lgan bitta joy: 3:56–4:00 (“…yanada aniqroq baholash rejalarini bayon qildi”). Audio noaniq, ma’no saqlangan holda yozildi. Kerak bo‘lsa `Subtitles.srt` da tahrirlang.

## Faktlar bo‘yicha eslatma
- Audiodagi raqamlar o‘zgartirilmadi.
- UZREPORT TV xabari (23.10.2026) Singapur 193 va Qozog‘iston 77 ni tasdiqlaydi.
- **Farq:** o‘sha xabardagi grafikada Qirg‘iziston **63** ta yo‘nalish bilan ko‘rsatilgan, audioda esa **59** deyilgan. Videoda audiodagi raqam turibdi. Joylashdan oldin henleyglobal.com da tekshirib ko‘rishni tavsiya qilaman.
- 75 → 74 → 82 dinamikasi ham audiodan olindi. UZREPORT sarlavhasida “9 pog‘ona pastladi” deyilgan, bu oraliqdagi boshqa nashrga nisbatan bo‘lishi mumkin.

## Autentiklik (critical failure tekshiruvi)
| Savol | Natija |
|---|---|
| Ko‘rsatilgan inson aynan audioda tilga olingan insonmi? | Ha. Shaxslar ekrandagi titr bilan tasdiqlangan (Mirziyoyev, To‘qayev, Brunner, Kaelin, Krol) |
| Joylar to‘g‘rimi? | Ha. Toshkent aeroporti (yozuvlar va Uzbekistan Airways bortlari), Berlaymont, Shengen chegaralari |
| Aloqasiz stock footage bormi? | Yo‘q |
| Har bir kadr aytilayotgan jumlaga mosmi? | Ha. 103 sahnaning har biri uchun asos `Storyboard.csv` da yozilgan |
| Har bir YouTube kadrida manba ko‘rsatilganmi? | Ha. 87 ta parchaning barchasida pastki o‘ng burchakda (split-screen’da har panelda alohida) |
| Uzun parchalar bormi? | Yo‘q. To‘liq ekran va split-screen parchalar 1.3–7.6 s, fon parchalari ≤4 s (loop, xira) |

**Montajdan oldin topilgan va tuzatilgan xatolar:**
1. Xukda (0:00) pasport o‘rniga MDH logotipi chiqayotgan edi → to‘g‘ri soniyaga ko‘chirildi.
2. “Shengen hududi” (0:41) jumlasida xarita o‘rniga bino ko‘rinayotgan edi → DW xaritasiga almashtirildi.
3. “Viza talab etiladi” (0:43) jumlasida avtomagistral ko‘rinayotgan edi → Council of the EU chegara posti kadriga almashtirildi.
4. “Iqtisodiyot?” (0:55) va moliyaviy holat (2:41) jumlalarida dollar o‘rniga poezd ko‘rinayotgan edi → dollar kadriga almashtirildi.
5. “Katta farq” (1:50) jumlasida boshlovchi ko‘rinayotgan edi → tipografiya kartochkasiga almashtirildi.
6. BBC O‘zbek kadrlaridagi inglizcha subtitrlar bizning subtitrlar bilan to‘qnashayotgan edi → kadrlar yuqoridan kesildi, uchta bo‘lak qayta render qilindi.

## Ma’lum cheklovlar
- 16 ta manba videosi snapyt.app’da faqat ≤480p sifatda mavjud edi. Ular 1080p ga lanczos bilan kattalashtirildi; Toshkent aeroporti ichki kadrlari va arxiv reportajlarida yumshoqlik sezilishi mumkin.
- Buyuk Britaniya va AQSh elchixonasi binosi uchun tekshirilgan kadr topilmadi (`Missing_Authentic_Footage.md`).
- Fair use kafolat emas: `Fair_Use_Assessment.md`.
