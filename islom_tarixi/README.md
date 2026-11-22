# Islom olami tarixi — 60 s kinematografik intro (4K)

**Tayyor video:**
- `ISLOM_OLAMI_TARIXI_4K.mp4` — 3840×2160, 30 kadr/s, aynan 60,0 s, HEVC (H.265, `hvc1`) ~11 Mbit/s + AAC 256 kbit/s, −14 LUFS.
- `ISLOM_OLAMI_TARIXI_1080p.mp4` — 1920×1080, H.264 — har qanday pleyer va telefonda ochiladi.

GitHub 100 MB dan katta faylni qabul qilmagani uchun 4K versiya HEVC da siqilgan. Siqilmagan master (H.264, CRF 14, ~620 MB) quyidagi buyruqlar bilan qayta yaratiladi.

Video AI-generator bilan emas, **kod bilan** yaratilgan: har bir kadr vaqtning sof funksiyasi sifatida brauzerda chiziladi (Canvas 2D motion graphics + three.js 3D sahnalar), so‘ng ffmpeg bilan yig‘iladi. Shuning uchun natija deterministik, matnlar va arab yozuvi buzilmaydi, tarixiy ma’lumotlar nazorat ostida.

- `SSENARIY.md` — storyboard, diktor matni vaqt kodlari bilan, ekrandagi har bir sana uchun tarixiy izoh, madaniy hurmat qoidalari.
- `AI_PROMPTLAR.md` — Veo / Kling / Runway / Sora uchun fotorealistik variant: 6 × 10 s prompt + montaj yo‘riqnomasi.

## Tuzilishi

```
render/
  index.html        shriftlar va sahifa
  main.js           kadr dispetcheri (vaqt → sahna) + post-ishlov
  core.js           effektlar: bloom, vinyetka, plyonka donadorligi, zarrachalar, 3D sarlavha, islomiy naqshlar
  scenes_a.js       01 globus + sarlavha · 02 cho‘l, tarixiy xarita, Bag‘dod «Doira shahar»
  scenes_b.js       03 Baytul Hikma, qo‘lyozma, usturlob · 05 sinus jadvali, osmon sferasi, bilim tarmog‘i
  scenes_3d.js      04 Kordova, Minorai Kalon, Samarqand · 06 Registon quyosh botishida (three.js)
  preview.js        tanlangan kadrlarni JPG qilib saqlash
  render.js         kadrlarni ffmpeg’ga uzatib MP4 yasash
  assets/           shriftlar (Cinzel, Cormorant Garamond, Amiri, Reem Kufi, Aref Ruqaa — OFL), three.js, Natural Earth geo-ma’lumotlari
audio/
  vo_matn.json      diktor matni va boshlanish vaqtlari
  tts.py            o‘zbekcha diktor ovozi (edge-tts, uz-UZ-SardorNeural)
  make_audio.py     musiqa + effektlar + ovoz miksi (faqat numpy) → mix.wav
```

## Qayta yaratish

Kerak: Node.js + Playwright (Chromium), Python 3 + numpy, ffmpeg, `pip install edge-tts`.

```bash
# 1) Diktor ovozi
cd audio
python3 tts.py
for f in vo/*.mp3; do ffmpeg -y -i $f -af "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse" -ar 48000 -ac 1 ${f%.mp3}.wav; done

# 2) Musiqa va miks
python3 make_audio.py

# 3) Video: 4K (scale=2), 4 ta parallel bo‘lak
cd ../render
for i in 0 1 2 3; do node render.js 2 $((i*450)) $((i*450+450)) c$i.mp4 & done; wait
printf "file 'c0.mp4'\nfile 'c1.mp4'\nfile 'c2.mp4'\nfile 'c3.mp4'\n" > list.txt
ffmpeg -f concat -safe 0 -i list.txt -i ../audio/mix.wav -c:v copy -c:a aac -b:a 256k -shortest ../ISLOM_OLAMI_TARIXI_4K.mp4
```

Tez ko‘rish: `node render.js 0.5 0 1800 preview.mp4` (960×540). Bitta kadr: `node preview.js out 1 7.6 25 58`.
