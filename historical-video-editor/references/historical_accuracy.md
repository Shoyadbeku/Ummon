# Historical accuracy checklist

## 1. What visual record can exist? (`media_era` in storyboard)

| Era | Years | Authentic visuals | Never claim |
|---|---|---|---|
| pre_photographic | < 1839 | manuscripts, miniatures (Zafarnama, Baburnama), paintings, coins, artefacts, architecture today (**labelled present day**), later engravings (label their date) | "archive footage", "photo of Timur" |
| early_photography | 1839–1894 | photographs (Turkestan Album 1871-72, Prokudin-Gorsky is 1905+), engravings | film footage |
| silent_film | 1895–1927 | newsreels, photos, B/W | sound, colour (except hand-tinted) |
| sound_film_bw | 1928–1949 | newsreels, documentaries (B/W) | colour footage without verification |
| color_film | 1950–1979 | colour and B/W film | |
| modern_video | 1980– | video, news agencies, official channels | |

The analyser adds `exclude_terms` (e.g. "film", "photo", "tank", "airplane" before they existed);
candidates containing them are down-ranked and flagged `anachronism`.

## 2. Per-shot checks

- **Place**: is it the narrated city/region? Uzbek monuments are frequently mislabelled
  (e.g. Shah-i-Zinda vs. Bibi-Khanym, Bukhara vs. Khiva) — check the title/description and the
  Commons category.
- **Time**: photo dates vs. event dates. A 1910 photo of Registan illustrates "Registan before
  restoration", not "Ulugh Beg's time" — say so in narration or credit (e.g. "Samarqand, 1910").
- **People**: portraits of medieval rulers are later artistic depictions — use "depiction",
  never "photo/portrait from life" in narration.
- **Uniforms, weapons, vehicles, flags**: must match the year (e.g. Soviet flags after 1922,
  T-34 tanks after 1940, Uzbek SSR flag versions).
- **Maps**: borders change; the schematic map shows points and routes only and is labelled.
- **Reconstructions & AI**: allowed only as illustration with a visible "reconstruction" label;
  never mixed into "archive footage" credits.
- **Re-enactments / feature films**: if a scene from a feature film is used (licensed), label
  it "feature film, YEAR" — never as documentary footage.

## 3. Facts in the script

- Cross-check dates and names with at least two reliable sources (encyclopaedias, academic
  works, museum catalogues). Note contested facts ("according to Ibn Arabshah...").
- Use established spellings per language: Amir Temur (uz) / Тимур (ru) / Timur, Tamerlane (en).
- Avoid present-day political claims inside historical narration unless sourced.

## 4. Before export

- Read `reports/license_report.md` and `reports/qc_report.md`.
- Watch the preview once fully with sound; check every lower third, date and credit.
