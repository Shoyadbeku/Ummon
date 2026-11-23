# Sifat hisoboti: "And tog'lari mo'jizasi"

## Texnik ko'rsatkichlar (ffprobe / ebur128 bilan o'lchangan)
| Parametr | Natija |
|---|---|
| Format | MP4, H.264 (CRF 18), AAC 320 kbit/s, 48 kHz stereo |
| O'lcham | **1920×1080, 16:9, gorizontal**, 30 fps |
| Davomiylik | 13:33.35 (original audio 13:33.31) |
| Hajm / bitreyt | 768.5 MB / ~7.6 Mbit/s |
| Ovoz balandligi | **−15.8 LUFS** integrated (YouTube uchun mos), true-peak ≤ −1.5 dBTP |
| Ovoz/fon nisbati | Nutq vaqtida fon nutqdan ≈ 28 dB past (sidechain ducking) |
| Qora kadrlar | Bo'sh qora ekran yo'q. 3 ta qisqa qorong'i joy (0:56 – 0.3 s, 10:34 – 0.7 s, 11:27 – 0.7 s) manba kadrlarining o'zida (tungi/qorong'i kadr) |

## Audio
- Original ovozingiz **so'zma-so'z va vaqt bo'yicha o'zgartirilmagan**. Qo'llanganlar: high-pass, shovqinni kamaytirish (afftdn), EQ, kompressor, de-esser, loudness normalizatsiya.
- Fon musiqasi uchinchi tomondan olinmagan. Litsenziya muammosi bo'lmasligi uchun past chastotali ambient fon va shamol shovqini shu yerda sintez qilindi. Bobga o'tishlarda yumshoq "whoosh + bass hit" effekti bor.
- YouTube kadrlarining o'z ovozi butunlay o'chirilgan.

## Transkripsiya va subtitrlar
- Whisper large-v3-turbo (uz) bilan har bir so'zga timestamp olindi (962 segment). Whisper o'zbekchani xato yozgani uchun barcha 78 jumla qo'lda tuzatildi. Ismlar: Roberto Kanessa, Fernando Parrado, Antonio Vizintin, Serxio Katalan, Xuan Antonio Bayona, Pirs Pol Rid.
- 188 subtitr; har bir jumla Whisper bergan boshlanish/tugash vaqtiga bog'langan. Jumla ichidagi qatorlar matn uzunligiga qarab taqsimlangan, shuning uchun ±0.5 s farq bo'lishi mumkin.
- Bob sarlavhasi ekranda katta yozuv bilan chiqqanda subtitr yashiriladi (takrorlanmasligi uchun).
- **Tekshirish kerak:** audioda 4 joyda (2:52, 5:20, 7:21, 12:05) Whisper "History plus", "National Geographic Plus", "PBS Plus" kabi so'zlarni eshitdi. Ular bo'lim boshlanishiga to'g'ri keladi va ehtimol jingl yoki Whisper xatosi. Bu so'zlar subtitrga qo'shilmadi; o'sha joylarda bob kartochkalari bor. Iltimos, tinglab tasdiqlang.
- Audiodagi sonlar o'zgartirilmadi (masalan, "o'n birinchi kuni" va qurbonlar taqsimoti audioda qanday aytilgan bo'lsa, shunday ko'rsatildi).

## Vizual autentiklik tekshiruvi
- 33 ta yuklab olingan videoning har biri contact sheet orqali kadrma-kadr ko'rib chiqildi. 172 ta shotning har biri kesilgandan keyin alohida QC sheetda yana tekshirildi.
- Tekshiruv natijasida tuzatilganlar: noto'g'ri shaxs tushgan kadr (s040: CGTN intervyusidagi boshqa ayol → yosh Kanessa fotosi), "Subscribe" stikeri va kanal logotiplari (crop), suratlar orasidagi effektli o'tishlar, noto'g'ri sarlavha (xat Parradoning Katalanga yozgan xati emas, "omon qolganlar yozgan xatlardan biri" deb tuzatildi).
- Rad etilgan: AI-illyustratsiyali video (K_gKRCtlwfc), zamonaviy Old Christians o'yini (1972 jamoasi emas).
- Har bir kadrda yuqori o'ng burchakda manba (ARXIV/INTERVYU/JOY • kanal) ko'rsatilgan. Arxiv kadrlarida sana/joy yozuvi bor. Bugungi kadrlar "bugun" deb belgilangan. Bir xil turdagi samolyot "bir xil turdagi" deb yozilgan.
- 4:3 va vertikal manbalar cho'zilmagan: asl nisbat saqlangan, yonlar shu kadrning blur qilingan nusxasi bilan to'ldirilgan.

## 14-bo'limdagi 20 ta savol bo'yicha xulosa
1–9 (shaxs, voqea, joy, sana, autentiklik, aloqasiz footage): ✅ tekshirildi (yuqoriga qarang).
6, 19 (foydalanish huquqi): ⚠️ litsenziya **yo'q**. Fair-use parchalar sizning ko'rsatmangiz bilan ishlatildi (`YouTube_Download_Report.md`).
10 (subtitr sinxroni): ✅ jumla darajasida.
11–16 (animatsiya, balans, 16:9, sifat, qora ekran, hujjatli uslub): ✅. 1972 arxivi manbada 240–480p bo'lgani uchun yumshoq ko'rinadi.
17–18, 20 (YouTube moslik, manbaga bog'lanish, yetarli qidiruv): ✅ 29 so'rov, 187 video ko'rib chiqildi, 29 ta ishlatildi, hammasi CSVda.

## Ma'lum cheklovlar
- Wikimedia Commons ochiq litsenziyali fotolari bu serverdan rate limit (HTTP 429) sababli olinmadi.
- Montaj tahlili kadrlar va vaqt kodlari bo'yicha qilindi. Videoni men o'zim real vaqtda ko'rib-eshitib chiqa olmadim. Yuklashdan oldin bir marta to'liq ko'rib chiqishingizni tavsiya qilaman.
