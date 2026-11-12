# Ovozdan video: "4000 yil oldin ham kredit bo'lganmi?"

Ovoz yozuvi (11:18) asosida Lightricks LTX modeli bilan yaratilgan hujjatli video pipeline'i.

## Bosqichlar

1. **Transkripsiya** — `transcribe.py`: Whisper (medium) ovozni vaqt belgilari bilan matnga aylantiradi → `transcript.json`.
2. **Sahna rejasi** — `make_scenes.py`: matn mazmuniga qarab 109 ta sahna, har biri aniq gap boshida boshlanadi
   (Mesopotamiya → loy taxtachalar → Bobil/Hammurapi → Afina/Solon → Buyuk ipak yo'li/Samarqand → bugun) → `scenes.json`.
3. **Video generatsiya** — `gen_ltx.py`: har bir sahna uchun LTX-Video 2B distilled (0.9.8) bilan 704×416, 3–5 soniyalik klip.
   GPU'siz, CPU'da ishlaydi (klip boshiga ~2–4 daqiqa). Avval T5 barcha promptlarni kodlaydi, keyin xotiradan chiqariladi.
4. **Montaj** — `assemble.py`: kliplar gaplarga kadr aniqligida moslanadi (kerak bo'lsa silliq slow-motion),
   1920×1080 ga kattalashtiriladi, rang korreksiyasi, vinyetka, plyonka donadorligi, bob sarlavhalari,
   ovoz esa kompressiya va −14 LUFS ga normallashtiriladi.

```bash
python transcribe.py ovoz16k.wav transcript.json
python make_scenes.py scenes.json
python gen_ltx.py scenes.json clips --w 704 --h 416
python assemble.py scenes.json clips ovoz.wav final.mp4
```

## LTX-2 (19B) bilan

GPU (≥32 GB VRAM) bo'lsa, `scenes.json` dagi promptlarni https://github.com/Lightricks/LTX-2 pipeline'iga berib,
`clips/sXXX.mp4` nomlari bilan saqlang — `assemble.py` o'zgarishsiz ishlaydi va sifat yanada oshadi.
