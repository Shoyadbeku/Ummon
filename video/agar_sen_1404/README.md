# "Agar sen...?" — 1404-yil, Samarqand

Ovozli hikoya asosida yig‘ilgan 5 daqiqalik video (`agar_sen_1404.mp4`) uchun pipeline.

1. `scripts/transcribe.py` — faster-whisper (medium) bilan so‘z vaqtlari.
2. `scripts/align.py` — asl matn (`text.txt`) so‘zlarini audio vaqtiga moslash.
3. `scripts/scenes.json` → `scripts/fsd_batch.py` — FastSD CPU (OpenVINO, `rupeshs/LCM-dreamshaper-v7-openvino`, 4 qadam, 768×448) bilan 60 ta sahna rasmi; `upscale.py` ularni 1920×1120 ga kattalashtiradi.
4. `scripts/timeline.py` — 6.5 s hook + sahnalar, subtitrlar, davr kartalari (`remotion/timeline.json`).
5. `remotion/src` — Remotion montaji: Ken Burns harakati, o‘tishlar, davr ranglari (1404 iliq, 1980 sepiya, 1950 oq-qora), zarralar, kino donadorligi, karaoke subtitrlar, hook va yakuniy titr.
6. `scripts/make_music.py`, `scripts/sfx.py`, `scripts/mix.sh` — sintez qilingan fon musiqasi (hijoz ladi, dutor tusidagi chertmalar, doira), effektlar va ovozga moslab pasaytirilgan (sidechain) mix.
