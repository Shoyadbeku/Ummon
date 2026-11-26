---
name: historical-video-editor
description: Builds cinematic historical documentary videos for YouTube from a topic, script or narration. Analyses the script into scenes, searches archive footage, photos, paintings and maps on many platforms (Internet Archive, Wikimedia Commons, Library of Congress, Europeana, museums, Openverse, Pexels, Pixabay, YouTube CC, Yandex/Google Images, Rutube, VK, Reddit, X/Facebook/Mover.uz via manual URLs) in Uzbek, Russian and English, verifies licences and original sources, downloads only permitted material, edits it with FFmpeg (Ken Burns, parallax, map animation, impact cuts, J/L cuts, beat sync, grading, grain), burns source credits on screen, mixes narration/music/SFX to -14 LUFS, exports H.264/H.265 MP4 and writes full source/licence reports and a YouTube description. Use when the user asks for a historical / archival / documentary video, "tarixiy video", "hujjatli film", "arxiv kadrlar bilan montaj", "исторический ролик", or automatic editing with source attribution.
---

# Historical Video Editor

Turns `{tarixiy_mavzu}` + `{ssenariy}` (text or narration audio) + `{video_davomiyligi}` into a
YouTube-ready **Cinematic Historical Documentary** MP4 with on-screen source credits, a
sources/licence report and a ready-to-paste YouTube description.

Everything runs locally with Python 3.10+ and FFmpeg. Scripts live in `scripts/`, every step
is a standalone CLI and `scripts/run_pipeline.py` chains all 17 steps.

## When to use

- The user wants a history / archive / documentary video, or B-roll for a historical narration.
- The user gives a topic, a script (`.txt`/`.md`), a narration audio file, or all three.
- The user asks to find historical footage/images with sources and licences.

Do **not** use it to re-upload someone else's video, to strip watermarks or to evade Content ID.

## Inputs → how to map them

| Input | Where it goes |
|---|---|
| `{tarixiy_mavzu}` topic | `--title` (also used for fallback queries) |
| `{ssenariy}` script text | save to `<project>/script.txt` → `--script` |
| narration audio | `--narration file.mp3` (timing taken from audio; word-level with faster-whisper if installed) |
| `{video_davomiyligi}` | `--duration SECONDS` (only when there is no narration audio) |
| language | `--lang uz|ru|en` (narration + on-screen text) |
| `{montaj_dasturi}` | FFmpeg render is built in; `timeline.json` + `overlays.ass` + `subtitles.srt` can be rebuilt in Premiere/DaVinci/CapCut by hand (see README "NLE hand-off") |

If the user only gives a topic, **write the script first** (factual, sourced, 130–140 words per
minute of target length, `# Chapter` headings, optional `*[Vizual: ...]*` notes) and show it
to the user before searching.

## Workflow (follow in order)

0. **Setup check** — `ffmpeg -version`, `python -c "import requests,yaml,PIL,numpy"`,
   `pip install -r requirements.txt` if needed. Copy `.env.example` → `.env`; keys are optional.
   Run `python scripts/check_env.py` to see which providers are active. Tell the user which
   integrations are unavailable (missing key, blocked network) — never pretend they ran.
1. **Analyse** — `python scripts/analyze_script.py --script S --title T [--narration A] [--duration D] [--lang uz]`
   → `output/<slug>/storyboard.json` (scenes, periods, places, persons, terms, mood,
   emphasis, effects, sfx, multilingual queries, anachronism exclusions, director notes).
2. **Review the storyboard yourself (AI step, important).** Open `storyboard.json` and improve it:
   - fix periods/places the gazetteer missed (`scripts/data/lexicon.json` covers Central Asia,
     Middle East, Europe, USSR …; add entries when useful);
   - add better English/Russian/Uzbek queries per scene (archive vocabulary: "newsreel",
     "кинохроника", "miniature", "Zafarnama", museum object names, exact event names);
   - translate `director_notes` into concrete queries;
   - for `media_era: pre_photographic` scenes plan art, manuscripts, artefacts, maps and
     **labelled present-day** location footage — never fake "archive film";
   - keep `review_required: false` once done. Read `references/historical_accuracy.md`.
3. *(optional)* **TTS narration** if no audio: `python scripts/audio_editor.py tts --project SLUG`
   (edge-tts, `uz-UZ-SardorNeural`/`uz-UZ-MadinaNeural`, re-times scenes to real speech).
4. **Search video** — `python scripts/search_videos.py --project SLUG` (providers from config,
   cached, parallel, multilingual). **Search images** — `python scripts/search_images.py --project SLUG`.
   Platforms without API access get links in `reports/manual_search_links.md`; if you (the agent)
   have a web browser/search tool, use it to inspect those platforms and put verified URLs into
   `<project>/manual_urls.txt` (`URL | license=... | author=@... | scene=s003`).
