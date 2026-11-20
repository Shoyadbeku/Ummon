# Ilon Mask: ofisdan raketalargacha — 8:08 vertikal hujjatli video

Asl ovoz: `Neytron_yulduzining_aql_bovar_qilmas_og‘irligi_SadoStudio 13.wav` (mazmuni — Ilon Mask hayoti, 1995–2008).

| Fayl | Tavsif |
|---|---|
| `Final_Video.mp4` | 1080×1920, 30 fps, H.264/AAC, −14 LUFS (343 MB — repoga kirmaydi, alohida yuborilgan) |
| `Subtitles.srt` | O'zbekcha subtitrlar (videoga yozilmagan) |
| `data/script_uz.txt` | Vaqt kodli tuzatilgan transkripsiya |
| `remotion/` | Remotion + React + TypeScript loyiha (`src/timeline.ts` — montaj ro'yxati, `src/comps.tsx` — grafikalar) |
| `Media_Sources.md` | Har bir lavha/rasm, vaqt kodi va litsenziyasi |
| `Storyboard.md` | 184 kadr, vaqt kodlari |
| `Quality_Report.md` | Sifat tekshiruvi |
| `tools_*.py` | Media yuklash, kesish, hujjat generatsiyasi skriptlari |

## Qayta render
Media (`remotion/public/v`, 1.5 GB) repoda yo'q — `tools_mk_dl.py`, `tools_cut.py` va `media_raw/nasa/cuts.txt` bilan qayta yuklanadi.
```bash
cd remotion && npm install
npx remotion render src/index.ts Main out/render_raw.mp4 --codec=h264 --crf=19
```
