# Tarix — Remotion shabloni (YouTube 16:9)

Tarixiy hujjatli videolar uchun motion graphics shabloni: 1920×1080, 30 fps.
Barcha matnlar, sanalar, rasmlar, ranglar va davomiyliklar bitta props
obyektidan boshqariladi, shuning uchun kod yozmasdan Remotion Studio'da
tahrirlash mumkin.

Namuna ssenariy Amir Temur haqida (≈73 soniya).

## Ishga tushirish

```bash
cd tarix-remotion
npm install
npm run dev        # Remotion Studio: http://localhost:3000
npm run render     # out/tarix.mp4 (1080p, H.264)
npm run still      # out/thumbnail.png — muqova uchun kadr
```

Fontlar (Cinzel, Cormorant Garamond, Inter) `@fontsource` paketlaridan lokal
yuklanadi, shuning uchun render internetsiz ham ishlaydi va o‘zbek lotin
harflari (o‘, g‘, ʼ) to‘g‘ri chiqadi.

## Sahnalar

| `type`     | Nima qiladi |
|------------|-------------|
| `intro`    | Katta sarlavha, oltin bezak chiziqlar, fonda yillar sanog‘i (masalan 1336 → 1405) |
| `chapter`  | Bob sarlavhasi: rim raqami (I, II…), nom va sanalar |
| `person`   | Shaxs kartasi: portret, ism, yillar, lavozim va 2–4 ta fakt |
| `map`      | Yurish yo‘li: shaharlar uzunlik/kenglik bo‘yicha joylashadi, chiziq o‘zi chiziladi, kamera yo‘l boshiga ergashadi |
| `timeline` | Gorizontal xronologiya; voqealar ko‘p bo‘lsa kamera suriladi |
| `image`    | Arxiv rasmi Ken Burns harakati bilan (zoom in/out, pan), sana va pastki yozuv |
| `quote`    | Iqtibos so‘zma-so‘z paydo bo‘ladi, muallif va manba |
| `stats`    | Sanaluvchi raqamlar (o‘nlik kasr ham ishlaydi) |
| `outro`    | “Obuna bo‘ling” tugmasi va YouTube end screen elementlari uchun 2 ta joy |

Sahnalar tartibini o‘zgartirish, takrorlash yoki olib tashlash mumkin —
umumiy davomiylik avtomatik hisoblanadi (o‘tishlar ustma-ust tushishi
hisobga olinadi). Studio'dagi **Sahnalar** papkasida har bir sahnani alohida
ko‘rish mumkin.

## Tahrirlash

- **Matn va ssenariy:** `src/defaultProps.ts` yoki Studio'ning o‘ng
  panelidagi props muharriri.
- **Rasmlar:** faylni `public/` papkasiga qo‘ying va sahnaning `image`
  maydoniga nomini yozing (masalan `"bibixonim.jpg"`). `https://` manzil ham
  bo‘ladi. Bo‘sh qoldirilsa, shablon o‘rniga bezakli zaxira fon chizadi.
  Rasmlarga avtomatik yengil sepiya filtri beriladi.
- **Xarita:** `bounds` — ko‘rinadigan hudud (gradus), `points` — shaharlar
  ketma-ketligi (`lon`, `lat`, `label`). Haqiqiy geografik fon kerak bo‘lsa,
  xarita rasmini aynan shu `bounds` bo‘yicha (ekvidistant proyeksiya) qirqib
  `image` ga bering.
- **Ranglar:** `theme.accent` (oltin), `background`, `text`, `paper`.
- **O‘tishlar:** `transition`: `fade` | `slide` | `wipe` | `none`,
  `transitionSeconds` — davomiyligi.
- **Kino effekti:** `grain: true` — plyonka donadorligi va miltillash.
- **Suv belgisi:** `watermark` — o‘ng yuqori burchakdagi kanal nomi.

## Tuzilishi

```
src/
  index.ts           registerRoot
  Root.tsx           kompozitsiyalar (to‘liq video + har bir sahna)
  TarixVideo.tsx     sahnalarni o‘tishlar bilan ketma-ket qo‘yadi
  schema.ts          zod sxemasi (Studio muharriri shundan quriladi)
  defaultProps.ts    namuna ssenariy
  fonts.ts           lokal fontlar
  components/ui.tsx  umumiy elementlar: fon, chang, vinyetka, donadorlik,
                     bezak chiziq, so‘zma-so‘z matn, Ken Burns
  scenes/            har bir sahna turi
```

## Eslatma

Namuna ssenariydagi faktlar ommabop manbalarga asoslangan; o‘z videongiz
uchun sanalar va raqamlarni tekshirib chiqing. “Kuch — adolatdadir” iqtibosi
an’anaviy ravishda Amir Temurga nisbat beriladi.
