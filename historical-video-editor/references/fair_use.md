# Copyright, Fair Use and YouTube — operating rules

> Not legal advice. These are conservative production rules the skill enforces in code
> (`scripts/licenses.py`, `verify_license.py`, `download_media.py`, `quality_check.py`).

## 1. Core facts the skill must respect

1. **Fair use is a defence, not a permission.** It is decided case by case (US 17 U.S.C. §107:
   purpose/character, nature of the work, amount used, market effect). It does not stop a
   Content ID match, a manual claim or a takedown. Other countries (Uzbekistan, Russia, EU)
   have narrower "quotation"/"citation" exceptions, not US-style fair use.
2. **Attribution is not a licence.** Writing "Source: X" never makes copyrighted footage legal.
   Credits are an obligation *on top of* a valid licence.
3. **"Found on the internet" ≠ public domain.** Uploads on YouTube, VK, Rutube, X, Facebook,
   Reddit, Telegram, Mover.uz are copyrighted by default (standard licence), often by someone
   other than the uploader.
4. **Public-domain status depends on jurisdiction and date.** US federal works (NARA, NASA, US
   Army) are PD in the US; works published in the US before 1930 are PD in the US (rolling date: 95 years);
   Soviet-era works may still be protected in Russia (life + 70, with wartime extensions).
   Prefer items whose archive explicitly states "Public Domain", "No known restrictions" or CC0.
5. **Never** try to defeat Content ID (mirroring, pitch shifting, cropping, speed changes,
   frames, overlays used to hide a match). The skill contains no such features.

## 2. Licence risk scale used by the skill

| Risk | Licences | Default action |
|---|---|---|
| 0 | Public Domain, PD Mark, CC0, "no known restrictions", NoC rights statements | use, credit archive anyway |
| 1 | CC BY, Pexels, Pixabay, Mixkit licences, written permission | use + credit (author, licence) |
| 2 | CC BY-SA, GFDL | use + credit; note share-alike in description |
| 3 | CC BY-NC / NC-SA (monetized channel), CC BY-ND, editorial only | blocked by default |
| 4 | unknown, all rights reserved, standard YouTube/VK/Rutube licence | blocked; discovery only |

`config.yaml → licensing.max_allowed_risk` (default 2). `channel_monetized: false` lowers NC to 2
for non-commercial channels — still check the work's terms. ND forbids edits (Ken Burns/cropping
already modify), so ND stays blocked.

## 3. Short copyrighted excerpts (opt-in only)

`licensing.allow_fair_use_clips: true` lets platform videos with unknown/standard licence through
as **`fair_use_review`** items, limited to `fair_use_max_clip_sec` (default 6 s). Conditions:

- the excerpt is the *subject* of commentary in the narration (you analyse that specific
  footage, e.g. a famous newsreel), not decorative B-roll;
- no open-licence alternative exists (the skill looks for one first);
- minimal amount, on-screen credit, original transformative narration;
- a human reviews every such clip (QC shows a ⚠️ until reviewed) and accepts the risk of a claim.

## 4. What makes the video transformative (do this every time)

- Original script with analysis, context, chronology and conclusions — not a re-narration of
  someone else's documentary.
- Footage illustrates *your* argument; many sources combined; maps, timelines, date cards,
  lower thirds and commentary add new meaning.
- Never upload long unaltered stretches of a single third-party film.

## 5. Platform terms

- YouTube ToS forbid downloading except through YouTube-provided features or with permission.
  The skill downloads YouTube videos only when YouTube itself marks them **Creative Commons
  Attribution** (Data API `videoLicense=creativeCommon` or `license` field in metadata), or when the
  user documents permission in `manual_urls.txt`.
- Pexels/Pixabay/Mixkit: free use, attribution appreciated, but do not sell unaltered copies and
  do not imply endorsement by people shown.
- Wikimedia Commons: every file has its own licence; check the file page, not Wikipedia.
- Museums: The Met Open Access (CC0) and Smithsonian Open Access (CC0) only for objects marked
  as such; other museum images may be restricted.

## 6. Credits format (on screen and in description)

On screen (bottom-right, small, faded): `Source: Wikimedia Commons / Author, CC BY-SA 4.0`,
`Manba: Internet Archive, Public Domain`, `Archive footage: Library of Congress`,
`Source: X / @username`, `Источник: Europeana / Bundesarchiv`.

In the description and `reports/SOURCES.md`: title, author, source archive, licence name + URL,
original page URL, and where it is used in the video. CC BY-SA requires noting modifications
("cropped, colour graded, animated") — the description template states this generally.

## 7. If a claim arrives

1. Check `reports/sources.csv` for the timecode → asset → licence evidence.
2. If the licence is valid (PD/CC), dispute with the evidence (original page, licence URL).
3. If not, replace the clip (`timeline.json` → re-render that clip with `video_editor.py --only cXXXX`).
