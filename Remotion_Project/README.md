# And tog'lari mo'jizasi — Remotion loyihasi (1920×1080, 30 fps)

Original audio: `samarqand-yulduzlari-ostidagi-suhbat-oltin-suhandon-(maxsus) 2.wav` (13:33).

## Qayta yig'ish
1. **Transkripsiya** – `python3 scripts/tools/transcribe.py <16k f32 raw> out.json large-v3-turbo` (faster-whisper, uz). Natija: `scripts/whisper_transcript.json`.
2. **Footage** – `scripts/dl_list.txt` dagi YouTube ID'larni `scripts/tools/dl_all.sh` (snapyt.app + Playwright) bilan `<root>/YouTube_*/ID.mp4` ga yuklang.
3. **Kadrlar** – `python3 scripts/build_media.py <root>` → `public/media/sNNN.mp4` (har bir shot qisqa, ovozsiz 1080p parcha) + `src/data/timeline.json`.
4. **Ovoz** – `bash scripts/build_audio.sh <original.wav>` → `public/soundtrack.wav` (tozalangan ovoz + o'zimiz sintez qilgan ambient fon + o'tish effektlari, −16 LUFS).
5. **Render** – `npm run render` → `out/Final_YouTube_Video_16x9.mp4`.

Tahrirlash: `scripts/storyboard.py` (har bir gap uchun matn, kadrlar, crop, yozuvlar, grafika) → 3-qadamni qayta ishga tushiring. `npm run studio` – Remotion Studio.

Manbalar: `scripts/sources.py` (tekshirilgan) va `REJECTED` (rad etilganlar va sabablari).
