# Kim Chen Nam ishi — hujjatli video (Remotion)

16:9 · 1920×1080 · 30 fps · H.264/AAC YouTube hujjatli videosi. Asos — muallifning original o‘zbekcha ovozi (10:26).

## Tuzilishi

```
src/
  Documentary.tsx        asosiy kompozitsiya: sahnalar, subtitrlar, film effekti, audio, titrlar
  data/storyboard.ts     har bir jumla uchun sahna (vaqt, media, manba, izoh)
  data/sources.ts        ekrandagi manba yozuvlari va yakuniy titrlar
  data/subtitles.ts      so‘zma-so‘z vaqtli subtitrlar (tools/build_subs.py yaratadi)
  data/transcript_uz.txt tuzatilgan o‘zbekcha matn (Whisper segmentlariga mos qatorlar)
  components/            Media (Ken Burns), Overlays (manba, lower-third, grain), Graphics (xarita, oila daraxti, timeline, VX), Subtitles, Credits
public/media/            tekshirilgan rasm va video kadrlari (litsenziyalar: deliverables/Authentic_Media_Sources.csv)
tools/
  build_subs.py          Whisper JSON + tuzatilgan matn → subtitles.ts + Subtitles.srt
  score.py               original musiqa/SFX sintezi va ovoz bilan mikslash
  make_reports.py        Storyboard.csv va manbalar hisobotlarini storyboard’dan yaratadi
deliverables/            SRT, CSV va hisobotlar
```

## Qayta yaratish

```bash
npm install
# 1) ovozni tozalash (asl wav fayldan)
ffmpeg -i original.wav -af "highpass=f=70,afftdn=nr=6:nf=-45,equalizer=f=250:t=q:w=1.2:g=-1.5,equalizer=f=3500:t=q:w=1.5:g=1.5,deesser=i=0.3,acompressor=threshold=-18dB:ratio=2.5:attack=8:release=180:makeup=1,loudnorm=I=-16:TP=-1.5:LRA=8" -ar 48000 -ac 1 narration_clean.wav
# 2) musiqa + miks → public/audio/mix.wav (-14 LUFS)
python3 tools/score.py tools/score_events.json narration_clean.wav public/audio/mix.wav
# 3) subtitrlar va hisobotlar
python3 tools/build_subs.py tools/whisper_raw.json src/data/transcript_uz.txt src/data/subtitles.ts deliverables/Subtitles.srt 0.5
python3 tools/make_reports.py
# 4) render
npx remotion render src/index.ts Documentary out/Final_YouTube_Video_16x9.mp4
```

`remotion.config.ts` sandbox’dagi Chromium yo‘lini ko‘rsatadi; boshqa kompyuterda `setBrowserExecutable` qatorini o‘chiring.

## Tamoyillar
- Ekrandagi har bir odam — aynan audioda tilga olingan odam. Litsenziyali material topilmagan shaxslar (Kim Chen Nam, Siti Aisyah, Doan Thi Huong, Chan Son Tek) uchun begona odam emas, grafik ishlatilgan.
- Hujum lahzasi — "GRAFIK REKONSTRUKSIYA" deb belgilangan sxema, arxiv kadri sifatida ko‘rsatilmagan.
- Har bir uchinchi tomon materiali ustida manba va litsenziya yozuvi bor.
