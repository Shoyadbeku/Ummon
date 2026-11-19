# Shahzoda — haqiqiy ismi (Shorts / Reels / TikTok)

Yuklangan ovoz asosida Remotion (React + TypeScript) bilan yaratilgan 9:16 video.

## Natijalar — `deliverables/`

- `Final_Video.mp4` — 1080×1920, 30 fps, H.264 + AAC, 32 s, −14 LUFS
- `Subtitles.srt` — sinxron subtitrlar (oʻzbek lotin)
- `Storyboard.md` — transkripsiya, sahnalar va vaqt kodlari
- `Media_Sources.md` — barcha manbalar va litsenziyalar (**CC BY-SA attribution’ni tavsifga qoʻshing**)
- `Quality_Report.md` — sifat tekshiruvi va ochiq masalalar

## Tahrirlash va qayta render

```bash
npm install
npm run fetch-media   # Mixkit stock video/musiqa/SFX (git’da saqlanmaydi)
npm run studio        # Remotion Studio’da koʻrish/tahrirlash
npm run render        # out/Final_Video.mp4
```

Render qilingandan keyin loudness mastering:

```bash
ffmpeg -i out/Final_Video.mp4 -c:v copy -af "loudnorm=I=-14:TP=-1.0:LRA=9" -c:a aac -b:a 320k -movflags +faststart Final_Video.mp4
```

## Tuzilishi

- `src/data/timing.ts` — soʻz darajasidagi transkripsiya: matn, vaqt, rang. Subtitrlar va SRT shu yerdan olinadi.
- `src/Main.tsx` — sahnalar ketma-ketligi, overlay’lar va ovoz dizayni (SFX jadvali, musiqa ducking).
- `src/components/Graphics.tsx` — ID-karta, Oʻzbekiston xaritasi, globus, hisoblagich, grafik, timeline, split-screen, vinil CTA.
- `src/components/Captions.tsx` — Hormozi uslubidagi soʻzma-soʻz subtitrlar.
- `src/components/Overlays.tsx` — film grain, vignette, light leaks, flash, progress bar.
- `scripts/make_srt.py` — `Subtitles.srt` generatori.
