# Remotion project — Murod Nazarov Shorts

Tahrirlanadigan manba loyiha (React + TypeScript + Remotion 4.0.545). Yakuniy video: `../Final_Video.mp4`.

## Tuzilishi

- `src/timeline.ts` — **barcha vaqtlar shu yerda**: so‘z darajasidagi transkripsiya vaqtlari, sahna kesimlari, SFX joylashuvi va balandligi.
- `src/Main.tsx` — 22 ta sahna, global qatlamlar (grain, light leak, flash), audio miks (ovoz, musiqa avtomatikasi, SFX).
- `src/components/core.tsx` — klip/foto kamera harakatlari, color grade, sahna kirish o‘tishlari, grain, shake.
- `src/components/type.tsx` — kinetik tipografiya: `KineticLine`, `Slam`, `WipeText`, `Counter`, `Chip`.
- `src/components/Globe.tsx` — 2.5D globus (d3-geo orthographic), pinlar, uchish yoyi va samolyot.
- `public/` — ovoz (tozalangan), Commons rasmlari, shriftlar, xarita ma'lumoti.

## Ishga tushirish

```bash
npm install
./prepare_media.sh      # Mixkit kliplari, musiqa va SFX ni yuklab, 9:16 ga kesadi
npm run studio          # Remotion Studio (preview va tahrir)
./master.sh             # render + -14 LUFS mastering -> out/Final_Video.mp4
```

Matnni yoki vaqtni o‘zgartirish uchun `src/timeline.ts` va `src/Main.tsx` dagi tegishli sahna komponentini tahrirlang.
