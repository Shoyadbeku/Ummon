# 🍚 “Ovqat sovidi, surat hali tayyor emas!” — Remotion motion-design video

Remotion (React + TypeScript) bilan yaratilgan, ovozga sinxronlanadigan kinetik tipografiyali
tushuntirish videosi. **1920×1080, 60 fps, H.264 MP4.**

Tayyor video: [`out/palov-video-github.mp4`](out/palov-video-github.mp4) (CRF 20, 55 MB; to‘liq sifat CRF 16 uchun `npm run render`)

## Tez boshlash

```bash
npm install
npm run dev        # Remotion Studio — jonli ko‘rish va tahrirlash
npm run render     # out/palov-video.mp4 (1080p, 60fps, CRF 16, x264 slow)
npm run render:shorts  # out/palov-shorts.mp4 — vertikal 1080×1920 (Shorts / Reels / TikTok)
npm run assets     # qaysi ovoz/rasm bor, qaysi yo‘q + taymlayn hisob-kitobi
```

## Ish jarayoni

1. **Ssenariy** — `src/data/script.ts`. Har bir sahna matni bo‘laklarga (segment) bo‘lingan,
   ajratib ko‘rsatiladigan so‘zlar, rang, o‘tish turi, TTS ohangi va AI rasm prompti shu yerda.
2. **Ovoz (voiceover)**
   - Gemini TTS: `.env` ga `GEMINI_API_KEY` yozing → `npm run voiceover`
     (`--force` — qayta yaratish, `--only=04-stop` — bitta sahna).
   - ElevenLabs: `.env` ga `ELEVENLABS_API_KEY` va `ELEVENLABS_VOICE_ID` → `npm run voiceover:eleven`.
     Har bir gapning ovozdagi aniq vaqti (`public/voiceover/<id>.json`) ham saqlanadi —
     kinetik matn ovozga kadrma-kadr sinxron chiqadi.
   - Yoki o‘z yozuvingiz / boshqa TTS: `public/voiceover/<sahna-id>.mp3|wav` qilib qo‘ying.
3. **AI rasmlar** — `public/images/<sahna-id>.jpg` (qo‘shimcha kadrlar: `<sahna-id>-2.jpg`, `-3.jpg` …).
   Rasm topilgan sahna avtomatik **rasmli rejimga** o‘tadi (`src/scenes/photo/PhotoScenes.tsx`):
   oq stiker chegarali karta, Ken Burns/zoom kamera, xiralashgan parallaks fon, kinetik subtitr paneli,
   personaj avatarlari, bug‘, flash, chiplar. Rasm bo‘lmasa — vektor illyustratsiyali sahna chiqadi.
   Yangi rasmlar uchun promptlar (2D cartoon cutout, sticker outline uslubi): `npm run assets -- --prompts`.
   Personaj avatarlari `public/avatars/` da (rasmlardan kesib olingan), ro‘yxat: `src/components/media/characters.ts`.
4. **Fon musiqasi (ixtiyoriy)** — `public/music/background.mp3`.
5. `npm run render`.

## Ovozga sinxronlash qanday ishlaydi

`src/lib/timeline.ts` dagi `calculateMetadata`:

- `getStaticFiles()` orqali har bir sahna uchun ovoz va rasm faylini topadi;
- ovoz davomiyligini `getAudioDurationInSeconds()` bilan o‘qiydi (ovoz bo‘lmasa — matn uzunligidan taxmin qiladi);
- sahna davomiyligi = `0.45s pauza + nutq + 0.55s pauza + o‘tish (30 kadr)`, lekin `minSeconds` dan kam emas;
- umumiy video uzunligini o‘tishlar qoplamasini hisobga olib qaytaradi.

Sahna ichida `useSegmentWindows()` har bir matn bo‘lagi nutqning qaysi qismida aytilishini
belgilar soniga proporsional hisoblaydi; `KineticText` so‘zlarni shu oynada ketma-ket chiqaradi.
Ya’ni ovoz faylini almashtirsangiz — sahnalar, so‘zlar va o‘tishlar avtomatik qayta moslashadi.

