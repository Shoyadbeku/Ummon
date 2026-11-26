# assets

- `fonts/` — put .ttf/.otf files here to use your own typeface for credits/titles (otherwise
  DejaVu Sans / DejaVu Serif or system fonts are used). For Uzbek Latin "oʻ/gʻ" make sure the font
  has U+02BB / U+2018 glyphs (DejaVu, Noto Sans, Inter, Montserrat do).
- `music/` — background music. Mood keyword in the file name lets the builder pick it:
  `epic_*`, `dramatic_*`, `calm_*`, `solemn_*`, `tense_*`. `demo_epic_drone.mp3` is generated
  by the tool (CC0) for testing only.
- `sfx/` — sound effects, matched by name: `wind`, `impact`/`boom`/`whoosh`, `horses`, `marching`,
  `city_ambience`, `crowd_market`, `crowd_protest`, `battle_distant`, `swords`, `train`, `waves`,
  `river`, `page_turn`, `rumble`, `explosion`, `aircraft`, `tank`, `camel_bells`.
  The bundled ones are synthetic placeholders (CC0) — replace with real CC0 recordings
  (e.g. Freesound CC0, Pixabay sound effects) for production.
- `luts/` — `.cube` LUTs, use with `render.grade: "lut:name.cube"`.
