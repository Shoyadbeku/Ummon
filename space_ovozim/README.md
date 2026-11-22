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

## Joylash

`python deploy.py <egasi>/<space-nomi>` (HF write token kerak, `HF_TOKEN` muhit o'zgaruvchisida):

1. Klon ovoz (`voice_design/ovozlar/mening_ovozim.pt`) **yopiq** model repozitoriyga yuklanadi.
2. Space yaratiladi, `app.py`, `uz_matn.py`, `requirements.txt`, `packages.txt`, `README.md` yuklanadi.
3. Space'ga `VOICE_REPO` o'zgaruvchisi va `HF_TOKEN` secret qo'shiladi. `--parol` berilsa, `PAROL` secret ham qo'shiladi.

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
