# Tahrirlanadigan loyiha (kod ko‘rinishida)

Video Premiere yoki DaVinci'da emas, kod bilan yig‘ilgan: har bir sahna, matn, xarita va kredit `scenes.py` faylida yozilgan. Matnni, vaqtni yoki kadrni o‘zgartirish uchun shu faylni tahrirlab, qayta render qilish yetarli.

| Fayl | Vazifasi |
|---|---|
| `scenes.py` | Storyboard: 51 sahna (vaqt, klip, `ss` boshlanish nuqtasi, tezlik, titrlar, kreditlar) |
| `gfx.py` | Grafika: lower third, kinetik matn, kredit yorlig‘i, xaritalar (Natural Earth), Ken Burns |
| `render.py` | Har bir sahnani `seg/NNN.mp4` ga render qiladi (ffmpeg + PIL). `python3 render.py 5,12 --force` faqat 5- va 12-sahnani qayta yasaydi |
| `audio.py` | Original fon musiqasi va effektlarni sintez qiladi (`aud/music.wav`, `aud/sfx.wav`) |
| `assemble.sh` | Sahnalarni birlashtirib, audio miksni qo‘shadi → `out/master.mp4` |
| `preview.py` | Har bir sahnadan bitta kadrni chiqaradi (tezkor tekshiruv uchun) |
| `transcribe.py` | Whisper large-v3 transkripsiyasi |
| `transcript_whisper.txt` | Whisperning tahrirlanmagan natijasi (tahrirlangan matn `../storyboard.md` faylida) |

Kerakli papkalar (repoga kiritilmagan, chunki ular katta hajmli va uchinchi tomon materiallari):
- `clips/`: Telegram'dan olingan videolar. Havolalar `../youtube_tavsif.txt` faylida.
- `img/`: Wikimedia fotolari va `meta.json` (shu yerdagi `img_meta.json`).
- `geo/countries.geojson`: Natural Earth 1:50m.
- `dl/audio.wav`: asl ovoz.

Ovozga ishlov berish zanjiri (ffmpeg): `highpass 70 Hz → afftdn → EQ (−1.5 dB @220 Hz, +2 dB @3.2 kHz) → deesser → compressor 2.5:1 → loudnorm` (ikki o‘tishda). Musiqa ovoz ostida sidechain bilan pasayadi. Yakuniy miks −13.9 LUFS, true peak −1.4 dBFS.
