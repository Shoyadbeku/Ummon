# Radiy qizlari — Remotion montaj

`../radiy_qizlari_video.mp4` videosining manba kodi (1080×1920, 30 fps, 62 s).

- `src/Video.tsx` — hook, Ken Burns animatsiyalari, o'tishlar, karaoke subtitrlar, obuna tugmasi
- `public/scenes.json` — sahna/rasm vaqtlari, `public/words.json` — so'z vaqtlari (subtitr)
- `scripts/transcribe.py` — faster-whisper bilan ovozni matnga aylantirish
- `scripts/music.py` — fon musiqasi va SFX sintezi (ovoz ostida avtomatik pasayadi)

Katta fayllar repoga qo'yilmagan, render oldidan `public/` ga joylang:
`img/01.jpg … img/25.jpg` (1080×1936), `voice.wav`, `music.wav` (`scripts/music.py`), `grain0..7.png`.

```bash
npm i
npx remotion render src/index.ts RadiyQizlari out.mp4 --codec=h264 --crf=18
```