5. **Verify** — `python scripts/verify_license.py --project SLUG` → `verified.json`,
   `reports/license_report.md`. Read the report; for Yandex/Google hits confirm the original
   page. Do not lower `licensing.max_allowed_risk` silently; ask the user.
6. **Download** — `python scripts/download_media.py --project SLUG` (approved only; long films are
   excerpted; duplicates removed by perceptual hash; shot cuts detected).
7. **Music beats** *(if `assets/music` has a track)* — `python scripts/audio_editor.py beats --project SLUG`.
8. **Build timeline** — `python scripts/scene_builder.py --project SLUG` → `timeline.json`.
   Check `visual_ratio_achieved` and `scenes_missing_visuals`; if scenes lack material, go back to
   step 4 with better queries instead of accepting fallback cards.
9. **Overlays** — `python scripts/source_overlay.py --project SLUG` (credits, lower thirds, date
   cards, chapter titles, subtitles → `render/overlays.ass`, `render/subtitles.srt`).
10. **Render** — `python scripts/video_editor.py --project SLUG --preview` first (960×540, fast),
    look at frames (`ffmpeg -i ... -vf "fps=1/5,scale=480:-2,tile=4x4" sheet.jpg`), then full res.
11. **Mix** — `python scripts/audio_editor.py mix --project SLUG` (ducking, J/L cuts, -14 LUFS).
12. **Export** — `python scripts/export_video.py --project SLUG [--4k] [--codec libx265]`.
13. **QC** — `python scripts/quality_check.py --project SLUG`; fix every ❌, report ⚠️ to the user.
14. **Deliver** — final MP4, `reports/SOURCES.md`, `reports/sources.csv`,
    `reports/youtube_description.md`, `reports/license_report.md`, `reports/qc_report.md`.

One-shot: `python scripts/run_pipeline.py --script S --title T [--narration A] [--preview]`
(resume any step with `--from verify`, stop with `--to build`).

## Tool-use rules

- Run scripts from the skill root; pass `--config project.yaml` for per-project overrides.
- Prefer official APIs; respect `Retry-After`, keep the polite per-host delay (`http.min_interval_sec`).
- **Never** download platform videos (YouTube, Rutube, VK, X, Facebook, Reddit, Mover.uz) unless the
  licence is Creative Commons / public domain *as stated by the platform*, or the user recorded
  permission in `manual_urls.txt`. Discovery results stay in reports for human follow-up.
- A search-engine result page is never a source. Credit the original page / author / archive.
- Credits: one per shot, bottom-right (configurable), small, faded; `Source: …`, `Manba: …`,
  `Archive footage: …`, `Source: X / @user`. Maps drawn by the tool say "Schematic map".
- Present-day footage of historical places gets "present day / hozirgi ko'rinish"; AI or 3D
  reconstructions get "reconstruction" — never present either as archive.
- If an integration fails, the scripts fall back to the next provider/candidate; report failures
  honestly from `reports/search_report_*.json` and `media_index.json["failed"]`.

## Quality standard

- Cinematic documentary pacing: 2.2–7 s shots, shorter on dramatic passages, impact cuts on
  dates/turning points, dissolves between calm scenes, fade-to-black between chapters.
- Visual mix target 80 % moving footage / 15 % stills & documents / 5 % maps & graphics,
  adapted to the era (pre-1839 topics rely on art and labelled present-day footage).
- No repeated shots, no anachronisms, no unlabelled AI imagery, every third-party shot credited.
- Effects in moderation; grade consistent; narration intelligible (music ducked ≥ 10 dB).
- Export: MP4, 1920×1080 (or 3840×2160), 16:9, 25/30 fps, H.264 High / H.265, AAC 320k 48 kHz,
  -14 LUFS integrated, ≤ -1 dBTP, `+faststart`.
- Read `references/editing_rules.md`, `references/fair_use.md`, `references/media_sources.md`,
  `references/historical_accuracy.md` before the first real project.

## Files

```
SKILL.md  README.md  config.yaml  requirements.txt  .env.example
scripts/  analyze_script.py search_videos.py search_images.py search_core.py verify_license.py
          download_media.py scene_builder.py source_overlay.py video_editor.py motion_graphics.py
          audio_editor.py export_video.py quality_check.py run_pipeline.py check_env.py
          make_demo_assets.py licenses.py common.py providers/ data/lexicon.json
references/ fair_use.md media_sources.md editing_rules.md historical_accuracy.md
templates/  storyboard.json timeline.json source_overlay.json youtube_description.md
tests/      pytest suite (offline)      examples/samarkand_demo/  sample project
assets/     fonts/ music/ sfx/ luts/    output/  per-project work folders
```
