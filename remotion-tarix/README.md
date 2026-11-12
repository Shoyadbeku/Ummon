# Tarixiy hujjatli video shabloni (Remotion, YouTube 16:9)

1920×1080, 30 fps. Ovozga moslangan: rasmlar, subtitrlar (so‘zma-so‘z yonib boradi), yil belgilari, boblar va fon musiqasi.

## Nimalar bor
- **Intro** — sarlavha harflari animatsiyasi + oltin yorug‘lik o‘tishi (4 s)
- **Ken Burns** — har bir rasm 6 xil kamera harakatidan biri bilan sekin zoom/pan
- **Sahnalar orasida** yumshoq crossfade
- **Kinoplyonka effekti** — donadorlik, changlar, chiziqlar, vinyetka, iliq rang
- **Subtitrlar** — ovozdan Whisper orqali olingan so‘z vaqtlari bo‘yicha, aytilayotgan so‘z oltin rangda
- **Yil belgilari** — «1856», «1943»… raqamlar aylanib chiqadi
- **Bob sarlavhalari** — markazda chiqib, chap yuqoriga o‘tadi
- **Fon musiqasi** — o‘zimiz sintez qilgan (mualliflik huquqi muammosi yo‘q), ovoz paytida pasayadi
- **Outro** — kanal nomi + «Obuna bo‘ling»
- Pastda progress chizig‘i

### Motion graphics elementlari (`src/data/overlays.ts`)
Har bir element ovozdagi aniq gap/so‘zga bog‘langan — so‘z aytilgan zahoti chiqadi:

| Turi | Nima qiladi | Misol |
|---|---|---|
| `lowerThird` | Ism plashkasi (ism + lavozim) | Jorj Vestingauz · Sanoatchi |
| `location` | Xarita pini + koordinatalar yozuv mashinkasida | Smilyan, Xorvatiya |
| `stat` | Raqam sanab chiqadi + aylana progress | 3327 XONA, 86 YOSH, 300+ PATENT |
| `keyword` | Zarbali kalit so‘z, xromatik effekt, kamera silkinishi | «O‘LIM NURI», «NEGA?» |
| `stamp` | Rezina muhr urilishi | MAXFIY, FBI, TASDIQLANMADI |
| `versus` | Ikki tomonlama taqqoslash ekrani | Edison (DC) VS Tesla (AC) |
| `question` | Yakuniy savol kartasi (A/B) — izohlarga chorlaydi | |

Bob almashganda — **light leak** (iliq yorug‘lik chaqnashi). Har bir element o‘z **ovoz effekti** bilan
(`public/sfx`: whoosh, impact, stamp, pop — `scripts/make_sfx.py` bilan sintez qilingan).

## Ishga tushirish
```bash
npm install
npm start          # Remotion Studio — brauzerda ko‘rish/tahrirlash
npm run build      # out/video.mp4 ga render
```

## Yangi video uchun shablonni ishlatish
1. `public/voice.mp3` — o‘z ovozingiz; `public/images/01_....jpg … NN_....jpg` — rasmlar (nomi 2 xonali raqam bilan boshlanadi).
2. Ovozni matnga aylantirish (so‘z vaqtlari bilan):
   ```bash
   pip install faster-whisper
   ffmpeg -i public/voice.mp3 -ac 1 -ar 16000 /tmp/v16.wav
   python3 scripts/transcribe.py /tmp/v16.wav   # transcript.json yaratadi
   ```
3. `scripts/narration.txt` — transcript.json dagi har bir segment uchun **bitta qator** to‘g‘ri imloda matn (qatorlar soni segmentlar soniga teng bo‘lishi kerak).
4. `scripts/scene_map.txt` — `segment_raqami rasm_raqami`: qaysi gapdan qaysi rasm boshlanadi (rasm qayta ishlatilishi mumkin).
5. `python3 scripts/build_timeline.py transcript.json` → `src/data/scenes.json` va `src/data/subtitles.json`.
6. `src/config.ts` — sarlavha, kanal nomi, ranglar, musiqa balandligi, boblar va yil belgilari.
7. Musiqa: `python3 scripts/make_music.py <soniya> public/music.wav` (keyin mp3 ga) yoki o‘z musiqangizni `public/music.mp3` qilib qo‘ying.
