# Editing rules — cinematic historical documentary

The scene builder applies these automatically; use them when reviewing `timeline.json` or
when finishing the edit by hand in an NLE.

## Rhythm

| Narration mood | Avg shot | Transition into scene | Extras |
|---|---|---|---|
| dramatic (war, massacre, collapse) | 2.2–3.5 s | impact cut (white flash 0.12 s + zoom punch) | SFX hit, short shots, map with route |
| tense (army, protest) | 3–4.5 s | cut | marching / crowd ambience |
| epic (empire, independence) | 4–5.5 s | cut / dissolve | music swell, wide shots, maps |
| neutral | 4–5.5 s | cut or dissolve | |
| calm / solemn (architecture, death, science) | 5–7 s | dissolve 0.6 s | slow Ken Burns, parallax |
| new chapter | – | fade to black 0.6 s | chapter title (serif, animated tracking) |

- Cut on the narration: a new shot starts with a new idea, name or date.
- Snap cuts to music beats only within ±0.35 s; narration sync always wins.
- Never hold a still longer than 7 s; split into two moves (e.g. wide → detail).
- No shot repeats; if an archive film is reused, use a different time range.

## Techniques and when to use them

- **Impact cut ("udar montaj")**: on dates, turning points, "ammo/однако/however", deaths, battles.
  Pair with a low boom or whoosh, never more than ~1 per 30 s.
- **J-cut / L-cut**: archive clips with original sound start their audio 0.5 s before the picture
  (J) and let it ring 0.5 s after (L), mixed under the narration (−20 dB).
- **Ken Burns**: eased zoom 1.0→1.12 (or reverse) with gentle pan towards the subject; portraits
  and documents are never cropped — they use parallax (contain + blurred background).
- **Parallax (2.5D)**: blurred background drifting one way, sharp foreground the other way. True
  depth-layer parallax needs manual cut-outs (Photoshop/After Effects); the skill does a safe pseudo-parallax.
- **Smooth zoom on footage**: 1.00→1.06 over the shot to give static archive film life.
- **Historical map animation**: procedural schematic map with route, pulsing markers and labels.
  For real historical maps (Commons/LoC), the map image gets a slow "map zoom".
- **Kinetic typography**: date cards (large serif year, tracking animation) and chapter titles.
- **Lower thirds**: first appearance of a person: name + life dates + role, 5 s, left.
- **Subtitles**: burned in (configurable) + `subtitles.srt` for upload; ≤ 42 chars/line, 2 lines.
- **Film grain + vignette + grade** applied once on the whole video for a consistent look.
  Presets: `documentary_warm`, `cold_war`, `sepia_archive`, `bleach_bypass`, or `lut:file.cube`.
- **Sound design**: music ducked ≥10 dB under narration (side-chain), ambience beds per scene
  (wind, city, crowd, horses), SFX hits on impacts, final loudness −14 LUFS / −1 dBTP.

## Framing archive material

- 4:3 / portrait archive film: pillarbox with blurred, darkened copy behind (no stretching, no
  heavy crop of faces/subtitles).
- Do not colourise or upscale with AI and present it as original; if used, label it.
- Keep original black-and-white footage black-and-white (grade is subtle).
- Avoid burnt-in logos/watermarks of TV channels — usually a sign of a copyrighted source.

## Don'ts

- No effects for their own sake (no glitch, no spins, no 3D cubes).
- No fast cutting over solemn narration; no comedic SFX.
- No reconstruction/AI imagery without a visible "reconstruction" label.
- No footage from a different era/place presented as the narrated event.