## Loyiha tuzilmasi

```
src/
├── index.ts                    registerRoot
├── Root.tsx                    <Composition> (1920×1080, 60fps, calculateMetadata)
├── Composition.tsx             TransitionSeries, ovoz treklari, fon, HUD
├── data/script.ts              ssenariy, ranglar, o‘tishlar, AI promptlar
├── lib/
│   ├── timeline.ts             ovoz → taymlayn hisoblash
│   ├── scene-context.tsx       sahna konteksti + segment vaqt oynalari
│   ├── anim.ts                 spring/interpolate yordamchilari, shake, float
│   └── theme.ts                lokal shriftlar (Montserrat, Inter), palitra
├── components/
│   ├── background/AnimatedBackground.tsx   gradient bloblar, texno-to‘r, parallaks shakllar, grain
│   ├── text/KineticText.tsx                so‘zma-so‘z kinetik tipografiya (rise/pop/slam)
│   ├── media/PhotoStage.tsx                rasm kartasi: Ken Burns, kamera zoom, rasm almashuvi, parallaks
│   ├── media/characters.ts                 personaj avatarlari
│   ├── text/Caption.tsx                    kinetik subtitr paneli
│   ├── media/HeroVisual.tsx                AI rasm (Ken Burns) yoki vektor zaxira
│   └── visuals/                            PlovPlate, Steam, Phone, Viewfinder, Chip, Thermometer...
├── scenes/Scene01Hook.tsx … Scene10Question.tsx   vektor rejim
└── scenes/photo/PhotoScenes.tsx                  rasmli rejim (10 sahna)
scripts/
├── generate-voiceover.ts       Gemini TTS → public/voiceover/*.wav
└── assets-status.ts            aktivlar holati va taymlayn jadvali
public/
├── fonts/                      Montserrat, Inter (SIL OFL)
├── images/                     AI rasmlar (sahna-id bo‘yicha)
├── avatars/                    personaj avatarlari
├── voiceover/  music/
```

## Sahnalar

| # | Sahna | Asosiy animatsiya | O‘tish |
|---|---|---|---|
| 01 | Hook | “slam” sarlavha, kamera silkinishi, telefon + flash | push-cut |
| 02 | Fotosessiya | 3D telefon, parallaks karta va chiplar | slide |
| 03 | Issiq palov | lagan, prosedural bug‘, uchib keluvchi qoshiqlar, harorat hisoblagichi | wipe |
| 04 | To‘xtanglar! | qizil puls, halqa to‘lqini, ✋, gap pufagi | iris |
| 05 | Fotosessiya boshlandi | viewfinder, burchak almashuvi (tepadan → yondan → zoom → selfi), flash | slide-up |
| 06 | Palov soviyapti | termometr 92°→24°, bug‘ so‘nadi, sovuq rang, qor | flip |
| 07 | Palov pasporti | 3D flip pasport, maydonlar, “TASDIQLANDI” muhri | clock-wipe |
| 08 | Joylandi | yuklash paneli, layklar hisoblagichi, uchuvchi yuraklar, 🥶 | fade |
| 09 | Eng yaxshi filtr | iliq nur, filtr karuseli “Bug‘ ♨️” | push-cut |
| 10 | Savol | VS so‘rovnoma kartalari, CTA | — |

## Render sozlamalari

`remotion.config.ts`: JPEG 95 kadrlar, H.264, `yuv420p`, CRF 16. `npm run render` qo‘shimcha
ravishda `--x264-preset=slow` va AAC 192k audio ishlatadi. Tezkor ko‘rish uchun `npm run render:fast` (540p).

Agar Remotion Chrome Headless Shell’ni yuklab ololmasa (yopiq tarmoq), mavjud brauzerni ko‘rsating:
`npx remotion render ... --browser-executable=/path/to/chrome`.
