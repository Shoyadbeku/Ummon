# Ummon Shorts

O‘zbek tilidagi AI subtitrlar, shablonlar va qisqa videolar uchun veb-muharrir. Hammasi brauzerda ishlaydi: videolar hech qanday serverga yuborilmaydi.

## Imkoniyatlar

- **Video yuklash** (MP4, MOV, WEBM) yoki sudrab tashlash.
- **AI subtitr**: Whisper modeli (tiny / base / small) o‘zbek nutqini vaqtlari bilan matnga aylantiradi. Model birinchi marta Hugging Face'dan yuklanadi va brauzer keshida saqlanadi. WebGPU bo‘lsa tezroq ishlaydi.
- **Kamerada yozish**: brauzer qo‘llasa, subtitrlar yozish paytida jonli (`uz-UZ`) chiqadi.
- **Matndan video**: ssenariy yoziladi, subtitrlar o‘qish tezligi bo‘yicha joylashadi, fon gradient yoki rasm.
- **12 ta subtitr uslubi**: Karaoke, Pop, Belgilash, Klassik, Qutichali, Sarlavha, Neon, Mashinka, Minimal, Kino, Qo‘lyozma, Lenta.
- **8 ta video shabloni**: Reels hook, YouTube Shorts, Podkast klip, Instagram post, Dars, Mahsulot reklamasi, Kino iqtibos, Vlog.
- **Format**: 9:16, 1:1, 4:5, 16:9; to‘ldirish yoki xira fon bilan sig‘dirish; sarlavha (hook).
- **Lotin ⇄ Kirill** transliteratsiyasi.
- **Ovoz klon** (`ovoz.html`): Gemini 3.8 Flash TTS bilan ovozni 10–30 soniyalik namunadan klonlash va o‘zbekcha matnni shu ovozda o‘qitish. O‘z Gemini API kalitingiz kerak; so‘rovlar brauzerdan to‘g‘ridan-to‘g‘ri Google'ga boradi.
- **Eksport**: subtitrlar kuydirilgan video (MP4 yoki WEBM, 720p/1080p), SRT, VTT, TXT. SRT import ham bor.

## Colab (GPU)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/shoyadbeku/ummon/blob/main/colab.ipynb)

Whisper Colab GPU’sida ishlaydi, subtitrlar ffmpeg bilan videoga kuydiriladi. **Runtime → Run all** ni bosing va chiqqan `gradio.live` havolasini oching. 12 ta uslub, shablonlar, formatlar, lotin ⇄ kirill, MP4/SRT/VTT/TXT/ASS eksport. Kod: `colab/ummon_colab.py`; daftarni qayta yig‘ish: `python3 colab/build_notebook.py`.

## Ishga tushirish

ES modullar ishlatilgani uchun sahifani `file://` orqali emas, HTTP server orqali oching:

```bash
python3 -m http.server 8000
# http://localhost:8000
```

### GitHub Pages

`main` ga push qilinganda `.github/workflows/pages.yml` saytni avtomatik joylaydi. Bir marta yoqish kerak:
**Settings → Pages → Build and deployment → Source: GitHub Actions**.
Kamera va AI uchun HTTPS kerak, GitHub Pages buni beradi.

## Tuzilishi

```
index.html            sahifa va barcha ko‘rinishlar
css/style.css         dizayn
js/app.js             ilova mantiqi (ijro, subtitrlar, kamera, eksport)
js/render.js          kadrni canvasga chizish (ko‘rish va eksport uchun bir xil)
js/templates.js       subtitr uslublari, video shablonlari, fonlar
js/translit.js        lotin ⇄ kirill
js/whisper-worker.js  Whisper (transformers.js) Web Worker'da
ovoz.html             ovoz klonlash sahifasi
css/ovoz.css          ovoz sahifasi dizayni
js/ovoz.js            Gemini Voices API va TTS chaqiruvlari
```

## Brauzerlar

Chrome, Edge va Safari (iOS/iPadOS 16.4+) ning so‘nggi versiyalari. Video eksport `MediaRecorder` orqali real vaqtda bajariladi, shuning uchun eksport video uzunligicha davom etadi.

## Ovoz klon

1. [aistudio.google.com/apikey](https://aistudio.google.com/apikey) dan Gemini API kalitini oling.
2. 10–30 soniyalik ovoz namunasini yozing yoki yuklang.
3. O‘sha odam rozilik matnini (inglizcha yoki xitoycha) so‘zma-so‘z o‘qiydi. Bu Google talabi.
4. «Ovozni klonlash» tugmasini bosing. Ovoz ID si shu brauzerda saqlanadi.
5. Matn yozing va «Ovozlashtirish»ni bosing, natijani WAV qilib yuklab oling.

Ovoz klonlash Illinoys, Texas, Yevropa iqtisodiy hududi, Buyuk Britaniya, Shveytsariya va Hindistonda ishlamaydi.
