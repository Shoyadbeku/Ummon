# Kreml sukut saqlaydigan savollar — Remotion loyihasi

16:9, 1920×1080, 30 fps hujjatli video. Original ovoz asosida qurilgan.

## Tuzilishi
- `src/data/transcript.ts` — asl ovozning tozalangan matni (vaqt kodlari Whisper large-v3 dan).
- `src/data/scenes.tsx` — storyboard: har bir sahna audio vaqtiga bog‘langan, media va litsenziya yozuvi bilan.
- `src/components/Primitives.tsx` — video/foto kadrlar, lower third, holat belgilari, grain.
- `src/components/Cards.tsx` — hujjat kartalari, legenda, vaqt chizig‘i, split-screen, hisoblagich.
- `src/components/Subtitles.tsx` — subtitrlar.
- `src/fonts.ts` — Inter va Playfair Display (OFL), `public/fonts` dan.

## Ishga tushirish
```bash
npm install
bash scripts/fetch_media.sh /path/to/original_voice.wav   # media va ovozni qayta yig‘adi
npm run studio      # preview
npm run render      # out/Final_YouTube_Video_16x9.mp4
```
`public/media`, `public/audio`, `public/blur` gitga qo‘shilmagan (hajmi katta). `public/blur/*` — `public/media/*.jpg` ning 480px, blur 14, yorqinlik 0.38 nusxasi;
`public/fx/grain*.png` — 960×540 Gauss shovqin. Fon musiqasi va effektlar ffmpeg `sine`/`anoisesrc` bilan sintez qilingan (komanda `../Deliverables/Quality_Report.md` da).

## Holat ranglari
- yashil — rasmiy fakt
- sariq — jurnalistik surishtiruv
- qizil — tasdiqlanmagan da’vo
