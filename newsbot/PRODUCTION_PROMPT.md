# NewsBot — har bir slot uchun ishlab chiqarish yo'riqnomasi (AI muharrir uchun)

Bu matnni rejalashtirilgan vazifa har slotda (09:00, 12:00, 15:00, 18:00, 20:00, Asia/Tashkent) ishga tushiradi.
Ish katalogi: `newsbot/`. Har bir buyruq `python3 -m pipeline.cli ...`.

## 0. Tayyorlik
- `python3 -m pipeline.cli slot` → qaysi slot va hudud (uz / world).
- Token: `~/.config/newsbot/ig_token` mavjudligini tekshir. Yo'q bo'lsa — nashrni o'tkazib yubor, adminni ogohlantir.
- Kerakli paketlar yo'q bo'lsa (yangi konteyner): `README.md` → "O'rnatish" bo'limidagi buyruqlar.

## 1. Discovery + Viral scoring
- `python3 -m pipeline.cli discover --region <uz|world> --hours 6` → nomzodlar va avtomatik ball.
- Qo'shimcha: WebSearch bilan so'nggi 1–6 soat ichidagi eng muhim voqealarni tekshir (uz: Kun.uz, Daryo, Gazeta, UzA, Spot, rasmiy saytlar; world: Reuters, AP, BBC, Al Jazeera, Guardian, Euronews, Bloomberg).
- Shou-biznes, mashhurlar hayoti, kino/serial va gossip — TANLANMAYDI.
- `duplicate_of` bo'lgan yangilikni faqat muhim YANGI tafsilot bo'lsa, "YANGILANISH" sifatida ol.

## 2. Fact-check (majburiy)
- Har bir raqam, ism, sana kamida 2 mustaqil ishonchli manbada (yoki 1 birlamchi rasmiy manbada) tasdiqlansin.
- Voqea sanasi ≠ maqola sanasi: `event_date` ni to'g'ri yoz.
- Qarama-qarshi ma'lumot bo'lsa — matnda ochiq ayt. Tasdiqlanmagan narsa fakt sifatida aytilmaydi.
- Ishonchli yangi yangilik topilmasa — slotni `skipped` qil, eski/soxta xabar bilan to'ldirma.

## 3. Ssenariy (episode.json)
- `python3 -m pipeline.cli new <slot> <region>` → `episodes/<id>/episode.json` ni to'ldir.
- 7–10 gap, 30–60 soniya. 1-gap = hook (original, clickbaitsiz). Gaplar qisqa, eshitishga qulay.
- Raqamlarni raqam bilan yoz (ovoz uchun avtomatik so'zga aylantiriladi). Chet nomlarni o'qilishiga qarab yoz.
- Har gapga: `highlight`, `media` (indeks), kerak bo'lsa `graphic` (stat/location/quote/list), `lower_third`.
- `fact_check` ro'yxatida har fakt manbasini qayd et. `viral_score` — taxmin, kafolat emas.

## 4. Media (huquqiy toza)
- `python3 -m pipeline.cli media <id> "inglizcha so'rov 1" "so'rov 2" ...` (Wikimedia Commons, CC0/CC BY/CC BY-SA).
- Kontakt varaqni ko'rib chiq: aloqasiz rasmlarni `media.json` da `"approved": false` qil.
- Ijtimoiy tarmoq/agentlik/TV kadrlari ruxsatsiz YUKLANMAYDI. Rasmiy press-foto faqat litsenziyasi aniq bo'lsa, qo'lda `media/` ga + `media.json` ga litsenziya bilan.
- AI-generatsiya qilingan tasvir haqiqiy kadr sifatida ko'rsatilmaydi.

## 5. Ishlab chiqarish
- `python3 -m pipeline.cli produce <id>` → ovoz (OmniVoice, ayol boshlovchi) + subtitr + Remotion render + texnik QC.
- `qc.json` ok=false bo'lsa — tuzat va qayta render qil.
- `contact_sheet.jpg` ni ko'rib, vizual QC qil (subtitr o'qiladimi, kadrlar mosmi).

## 6. Nashr
- NEWSBOT_PUBLISH_MODE=approval (standart): videoni adminga yubor, "joyla" deyilgandan keyin `publish <id> --confirm`.
- auto rejimda: QC o'tgan bo'lsa slot vaqtida `publish <id> --confirm`.
- So'ng: `python3 -m pipeline.cli dashboard`, kerak bo'lsa `analytics`.
