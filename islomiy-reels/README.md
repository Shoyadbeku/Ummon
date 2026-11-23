# Islomiy Reels — "Qorun qissasi" (Remotion)

Ovozli yozuv asosida yaratilgan cinematic islomiy video, 16:9 (1920×1080, 30 fps).
Subtitr va captionlar yo'q — ekranda faqat oyat raqami ko'rsatkichi (sura + oyat) chiqadi, uni ham o'chirish mumkin.

## Tuzilishi

```
scripts/
  storyboard.py     # audio vaqtlariga bog'langan sahna rejasi (137 sahna)
  prep_assets.py    # kliplarni kesish, 16:9 reframe, yagona color grade, 30 fps
  synth_sfx.py      # ovoz effektlarini sintez qilish (tashqi namunasiz)
  make_docs.py      # SOURCES.md va EDIT_PLAN.md ni avtomatik yaratish
  data/             # litsenziya tekshiruvi natijalari
src/
  IslamicReel.tsx   # asosiy kompozitsiya (sahnalar + global grade/vignette/grain + audio)
  Shot.tsx          # bitta sahna: kamera harakati, o'tishlar, 2.5D parallax, effekt qatlamlari
  SoundDesign.tsx   # SFX vizual voqealarga avtomatik sinxronlanadi
  fx/               # EarthCracks, GoldenKeys, IslamicPattern, LightRays, Particles, VerseBadge ...
  timeline.json     # prep_assets.py natijasi
public/
  audio/voice_master.wav   # tozalangan va -14 LUFS'ga master qilingan ovoz
  sfx/  fonts/  images/  shots/
```

## Ishga tushirish

```bash
npm install
# xom materiallar: <raw>/mixkit/<id>.mp4, <raw>/wm/<key>.webm|jpg
python3 scripts/storyboard.py storyboard.json
python3 scripts/prep_assets.py storyboard.json <raw> public
python3 scripts/synth_sfx.py public/sfx
npx remotion studio                       # ko'rib chiqish
npx remotion render IslamicReel out/video.mp4 --crf=16
# oyat ko'rsatkichlarisiz:
npx remotion render IslamicReel out/video.mp4 --props='{"showVerseBadges":false}'
```

`public/shots/` (tayyorlangan kliplar, ~1–2 GB) repoga kiritilmagan — ularni `prep_assets.py` qayta yaratadi.

## Ovoz ishlovi
highpass 70 Hz → FFT denoise → EQ (−1.5 dB @180 Hz, +1.5 dB @3.2 kHz, +1 dB high shelf) → kompressor 2.2:1 → ikki bosqichli loudnorm (−14 LUFS, TP −1.5 dBTP).

Manbalar va litsenziyalar: [SOURCES.md](SOURCES.md) · Montaj rejasi: [EDIT_PLAN.md](EDIT_PLAN.md)
