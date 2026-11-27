# Ormuz inqirozi — yangiliklar reportaji (Remotion loyihasi)

Ovozli matn (`original_audio.wav`, 5:39.6) asosida yig‘ilgan 16:9, 1920×1080, 30 fps yangiliklar/tahlil videosi.

## Tuzilishi

```
hormuz_video/
├── public/
│   ├── audio/            original_audio.wav, voice_clean.wav, final_mix.wav
│   ├── x_footage/        X postlaridan yuklangan 22 ta video (+ .info.json)
│   ├── youtube_footage/  snapyt.app orqali yuklangan 23 ta YouTube video (+ .snapyt.json)
│   ├── shots/            storyboard bo‘yicha kesilgan 84 ta kadr (1920×1080, 30 fps)
│   ├── music/            original fon musiqasi (sintez, litsenziya muammosi yo‘q)
│   └── sfx/              original SFX (whoosh, impact, riser, tick, glitch, hit)
├── src/
│   ├── compositions/Hormuz.tsx   asosiy kompozitsiya (kadrlar, Ken Burns, o‘tishlar, kreditlar)
│   ├── components/               Graphics / Charts / Maps / theme
│   └── data/storyboard.json      tools/storyboard.py dan yaratiladi
├── tools/
│   ├── storyboard.py     YAGONA MANBA: kadrlar, grafikalar, SFX vaqtlari va manbalar
│   ├── cut_shots.py      kadrlarni kesish + rang korreksiyasi
│   ├── synth_audio.py    fon musiqasi va SFX sintezi
│   ├── mix_audio.py      ovoz + musiqa (sidechain ducking) + SFX, −14 LUFS
│   ├── transcript.py     tahrirlangan transkripsiya va SRT
│   ├── reports.py        manba hisobotlari (CSV)
│   └── sheet.sh          videodan vaqt belgili kadr varag‘i
└── deliverables/         hisobotlar, subtitr, YouTube description
```

## Qayta yig‘ish

```bash
npm install
python3 tools/storyboard.py          # storyboard.json
python3 tools/cut_shots.py           # public/shots/*.mp4  (manba videolar kerak)
python3 tools/synth_audio.py 340     # musiqa + SFX
python3 tools/mix_audio.py           # public/audio/final_mix.wav
npx remotion studio src/index.ts     # ko‘rib chiqish / tahrirlash
npx remotion render src/index.ts Hormuz out/video_noaudio.mp4 --codec=h264 --crf=16
ffmpeg -i out/video_noaudio.mp4 -i public/audio/final_mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest out/hormuz_final.mp4
```

Kadrni almashtirish uchun `tools/storyboard.py` dagi `SHOTS` ro‘yxatida manba kodini/boshlanish soniyasini o‘zgartiring, so‘ng `cut_shots.py` (o‘sha kadr faylini o‘chirib) va render’ni qayta ishga tushiring.

Katta media fayllar (`public/x_footage`, `public/youtube_footage`, `public/shots`, `out/`) mualliflik huquqi va GitHub hajm cheklovi sababli repozitoriyga qo‘shilmagan; ular `tools/` skriptlari va hisobotlardagi havolalar orqali qayta yuklab olinadi.
