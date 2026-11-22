# Quality_Report — GTA tarixi (yakuniy tekshiruv)

## Texnik parametrlar (ffprobe / ebur128 bilan o‘lchangan)
| Parametr | Natija |
|---|---|
| Format | MP4, H.264 (yuv420p, CRF 20) + AAC 192 kbps, 48 kHz stereo |
| O‘lcham / FPS | 1080 × 1920 (9:16), 30 fps |
| Davomiylik | 11:49.1 (original ovoz: 11:49.06) |
| Fayl hajmi | 523 MB (~5.9 Mbps) |
| Loudness | −14.0 LUFS integrated, LRA 2.0 LU, true-peak −1.4 dBFS (YouTube/TikTok/Instagram normasi) |
| Qora kadrlar | `blackdetect` (≥0.3 s) — **topilmadi** |

## Ish jarayoni
1. **Audio tahlil** — iCloud’dan WAV (48 kHz mono, 11:49) yuklandi. Whisper large-v3 (so‘z vaqtlari bilan) transkripsiya qildi; VAD o‘tkazib yuborgan 3 ta joy (478–486 s, 503–516 s, 690–703 s) alohida qayta tanildi.
2. **Matn tuzatish** — Whisper o‘zbekcha matni xato bo‘lgani uchun 546 segment qo‘lda to‘g‘ri lotin imlosiga keltirildi (o‘/g‘, tutuq belgisi), noaniq joylar qayta tekshirildi (masalan “vrmin 1982 illar” = “1980-yillar”, “agar, rakiyan” = “okean”). So‘zlar Whisper vaqtlariga 1:1 yoki harf-proporsional moslandi → 1393 so‘z, 216 SRT kartochka.
3. **Ovoz tozalash** — highpass 75 Hz, FFT shovqin kamaytirish, EQ (−2.5 dB 250 Hz, +2.5 dB 3.2 kHz, havo +1.5 dB), de-esser, kompressor 3:1, ikki bosqichli loudnorm. Tembr o‘zgarmagan, sun’iy ovoz ishlatilmagan.
4. **Montaj** — 152 sahna, o‘rtacha kesim ~4.7 s (hook’da 1.3–1.8 s). 10 xil transition (zoom, whip + motion blur, flash, glitch/RGB, camera shake, blur-in, light leak), Ken Burns, card/parallax layout, color grade, film grain, vignette, progress bar.
5. **Motion graphics (Remotion)** — kinetic typography, 6 ta raqam counteri, yil shtamplari, 5 ta xarita animatsiyasi (Dandi, Nyu-York, Miami, Los Santos, Leonida), original piksel-shahar va 2D→3D o‘tish, split-screen (oddiy poyga vs qochish; orzu vs haqiqat), ikonka gridlari, 3 panelli qahramonlar, kiber-hujum terminali, treyler pleyer, chiqish sanalari kartasi, 1997–2026 taymlayn, yakuniy so‘rovnoma + CTA.
6. **Sound design** — 8 ta litsenziyali musiqa treki (bob bo‘yicha), ovozga avtomatik ducking (gap ostida −13 dB, pauzalarda −7 dB), 182 ta SFX (whoosh, impact, bass hit, riser, glitch, siren, coin…).

## QA checklist
| Savol | Natija |
|---|---|
| Footage audio mazmuniga mosmi? | ✅ har bir sahna aytilayotgan gapga bog‘langan (Storyboard.md da so‘zma-so‘z) |
| Subtitr vaqti to‘g‘rimi? | ✅ so‘z darajasida sinxron; faol so‘z sariq, kalit so‘zlar yashil |
| Motion graphics silliqmi? | ✅ spring/easing interpolyatsiya, 53 ta tekshiruv kadri ko‘rib chiqildi |
| Keraksiz qora ekranlar? | ✅ yo‘q (blackdetect) |
| Ovoz/musiqa balansi | ✅ musiqa ovozdan ~13–14 LU past, −14 LUFS |
| Vizual ritm | ✅ har 1–5 s da yangi kadr yoki grafika |
| Takrorlanish | ✅ 91 ta turli media; bitta klip ko‘pi bilan 3–4 marta, har safar boshqa joyidan/kadrda |
| Mobil o‘qiluvchanlik | ✅ subtitr 80–92 px, 14 px qora kontur; o‘ng tomondagi 150 px va pastki UI zonasi bo‘sh |
| Hook kuchlimi? | ✅ 0–8.7 s: 5 ta tez kesim, flash + impact, GTA VI logo reveal, glitch |

## Cheklovlar (ochiq aytiladi)
- **Haqiqiy GTA o‘yin kadrlari ishlatilmadi.** YouTube/X/VK/Rutube/Mover’dagi treyler va gameplay videolar Rockstar’ning mualliflik huquqi ostida, qayta foydalanishga ruxsat yo‘q. O‘rniga: litsenziyali stock footage (Mixkit), Wikimedia Commons rasmlari (DMA Design jamoasi, Dandi, Rockstar North, konsollar), Commons’dagi logotiplar va original grafikalar.
- Pexels va Pixabay serverlari bu muhitdan bloklangan (403) edi; Coverr/Videvo ishlatilmadi — barcha stock video Mixkit’dan.
- Mixkit’ning yangi kliplari faqat 720p da ochiq; ular asosan card-layout yoki yorug‘lik/abstrakt fonda ishlatilgan.
- 3 ta Commons rasm (Lemmings haykali, Tay ko‘prigidagi poyezd, Houser aka-ukalar) rate-limit sabab yuklanmadi va ishlatilmadi.
- 11:49 davomiylik — YouTube’da oddiy video (Shorts limiti 3 daqiqa), TikTok’da ≤10 daqiqa cheklovi bo‘lishi mumkin; Reels uchun ham uzun. Qisqa versiyalar kerak bo‘lsa, storyboard bo‘limlari bo‘yicha alohida render qilish oson.
- Ovozdagi faktlar (sotuvlar, sanalar va h.k.) ovozdagidek berildi; ekranga ovozda yo‘q yangi fakt qo‘shilmadi (faqat “Los-Anjeles asosida”, “Florida ilhomi” kabi xarita izohlari va mashhur SA kodlari namunasi).
