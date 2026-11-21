# NewsBot — avtomatik yangiliklar video tizimi (Reels / Shorts / TikTok)

O'zbekiston va dunyo yangiliklarini topadi, baholaydi, tekshiradi, o'zbekcha ovozli professional
9:16 videoga aylantiradi va Instagram'ga joylaydi. Kuniga 5 slot (Asia/Tashkent):

| Vaqt | Yo'nalish |
|---|---|
| 09:00 | 🇺🇿 O'zbekistonning eng dolzarb yangiliklari |
| 12:00 | 🌍 Dunyoning eng muhim yangiliklari |
| 15:00 | 🌍 Dunyo bo'ylab trenddagi yangiliklar |
| 18:00 | 🇺🇿 O'zbekistondagi eng yangi xabarlar |
| 20:00 | 🇺🇿 Kechki yangiliklar |

## Arxitektura

```
 RSS (Kun, Gazeta, Daryo, UzA, BBC, Al Jazeera, Guardian, Euronews, Google News)
        │  pipeline/discover.py  — crawl + Viral Potential Score (0–100)
        ▼
 SQLite news history (data/newsbot.sqlite) — pipeline/db.py, dedupe.py (takrorlanishni aniqlash)
        ▼
 AI muharrir (Claude, rejalashtirilgan sessiya) — WebSearch bilan fact-check, tanlov,
        ssenariy → episodes/<id>/episode.json   (PRODUCTION_PROMPT.md)
        ▼
 pipeline/media.py  — Wikimedia Commons (faqat CC0 / CC BY / CC BY-SA), kreditlar DB'da
 pipeline/tts.py    — OmniVoice, doimiy ayol boshlovchi ovozi, raqamlar → so'z (uz_text.py),
                      gap/so'z vaqtlari, SRT
 pipeline/build.py  — render props, original sintez musiqa, Remotion render, texnik QC
 remotion/          — React/TypeScript motion graphics (intro, kinetic captions, Ken Burns,
                      statistik hisoblagich, joy belgisi, ro'yxat, lower third, ticker, progress, outro)
        ▼
 pipeline/publish_instagram.py — Graph API, resumable upload, approval yoki auto rejim
 pipeline/dashboard.py         — dashboard/index.html (jadval, trendlar, holat, litsenziyalar, xatolar)
```

## Buyruqlar (`newsbot/` ichida)

```
python3 -m pipeline.cli discover --region uz --hours 6
python3 -m pipeline.cli new 18:00 uz
python3 -m pipeline.cli media <id> "power lines winter" "electricity meter"
python3 -m pipeline.cli produce <id>          # ovoz + subtitr + render + QC
python3 -m pipeline.cli stage <id>            # Instagram'ga yuklab, e'lon qilmasdan sinash
python3 -m pipeline.cli publish <id> --confirm
python3 -m pipeline.cli dashboard
python3 -m pipeline.cli analytics
```

Har bir epizod papkasida: `episode.json` (ssenariy, manbalar, fact-check, viral score), `storyboard.md`,
`subtitles.srt`, `timings.json`, `media.json` (litsenziya/kredit), `qc.json`, `final.mp4`.

## O'rnatish (yangi server/konteyner)

```
pip install feedparser omnivoice soundfile
pip install --force-reinstall --no-deps torch torchaudio --index-url https://download.pytorch.org/whl/cpu
cd newsbot/remotion && npm install
mkdir -p ~/.config/newsbot && chmod 700 ~/.config/newsbot
# token: ~/.config/newsbot/ig_token (chmod 600)  yoki  IG_TOKEN muhit o'zgaruvchisi
```

Kerakli maxfiy ma'lumotlar (kodga YOZILMAYDI):
- `IG_TOKEN` — Meta System User token (`instagram_basic`, `instagram_content_publish`, ixtiyoriy `instagram_manage_insights`).
- `IG_USER_ID` — standart: @pomi.uz.
- YouTube / TikTok — hali ulanmagan (pastga qarang).

## Halollik: nima ishlaydi va nima ishlamaydi

| Qism | Holat |
|---|---|
| RSS discovery, viral score, dedupe, SQLite tarix | ✅ ishlaydi (jonli ma'lumotda sinalgan) |
| Fact-check | ✅ AI muharrir 2+ manba bilan qiladi; to'liq avtomatik "haqiqat detektori" emas |
| Media | ⚠️ faqat litsenziyasi toza manbalar. Real voqea kadrlari (X, Telegram, TV) ruxsatsiz olinmaydi. Mahalliy yangiliklar uchun Commons'da mos rasm ko'pincha kam |
| Ovoz | ✅ OmniVoice (CPU, ~1 daqiqa ovoz uchun 10–15 daqiqa). ⚠️ Litsenziya CC-BY-NC: monetizatsiya qilinadigan kanal uchun tijoriy TTS ga almashtirish kerak |
| Subtitr | ✅ gap darajasida aniq, so'z darajasida taqsimlangan (ASR emas) |
| Remotion render | ✅ 1080×1920, 30 fps, h264 + aac |
| Instagram nashr | ✅ ulanish va kvota tekshirilgan; approval rejimi standart |
| YouTube Shorts | ❌ ulanmagan (Google Cloud OAuth + audit kerak) |
| TikTok | ❌ ulanmagan (TikTok Content Posting API audit talab qiladi) |
| Animated maps | ⚠️ hozircha joy belgisi + bayroq; geo-xarita qatlami keyingi bosqich |
| Analytics | ⚠️ kod tayyor, `instagram_manage_insights` ruxsati bo'lsa ishlaydi |
| Server | ⚠️ bulut sessiya konteyneri vaqtinchalik: token/modellar qayta o'rnatilishi mumkin. Barqaror ish uchun doimiy VPS tavsiya etiladi |

Remotion litsenziyasi: jismoniy shaxs va ≤3 xodimli kompaniyalar uchun bepul.
