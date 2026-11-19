# Ronaldo va yurak muammosi — Shorts / Reels / TikTok

Ovozli yozuv asosida yaratilgan 35 soniyalik vertikal video (1080×1920, 30 fps, H.264 + AAC).
Remotion + React + TypeScript loyihasi; musiqa va SFX noldan sintez qilingan.

| Fayl | Tavsif |
|---|---|
| `out/Final_Video.mp4` | Tayyor video |
| `docs/Subtitles.srt` | Sinxronlashtirilgan subtitrlar (videoga kuydirilmagan) |
| `docs/STORYBOARD.md` | Sahnalar va vaqt kodlari |
| `docs/MEDIA_SOURCES.md` | Manbalar, litsenziyalar, tavsif uchun kredit matni |
| `docs/QUALITY_REPORT.md` | Yakuniy sifat tekshiruvi |
| `src/` | Remotion kompozitsiyasi (`Main.tsx` sahnalar, `components/` grafikalar) |
| `audio/synth.py`, `audio/mix.sh` | Musiqa/SFX sintezi va ovoz miksi |

## Qayta render qilish

```bash
npm install
./scripts/fetch-clips.sh                      # Mixkit kliplari (git'da saqlanmaydi, 380 MB)
# ovozni o'zgartirsangiz:  (cd audio && python3 synth.py . && ./mix.sh /path/to/voice.wav ../public)
npm run studio                                # Remotion Studio'da tahrirlash
npx remotion render Main out/Final_Video.mp4 --codec=h264 --audio-codec=aac --crf=16
```

Bu muhitda Chrome headless shell oldindan o'rnatilgan: `--browser-executable=/opt/pw-browsers/chromium_headless_shell`.

Vaqtlarni o'zgartirish: `src/timeline.ts` (sahna chegaralari va yurak urishlari) — urishlar `audio/synth.py` dagilar bilan bir xil bo'lishi kerak.
