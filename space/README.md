---
title: Ummon Matn Ovoz
emoji: 🎙️
colorFrom: indigo
colorTo: pink
sdk: gradio
sdk_version: 6.31.0
python_version: "3.10"
app_file: app.py
pinned: false
---

# Ummon: Matn → Ovoz

O'zbekcha matnni klonlangan ovozda o'qiydigan Hugging Face Space.

1. `edge-tts` o'zbekcha tayyor ovozda (Sardor yoki Madina) nutq yaratadi.
2. RVC v2 modeli (`myvoice.pth`) uni egasining ovoziga aylantiradi.

## Joylash

1. huggingface.co → **New Space** → SDK: **Gradio**, Hardware: **CPU basic (bepul)**.
2. Shu papkadagi `app.py`, `requirements.txt`, `packages.txt`, `README.md` fayllarini Space'ga yuklang.
3. Ovoz modelini ulang (ikki yo'ldan biri):
   - **Oson:** `.pth` faylni Space'ga `myvoice.pth` nomi bilan yuklang. Space ochiq bo'lsa, faylni har kim yuklab olishi mumkin.
   - **Xavfsiz:** faylni **yopiq** model repozitoriyga yuklang, Space **Settings → Variables and secrets** ga
     `MODEL_REPO` (masalan `Baxtbek97/myvoice-rvc`), `MODEL_FILE` (fayl nomi) va `HF_TOKEN` (read token) qo'shing.

## API

Ummon saytidagi `matn.html` sahifasi shu Space'ning `/ovozlashtirish` API'sini chaqiradi:

```bash
curl -X POST https://<egasi>-<space>.hf.space/call/ovozlashtirish \
  -H 'Content-Type: application/json' \
  -d '{"data": ["Salom dunyo", "Sardor (erkak)", 0, 0, 0.33]}'
# → {"event_id": "..."}; natija: GET .../call/ovozlashtirish/<event_id>
```
