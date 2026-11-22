# GTA tarixi — Remotion video loyihasi (9:16 Shorts/Reels/TikTok)

Original o‘zbekcha ovoz asosida avtomatik montaj qilingan 11:49 daqiqalik vertikal hujjatli video.
Remotion + React + TypeScript, 1080×1920, 30 fps, H.264 + AAC.

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
npx remotion render src/index.ts Main out/Final_Video.mp4 --codec h264 --crf 20 --audio-codec aac
```
Matn/vaqtni o‘zgartirish: `src/storyboard.tsx` dagi `t` (soniya) va matnlar; subtitr: `src/data/words.json`.
