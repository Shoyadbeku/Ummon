# Saudiya shahzodasining qorong‘i sirlari — YouTube hujjatli video (16:9)

Asl audio: `Neytron_yulduzining_aql_bovar_qilmas_og‘irligi_SadoStudio.wav` (iCloud). Fayl nomi "neytron yulduzi" bo'lsa ham, audio mazmuni **Muhammad bin Salmon, 2017-yildagi Ritz-Carlton hibslari va Jamol Xashoggi qotilligi** haqida. Video shu mazmunga moslab qurilgan. Papka nomi asl fayl nomidan qolgan.

## Fayllar

| Fayl | Tavsif |
|---|---|
| `Final_YouTube_Video_16x9.mp4` | 1920×1080, 30 fps, H.264 + AAC 320k, 11:45. Hajmi katta bo'lgani uchun git'da emas: alohida yuborilgan |
| `Subtitles.srt` | Asl ovoz bilan sinxron o'zbekcha subtitrlar (343 qator) |
| `Storyboard.csv` | 115 sahna: vaqt kodi, asl nutq, media, ekrandagi matn, kamera harakati, litsenziya |
| `Authentic_Media_Sources.csv` | Har bir media uchun shaxs yoki voqea, asl URL, haqiqiylik dalili, litsenziya va ishlatilgan vaqtlar |
| `Quality_Report.md` | Texnik, faktologik va sinxronizatsiya QC hisoboti |
| `Missing_Authentic_Footage.md` | Topilmagan materiallar va ularning o'rniga qo'llangan halol yechimlar |
| `Remotion_Project/` | React + TypeScript manba kodi |

## Qayta render qilish

```bash
cd Remotion_Project
npm install
npm run studio   # brauzerda tahrirlash
npm run render   # out/Final_YouTube_Video_16x9.mp4
```

Sahnalar `src/data/storyboard.json`, subtitrlar `src/data/subtitles.json` faylida. Vizual komponentlar `src/components/` ichida.
