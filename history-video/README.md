# Meri Selest — tarixiy video (Remotion, YouTube 16:9)

1920×1080, 30 fps, ~12 daqiqa. Ovoz, 60 ta sahna rasmi, so'zma-so'z subtitrlar va fon musiqasi.

## Ishlatilgan RVE shablonlari
[reactvideoeditor/remotion-templates](https://github.com/reactvideoeditor/remotion-templates) dan olinib, tarixiy (sepia, oltin, serif) uslubga moslangan — `src/rve/`:

| Shablon | Qayerda |
|---|---|
| ken-burns | har bir rasm — 6 xil kamera harakati |
| cross-dissolve | sahnalar orasida silliq o'tish |
| film-burn | bob boshlanishi va dramatik joylarda yorug'lik chaqnashi |
| noise-grain + vignette-pulse | butun video bo'ylab eski kino donadorligi |
| letterbox-reveal | kino formatidagi qora chiziqlar, intro |
| cinematic-title-intro | "MERI SELEST" nomi (10-sahna) |
| chapter-title | I–VI boblar |
| typewriter-subtitle | sanalar (1872-yil 4-dekabr …) |
| lower-third | ismlar (Briggs, Morxaus, Solli-Flad, Konan Doyl) |
| stat-counter | raqamlar (1700+ bochka, 10 kishi, 6 oy …) |
| text-highlight | ovozga mos so'zma-so'z subtitr |
| subscribe-reminder | oxirida "Obuna bo'ling" |

## Ovozga moslash
`src/data/scenes.json` — har bir sahna va so'zning vaqti. Ovoz Whisper bilan tanib olinib, storyboard matni bilan tekislangan (1061 so'zdan 841 tasi to'g'ridan-to'g'ri mos tushgan, qolganlari oraliqda joylashtirilgan). Ovozda matnda yo'q qo'shimcha gaplar bor joylarda subtitr ko'rsatilmaydi.

Overleylar (sana, ism, raqam, bob) — `src/overlays.ts`, sahna raqami bo'yicha.

## Fon musiqasi
`public/music.mp3` — shu yerda dasturiy yaratilgan (mualliflik huquqisiz) qorong'u-sirli ambient: D-minor pad, past drone, okean shovqini, qo'ng'iroq notalari. Ovoz paytida pasaytirilgan (11%).

## Ishga tushirish
```bash
npm install
npm run studio   # brauzerda tahrirlash
npm run render   # out/meri_selest.mp4
```
Shriftlar: Cinzel, Playfair Display, Special Elite (OFL/Apache, `public/fonts/`).
