# Kino-video: rasmlar + ovoz → jonli video

8 ta rasm va `voice.mp3` (48 s) asosida bepul **Wan 2.2 TI2V-5B** modeli bilan har bir rasm jonli sahnaga aylantiriladi. Keyin sahnalar ovozga moslab birlashtiriladi.

**Ishga tushirish (bepul Google Colab T4 GPU):**
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/shoyadbeku/ummon/blob/kino-video/kino/wan_kino.ipynb)

| Fayl | Vazifasi |
|---|---|
| `scenes.json` | Har bir sahna: rasm, ovozdagi vaqti, harakat prompti |
| `generate.py` | Rasm → 5 s video (Wan 2.2, 24 fps) |
| `assemble.py` | Ovozga moslash, 1080x1920, o'tishlar, rang, AAC ovoz |
| `wan_kino.ipynb` | Colab notebook (hammasini bir tugma bilan) |
