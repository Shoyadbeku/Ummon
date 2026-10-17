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
- **Eksport**: subtitrlar kuydirilgan video (MP4 yoki WEBM, 720p/1080p), SRT, VTT, TXT. SRT import ham bor.

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
```

## Brauzerlar

Chrome, Edge va Safari (iOS/iPadOS 16.4+) ning so‘nggi versiyalari. Video eksport `MediaRecorder` orqali real vaqtda bajariladi, shuning uchun eksport video uzunligicha davom etadi.
