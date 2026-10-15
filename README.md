# Bitta kichkina narsa oldim 🎬

Matndan avtomatik **o'zbekcha dublyaj** (ochiq manbali TTS) → **Motion Canvas**
animatsiyasi (lab-sinxron stickman'lar + taglavhalar) → **MP4** video.

Tayyor video: [`video/bitta-kichkina-narsa.mp4`](video/bitta-kichkina-narsa.mp4)

## Tuzilma

| Fayl | Vazifasi |
|---|---|
| `tts/script.json` | Ssenariy: replikalar (kim, matn, effekt), pauzalar, ovoz effektlari |
| `tts/generate_audio.py` | TTS → `audio/audio.wav` + `src/data/timeline.json` (vaqtlar, lab-sinxron konverti, taglavhalar) |
| `src/scenes/scene.tsx` | Motion Canvas sahnasi |
| `src/project.ts` | Loyiha (audio ulangan) |
| `scripts/render.mjs` + `render.html` + `src/render.ts` | Headless render → `output/bitta-kichkina-narsa.mp4` |

## TTS haqida

* **Asosiy: Meta MMS-TTS** — `facebook/mms-tts-uzb-script_latin` (VITS). O'zbek tili uchun
  eng tabiiy eshitiladigan ochiq model. Bitta ovozdan 3 qahramon pitch-shift orqali farqlanadi.
  ⚠️ Model og'irliklari CC-BY-NC 4.0 litsenziyasida (notijorat foydalanish).
* **Zaxira: espeak-ng** (`uz` ovozi) — GPLv3, to'liq oflayn, lekin robotroq.

Skript `--backend auto` rejimida avval MMS'ni sinaydi, bo'lmasa espeak-ng'ga o'tadi.
Effektlar ffmpeg bilan: xotin ovozi "oshxonadan" (aks-sado), erning "Niyeeeet!"i
qutilar tagidan bo'g'iq. Eshik taqillashi, fura signali va qutilar ko'chkisi tovushlari
numpy bilan sintez qilinadi (tashqi fayl kerak emas).

## Ishga tushirish

```bash
# 1) bog'liqliklar
sudo apt install ffmpeg espeak-ng
pip install numpy torch transformers      # MMS uchun (ixtiyoriy, lekin tavsiya etiladi)
npm install

# 2) ovoz + timeline
python3 tts/generate_audio.py             # yoki --backend mms / --backend espeak

# 3) video
npm run render                            # -> output/bitta-kichkina-narsa.mp4
# yoki muharrirda ko'rish:
npm start                                 # http://localhost:9000
```

`npm run render` Chromium'ni Playwright orqali ishlatadi. Brauzer yo'li boshqa joyda bo'lsa:
`CHROMIUM_PATH=/path/to/chrome npm run render`.

Matnni o'zgartirish uchun faqat `tts/script.json` ni tahrirlang va 2–3 qadamlarni qayta
bajaring: barcha animatsiya vaqtlari, og'iz harakati va taglavhalar avtomatik moslashadi.
