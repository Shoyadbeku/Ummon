# GTA tarixi — Remotion video loyihasi

Original o‘zbekcha ovoz asosida montaj qilingan 11:49 daqiqalik hujjatli video.
Remotion + React + TypeScript, 30 fps, H.264 + AAC.

- **`Main`** — asosiy versiya: 16:9, 1920×1080, subtitrlarsiz.
- **`Vertical`** — qo‘shimcha: 9:16, 1080×1920, so‘zma-so‘z subtitrlar bilan (Shorts/Reels/TikTok).

Barcha komponentlar kadr yo‘nalishiga qarab joylashuvni o‘zi moslaydi (`useLayout()` in `src/theme.ts`).

## Tuzilishi
```
src/storyboard.tsx      152 ta sahna: vaqt (ovozga sinxron), fon, motion graphics, transition, SFX
src/Main.tsx            kompozitsiya: sahnalar, o‘tishlar, subtitrlar, grain/vignette, progress bar, audio
src/components/
  Captions.tsx          so‘zma-so‘z subtitr (Hormozi uslubi, faol so‘z sariq, kalit so‘zlar yashil)
  Shot.tsx              video/rasm: Ken Burns, cover/card layout, color grade, klip uzunligiga avto-moslash
  Graphics.tsx          kinetic typography, counter, yil shtampi, bob kartasi, callout, ro‘yxat, iqtibos
  MapScene.tsx          Natural Earth xaritasi, zoom + pin animatsiya
  Scenes.tsx            piksel-shahar (2D→3D), logo reveal, split-screen, ikonka gridi, panellar,
                        kiber-hujum terminali, treyler pleyer, sanalar kartasi, taymlayn, so‘rovnoma
src/data/words.json     1393 so‘z: tuzatilgan matn + Whisper vaqtlari
scripts/mix.py          ovoz + musiqa (ducking) + SFX miksi → public/audio/final_mix.wav (-14 LUFS)
scripts/fetch_media.sh  Mixkit video/musiqa/SFX ni qayta yuklab olish (git’da saqlanmaydi)
scripts/docs.py         Storyboard.md generatsiyasi
deliverables/           Subtitles.srt, Storyboard.md, Media_Sources.md, Attribution.txt, Quality_Report.md
```

## Qayta render qilish
```bash
npm install
bash scripts/fetch_media.sh                 # Mixkit media (≈900 MB)
# ovoz: o‘z WAV faylingizni tozalab public/audio/voice_clean.wav ga qo‘ying (Quality_Report’dagi ffmpeg zanjiri)
python3 scripts/mix.py                      # public/audio/final_mix.wav
npx remotion studio src/index.ts            # tahrirlash/ko‘rish
npx remotion render src/index.ts Main out/Final_Video.mp4 --codec h264 --crf 20 --audio-codec aac        # 16:9
npx remotion render src/index.ts Vertical out/Final_Video_9x16.mp4 --codec h264 --crf 20 --audio-codec aac  # 9:16
```
Matn/vaqtni o‘zgartirish: `src/storyboard.tsx` dagi `t` (soniya) va matnlar; subtitr: `src/data/words.json`.
