# Vulpitning yashil bolalari — cinematic vertikal video (Remotion)

Ovozli hikoya (10:38, o‘zbek tili) va 60 ta rasm asosida Remotion (React + TypeScript) yordamida montaj qilingan, ovozga so‘zma-so‘z sinxronlangan hujjatli video. Asosiy format — 16:9 (`Main`), xuddi shu montajning 9:16 varianti ham bor (`Vertical`).

| Parametr | Qiymat |
|---|---|
| Format | 1920 × 1080, 16:9, 30 fps (`Main`); 1080 × 1920, 9:16 (`Vertical`) |
| Kodek | H.264 (CRF 20) + AAC 192 kbps, MP4 |
| Davomiylik | 10:57 (19 724 kadr) = 16.4 s hook/sarlavha + 10:38.6 to‘liq ovoz + 2.5 s yakun |

## Papkalar

```
vulpit-video/
├── final_video.mp4          # yakuniy 16:9 render (gitda yo‘q, hajmi katta)
├── final_video_9x16.mp4     # 9:16 vertikal varianti (gitda yo‘q)
├── storyboard.json          # sahnalar, kadr vaqtlari, overlay-lar, SFX, musiqa rejasi
├── transcript.json          # transkript + har bir so‘zning start/end vaqti (forced alignment)
├── assets/
│   ├── images/              # ZIP’dagi 60 ta asl rasm
│   ├── 00_kadrlar_royxati.txt
│   ├── music/original_score.mp3   # shu loyiha uchun sintez qilingan original musiqa
│   └── sfx/*.wav            # sintez qilingan effektlar (boom, whoosh, riser, shimmer, bells, ...)
├── pipeline/                # tahlil va tayyorlov skriptlari (Python)
│   ├── transcript_corrected.json  # Whisper matni + qo‘lda tuzatilgan ASR xatolari
│   ├── whisper_*_raw.json         # Whisper’ning xom natijalari (taqqoslash uchun)
│   ├── align.py                   # MMS_FA forced alignment → so‘z vaqtlari
│   ├── build_storyboard.py        # storyboard, subtitr sahifalari, ducking egri chizig‘i
│   └── make_audio_assets.py       # original musiqa va SFX sintezi
└── remotion-project/        # Remotion manba kodi
    ├── src/Main.tsx               # sahnalar, o‘tishlar, audio qatlamlari
    ├── src/components/Scene.tsx   # virtual kamera: Ken Burns, parallax, slam, shake, desat, dim, flash
    ├── src/components/Subtitles.tsx  # so‘zma-so‘z kinetic subtitr
    ├── src/components/Overlays.tsx   # kinetic typography (sarlavha, sanagich, nomlar, nazariyalar, CTA)
    ├── src/components/Effects.tsx    # grading, vignette, film grain, chang zarralari, light leak
    └── public/                    # rang-grading qilingan rasmlar, fon blur’lari, fontlar, sfx, audio
```

## Qayta render qilish

```bash
cd remotion-project
npm install
# ovoz faylini joylashtiring (gitga qo‘yilmagan):
cp /yo‘l/samarqand-...wav public/audio/voice.wav
# musiqa WAV’ini mp3’dan tiklash (yoki pipeline/make_audio_assets.py bilan qayta sintez):
ffmpeg -i ../assets/music/original_score.mp3 -ar 44100 public/audio/music.wav

npm run studio      # brauzerda preview
npm run render            # 16:9  -> ../final_video.mp4
npm run render:vertical   # 9:16  -> ../final_video_9x16.mp4
npx remotion still Main kadr.jpg --frame=500   # bitta kadrni tekshirish
```

## Ishlov bosqichlari (qisqacha)

1. **Transkripsiya** — `faster-whisper` + o‘zbek tiliga fine-tune qilingan `whisper-large-v3-turbo` (CT2) modeli, ikki marta: butun fayl va pauzalar bo‘yicha ~10–18 s bo‘laklar. Ikkala natija solishtirilib, aniq ASR xatolari tuzatildi (masalan *Vulpid → Vulpit*, *qo‘rini → qo‘lini*, *tilla → tilda*, *ertaga → ertagi*, ismlar kadrlar ro‘yxatidagi yozuvga moslandi). Matnga yangi gap qo‘shilmadi.
2. **Forced alignment** — `torchaudio` MMS_FA (wav2vec2 CTC) bilan har bir so‘zning vaqti; o‘rtacha ishonch 0.77–0.93. Takrorlangan so‘zlar (*“Ke, keyingi…”*) transkriptda saqlangan, subtitrda yashirilgan.
3. **Hook** — videoning boshida ovozning ikkita eng kuchli jumlasi qayta ishlatildi (39 s: *“Bu bolalarning terisi yashil edi”* va 54–63 s: *“Sakkiz yuz yildan ko‘proq vaqt o‘tdi. Ammo bu bolalar kim…”*), keyin sarlavha va hikoya boshidan to‘liq, kesilmagan holda boshlanadi. Ovozning o‘zi o‘zgartirilmagan.
4. **Dramaturgiya** — HOOK → sarlavha → I Topilma → II Guvohlar → III Loviya siri → IV Yashil rang so‘nadi → V Qizning hikoyasi → VI Nazariyalar (1–5) → VII Begona yurtda (emotsional cho‘qqi) → VIII Siz-chi? (payoff) → CTA va yakun.
5. **Vizual** — 84 sahna, har biri aniq gap/so‘z vaqtidan boshlanadi (kesimlar nutqdan 0.25 s oldin). 60 rasmning barchasi ishlatilgan, yetishmagan joylarda mos rasmlar boshqa kompozitsiya bilan qayta ishlatilgan. Har bir rasm bir xil grading (S-curve, teal/amber split-tone, film-qora) bilan ishlangan.
6. **Musiqa va ovoz dizayni** — barcha musiqa va effektlar `make_audio_assets.py` orqali noldan sintez qilingan (D-minor drone, padlar, celesta, heartbeat puls) — uchinchi tomon litsenziyasi yo‘q. Musiqa 14 bo‘limli kayfiyat rejasi bo‘yicha o‘zgaradi; ovoz bor joyda kadrma-kadr ducking (−8.4 dB), fade-in/out. SFX: boom, whoosh, riser, shimmer, qo‘ng‘iroq (“qo‘ng‘iroqlarning ovozi” so‘zida), quyosh nuri flash, heartbeat, sub-drop.
