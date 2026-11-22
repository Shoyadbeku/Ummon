# Fotorealistik versiya uchun AI-video promptlar (6 × 10 s)

Repozitoriydagi `ISLOM_OLAMI_TARIXI_4K.mp4` kod bilan to‘liq render qilingan (three.js 3D + Canvas motion graphics). Agar Veo, Kling, Runway Gen-4, Sora, Hailuo yoki Luma kabi generatorda **fotorealistik** variant kerak bo‘lsa, quyidagi 6 ta ketma-ket 10 soniyalik promptdan foydalaning, so‘ng ularni `audio/mix.wav` ustiga montaj qiling: vaqtlar va diktor matni aynan shu saundtrekka mos.

Generatorlar inglizcha promptni yaxshiroq tushunadi, shuning uchun promptlar inglizcha. Matn/sarlavhalarni AI’ga chizdirmang (harflar buziladi) — ularni montajda qo‘shing yoki shu repozitoriydagi render qatlamidan oling.

## Umumiy uslub bloki (har bir promptning oxiriga qo‘shing)

```
Cinematic historical documentary, Netflix-grade opening title sequence, ultra-realistic, Unreal Engine 5 cinematic lighting, Octane-style global illumination, volumetric light, shallow depth of field, anamorphic lens, subtle film grain, smooth gimbal camera, color palette: turquoise, emerald green, deep navy blue and metallic gold, 16:9, 4K, 30fps. No people in close-up, no faces, no prophets depicted, no text, no letters, no watermarks.
```

## Negativ prompt (qo‘llab-quvvatlasa)

```
text, letters, captions, logos, watermark, distorted Arabic, fake calligraphy, faces, human figures in foreground, depiction of prophets, cartoon, low-poly, plastic look, oversaturated, flicker, morphing architecture, modern buildings, cars, power lines, anachronisms
```

---

### 01 · 00:00–00:10 — Epik kirish
```
Total darkness. Tiny golden dust particles drift in deep space. A luminous ancient Earth globe slowly emerges from the dark, oceans deep navy, continents dark emerald with thin glowing gold coastlines and a faint graticule. The camera pushes in dramatically toward the Arabian Peninsula; a warm golden light blooms from the Hejaz region and spreads gently across the land. In the final seconds, intricate golden Islamic geometric patterns (16-point rosette, eight-pointed khatam stars) draw themselves outward across the frame, leaving the center dark and empty for a title.
```

### 02 · 00:10–00:20 — Sivilizatsiyaning yuksalishi
```
Dawn over the Arabian desert: layered sand dunes with sharp crests catching golden sunlight, long blue shadows, a distant caravan of camels in silhouette walking along a ridge, the faint silhouette of a medieval walled city with domes and a minaret on the horizon, blowing sand particles. The camera tilts down and the landscape transforms into a tilted 3D antique map of the Mediterranean, Middle East and Central Asia, with glowing gold light trails travelling from Arabia toward Damascus, Egypt, Iraq, North Africa, al-Andalus and Transoxiana. The map then dives toward Baghdad and becomes an elegant top-down golden line drawing of a perfectly circular walled city with four gates and a central green dome, a river on its eastern side.
```

### 03 · 00:20–00:30 — Oltin asr
```
Interior of a grand medieval Islamic library (House of Wisdom, Baghdad): a long hall of pointed arches, tall wooden shelves filled with leather-bound manuscripts, hanging brass oil lamps, warm volumetric light beams from a round window with geometric wooden lattice, dust motes floating. The camera glides backward through the hall. Then macro shots: an illuminated parchment manuscript opens on a wooden reading stand, a page turns, an ink geometric diagram of a square divided into rectangles glows softly; a polished brass astrolabe rotates slowly in candlelight, its rete and engraved scales catching highlights. Shallow depth of field.
```

### 04 · 00:30–00:40 — Islomiy me’morchilik
```
Three seamless camera flights. (1) Inside the Great Mosque of Córdoba: a forest of marble columns with double-tier horseshoe arches with alternating red brick and white stone voussoirs, warm low light, polished floor reflections, the camera dollying down an aisle. (2) The Kalyan Minaret in Bukhara at dusk: a 45-metre tapering baked-brick tower covered in bands of geometric brick patterns and one turquoise glazed band, topped by a lantern with sixteen arches; the camera spirals upward along it against a deep blue sky with first stars and pink clouds. (3) A Timurid madrasa in Samarkand in bright golden-hour sun: a monumental pishtaq portal covered in blue, turquoise and white tile mosaic, a tiled iwan vault, flanking minarets and a ribbed turquoise melon dome on a tall drum; the camera flies toward the portal.
```

### 05 · 00:40–00:50 — Ilm va meros
```
Close-up of an aged parchment page with a ruled astronomical table and a gold-and-lapis illuminated rosette; the ink lifts off the page as thousands of golden particles that swirl and assemble into a rotating transparent celestial sphere with a golden ecliptic ring, glowing constellations and star points, floating mathematical diagrams and astronomical charts like elegant holograms. Then streams of light flow along curved paths across a dark navy space connecting glowing nodes from left to right, symbolizing the transmission of knowledge between civilizations, all converging into a single brilliant golden light that fills the frame.
```

### 06 · 00:50–01:00 — Buyuk final
```
From a golden light flash, reveal an epic panoramic view of the Registan ensemble in Samarkand at golden sunset: three monumental madrasas facing a square, tiled pishtaq portals, minarets, ribbed and smooth turquoise domes glowing in warm light, a dramatic sky of orange, pink and violet clouds. The camera slowly pulls back and rises, revealing the whole square. Intricate golden Islamic geometric patterns slowly form in the sky above the buildings, leaving the center clear for a title. The final second fades to a soft golden glow and then to black.
```

---

## Montaj

1. Har bir 10 s klipni ketma-ket qo‘ying (00:00, 00:10, … 00:50).
2. Sarlavhalar va ma’lumot kartalarini qo‘shing (matnlar `SSENARIY.md` da).
3. Ovoz: `audio/mix.wav` (musiqa + effektlar + diktor, 60,0 s, −14 LUFS).
4. ffmpeg bilan birlashtirish misoli:

```bash
ffmpeg -f concat -safe 0 -i klips.txt -i audio/mix.wav -c:v libx264 -crf 16 -pix_fmt yuv420p -c:a aac -b:a 256k -shortest yakuniy.mp4
```
