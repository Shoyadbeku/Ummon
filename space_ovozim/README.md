---
title: Ummon Ovozim
emoji: 🎙️
colorFrom: indigo
colorTo: pink
sdk: gradio
sdk_version: 6.31.0
python_version: "3.10"
app_file: app.py
pinned: false
---

# Ummon Ovozim

O'zbekcha matnni egasining OmniVoice klon ovozida o'qiydigan Hugging Face Space.
Ummon saytidagi `ovozim.html` sahifasi shu Space'ning `/ovozlashtirish` API'sini chaqiradi.

## Joylash (telefon brauzerida ham bo'ladi)

1. huggingface.co/new-space → nomi `ummon-ovozim`, SDK **Gradio**, Hardware **CPU basic (free)**, **Public** → Create Space.
2. Files → Add file → Upload files → 7 ta faylni tanlang: `app.py`, `uz_matn.py`, `ovoz_shifr.py`,
   `requirements.txt`, `packages.txt`, `README.md`, `ovoz.enc` → Commit.
3. Settings → Variables and secrets → **New secret**: nomi `PAROL`, qiymati ovoz shifrlangan parol.

`ovoz.enc` klon ovozning parol bilan shifrlangan nusxasi (`python ovoz_shifr.py shifrla ovoz.pt ovoz.enc PAROL`).
Space ochiq bo'lsa ham, parolsiz ovozni ochib ham, ishlatib ham bo'lmaydi.

Boshqa yo'l: `HF_TOKEN=... python deploy.py <egasi>/<space>` (yopiq repozitoriy + HF_TOKEN secret).

## API

```bash
curl -X POST https://<egasi>-<space>.hf.space/gradio_api/call/ovozlashtirish \
  -H 'Content-Type: application/json' \
  -d '{"data": ["Salom dunyo", 0.92, 0.35, false, ""]}'
# -> {"event_id": "..."}; natija: GET .../gradio_api/call/ovozlashtirish/<event_id>
```

Bepul CPU basic'da 10 soniyalik nutq taxminan 1–2 daqiqada tayyor bo'ladi. Space 48 soat ishlatilmasa uxlaydi,
keyingi birinchi so'rov uni uyg'otadi (bir necha daqiqa). Doim tez ishlashi uchun Space Settings'da GPU tanlang.

OmniVoice model og'irliklari CC-BY-NC litsenziyasida: faqat notijoriy foydalanish uchun.
