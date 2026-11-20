# MrBeast va haqiqiy Squid Game — Shorts / Reels / TikTok (Remotion)

9:16, 1080×1920, 30 fps, 38.4 s. Original ovoz asosida qurilgan, kesimlar so‘z vaqtlariga bog‘langan.

## Tayyor fayllar

| Fayl | Tavsif |
|---|---|
| `deliverables/Final_Video.mp4` | Yakuniy video (H.264 High, yuv420p BT.709, AAC 320k, −14 LUFS) |
| `deliverables/Subtitles.srt` | So‘z vaqtlari bo‘yicha sinxron subtitrlar (videoga kuydirilmagan) |
| `deliverables/Storyboard.md` | 21 sahna: vaqt kodlari, vizual, grafika, SFX |
| `deliverables/Media_Sources.md` | Barcha footage, rasm, musiqa, SFX manbalari va litsenziyalari |
| `deliverables/Quality_Report.md` | Yakuniy sifat nazorati |

## Loyihani ochish va qayta render qilish

```bash
npm install
./scripts/fetch_media.sh            # stock video/rasm/SFX/musiqani yuklab oladi (~520 MB)
npm run studio                      # Remotion Studio'da tahrirlash
npx remotion render src/index.ts Main out/render_raw.mp4 --codec=h264 --crf=16 --audio-codec=aac --audio-bitrate=320k
./scripts/master.sh                 # loudnorm −14 LUFS + yuv420p → out/Final_Video.mp4
```

## Tuzilishi

```
src/timeline.ts           so‘z vaqtlari, shot list, beat grid, SFX cue'lari — montajning "manbasi"
src/Main.tsx              21 sahna, audio mix (musiqa ducking), global qatlamlar
src/components/fx.tsx     Footage (Ken Burns, o‘tishlar, grading), kinetik matn, glitch, grain, light leak, shake
src/components/graphics.tsx  globus-xarita, 456 o‘yinchi infografikasi, byudjet bar chart, ID-karta,
                          blueprint, REC UI, pleyer UI, split-screen o‘lchagich, so‘rovnoma
src/media.ts              Commons rasmlari va muallif yozuvlari
public/audio/voice_clean.wav  tozalangan original ovoz
scripts/                  stills.mjs (tez tekshiruv), master.sh, fetch_media.sh
```

Matnni o‘zgartirish yoki kesim vaqtini surish uchun avval `src/timeline.ts`ni tahrirlang.
