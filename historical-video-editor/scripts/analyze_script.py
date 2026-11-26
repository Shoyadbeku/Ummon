#!/usr/bin/env python3
"""Step 1-4: read a script / narration, analyse historical context, split it
into scenes and generate multilingual search queries.

Output: <project>/storyboard.json (schema: templates/storyboard.json)

The analysis is deterministic (regex + multilingual gazetteer in
scripts/data/lexicon.json). When the skill runs inside an AI agent, the agent
is expected to REVIEW and ENRICH storyboard.json (better keywords, periods,
anachronism notes) before searching — see SKILL.md, step 2.

Usage:
  python scripts/analyze_script.py --script script.txt --title "Amir Temur" \
      [--narration narration.mp3] [--duration 600] [--lang uz] [--project slug]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (SKILL_ROOT, load_config, log, media_info, project_dir, read_json,  # noqa: E402
                    setup_logging, slugify, write_json)

LEXICON = read_json(SKILL_ROOT / "scripts" / "data" / "lexicon.json")

APOS = re.compile(r"[ʻʼ‘’`´ʹ]")
ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "M": 1000}

# dramatic / emphasis words in uz, ru, en  -> impact cut + SFX hit
EMPHASIS = re.compile(
    r"\b(birdan|to'satdan|ammo|lekin|biroq|halokat|fojia|qirg'in|g'alaba|mag'lubiyat|"
    r"внезапно|однако|но|катастрофа|трагедия|победа|поражение|резня|"
    r"suddenly|however|but|disaster|tragedy|victory|defeat|massacre|never|forever)\b",
    re.I,
)


def norm(text: str) -> str:
    return APOS.sub("'", text)


def roman_to_int(s: str) -> int:
    total, prev = 0, 0
    for ch in reversed(s.upper()):
        v = ROMAN.get(ch, 0)
        total = total - v if v < prev else total + v
        prev = max(prev, v)
    return total


# --------------------------------------------------------------------------
# scene splitting
# --------------------------------------------------------------------------
SCENE_MARK = re.compile(r"^\s*(?:#{1,6}\s+|\[(?:scene|sahna|сцена)[^\]]*\]\s*|(?:scene|sahna|сцена)\s*\d+[.:)]\s*)(.*)$", re.I)
SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+(?=[A-ZА-ЯЁO'G'ʻ\"«(0-9])")


NOTE_RX = re.compile(r"^\s*[*_]*\s*[\[(]\s*(?:vizual|visual|визуал|kadr|кадр|b-roll|note|izoh)?[^\])]*[\])]\s*[*_]*\s*$", re.I)
META_RX = re.compile(r"^\s*\*\*[^*]{1,40}:\*\*")
TS_RX = re.compile(r"^\[?\(?\d{1,2}:\d{2}\s*[-–]\s*\d{1,2}:\d{2}\]?\)?\s*")


def clean_md(line: str) -> str:
    line = re.sub(r"\*\*|__|(?<!\w)\*(?!\s)|(?<!\s)\*(?!\w)", "", line)
    line = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1", line)
    return line.strip()


def split_scenes(text: str, max_words: int = 45, min_words: int = 12) -> list[dict]:
    """Split by explicit markers / blank lines, then long paragraphs by sentences.
    Lines like *[Vizual: ...]* become director notes of the following scenes."""
    text = norm(text.replace("\r\n", "\n"))
    blocks: list[dict] = []
    heading = ""
    notes: list[str] = []
    buf: list[str] = []

    def flush():
        nonlocal buf
        para = " ".join(" ".join(buf).split())
        if para:
            blocks.append({"heading": heading, "text": para, "notes": list(notes)})
        buf = []

    for line in text.split("\n"):
        if NOTE_RX.match(line):
            flush()
            notes = [clean_md(line).strip("[]() ")]
            continue
        if META_RX.match(line):
            continue
        m = SCENE_MARK.match(line)
        if m:
            flush()
            rest = m.group(1).strip()
            # a heading line alone is a chapter title; text after [scene] marker is narration
            if line.lstrip().startswith("#"):
                heading = TS_RX.sub("", clean_md(rest)).strip()
                notes = []
            elif rest:
                buf.append(rest)
            continue
        if not line.strip():
            flush()
            continue
        if line.strip().startswith(("<!--", "---")):
            continue
        buf.append(clean_md(line))
    flush()

    scenes: list[dict] = []
    for b in blocks:
        words = b["text"].split()
        if len(words) <= max_words:
            scenes.append(b)
            continue
        first = True
        sents = SENT_SPLIT.split(b["text"])
        cur: list[str] = []
        for s in sents:
            if cur and len(" ".join(cur + [s]).split()) > max_words:
                scenes.append({"heading": b["heading"], "text": " ".join(cur), "notes": b["notes"] if first else []})
                first = False
                cur = []
            cur.append(s)
        if cur:
            scenes.append({"heading": b["heading"], "text": " ".join(cur), "notes": b["notes"] if first else []})

    # merge very short fragments into the previous scene
    merged: list[dict] = []
    for s in scenes:
        if merged and len(s["text"].split()) < min_words and merged[-1]["heading"] == s["heading"]:
            merged[-1]["text"] += " " + s["text"]
            merged[-1]["notes"] = merged[-1].get("notes", []) + s.get("notes", [])
        else:
            merged.append(dict(s))
    return merged


# --------------------------------------------------------------------------
# entity extraction
# --------------------------------------------------------------------------
def _alias_regex(alias: str) -> re.Pattern:
    return re.compile(r"(?<![\w'])" + re.escape(alias) + r"(?:[a-zа-яё']{0,6})?(?![\w])", re.I)


_COMPILED: dict[str, list[tuple[str, re.Pattern]]] = {}
for _kind in ("places", "persons", "terms"):
    lst = []
    for canon, d in LEXICON[_kind].items():
        for a in sorted(set(d["aliases"] + [canon.lower()]), key=len, reverse=True):
            lst.append((canon, _alias_regex(norm(a))))
    _COMPILED[_kind] = lst


def find_entities(text: str, kind: str) -> list[str]:
    found: list[tuple[int, str]] = []
    seen = set()
    for canon, rx in _COMPILED[kind]:
        if canon in seen:
            continue
        m = rx.search(text)
        if m:
            seen.add(canon)
            found.append((m.start(), canon))
    return [c for _, c in sorted(found)]


YEAR_RX = re.compile(r"(?<![\d.,])(1[0-9]{3}|20[0-4][0-9]|[1-9][0-9]{2})(?:\s*[-–]\s*(?:yil|yilda|yillar|йил|год|годы|г\.)|\s*(?:yil|yilda|yilning|yillarda|йил|год[ау]?|г\.|AD|CE|BC|BCE|mil\. avv))?(?![\d])", re.I)
BC_RX = re.compile(r"(mil\.?\s*avv|miloddan avvalgi|до н\.?\s*э|BC|BCE)", re.I)
CENTURY_RX = re.compile(r"\b([IVXLC]{1,6})\s*[-–]?\s*(asr|asrda|asrning|век|века|в\.|century)\b|\b(\d{1,2})(?:st|nd|rd|th)?[-\s]*(asr|asrda|century|век|века)\b", re.I)


def find_dates(text: str) -> dict:
    years: list[int] = []
    for m in YEAR_RX.finditer(text):
        y = int(m.group(1))
        # reject numbers that are clearly counts ("300 askar") — need year suffix unless 4 digits
        has_suffix = bool(re.search(r"(yil|йил|год|г\.|AD|CE|BC|BCE|avv)", m.group(0), re.I))
        if len(m.group(1)) < 4 and not has_suffix:
            continue
        if BC_RX.search(m.group(0)) or BC_RX.search(text[m.end(): m.end() + 30]):
            y = -y
        years.append(y)
    centuries = []
    for m in CENTURY_RX.finditer(text):
        c = roman_to_int(m.group(1)) if m.group(1) else int(m.group(3))
        if 1 <= c <= 21:
            bc = bool(BC_RX.search(text[m.end(): m.end() + 30]))
            centuries.append(-c if bc else c)
    return {"years": years, "centuries": centuries}


def period_of(dates: dict, persons: list[str], fallback: dict | None = None) -> dict:
    ys = list(dates["years"])
    for c in dates["centuries"]:
        if c > 0:
            ys += [(c - 1) * 100 + 1, c * 100]
        else:
            ys += [c * 100, (c + 1) * 100 - 1]
    for p in persons:
        d = LEXICON["persons"][p]
        ys += [d["born"], d["died"]]
    if not ys:
        return dict(fallback) if fallback else {"start": None, "end": None, "label": "unknown", "media_era": "unknown"}
    start, end = min(ys), max(ys)
    return {"start": start, "end": end, "label": era_label(start, end), "media_era": media_era(end)}


def era_label(start: int, end: int) -> str:
    def f(y):
        return f"{-y} BC" if y < 0 else str(y)
    return f(start) if start == end else f"{f(start)}–{f(end)}"


def media_era(year: int | None) -> str:
    """What kind of authentic visual record can exist for that time."""
    if year is None:
        return "unknown"
    if year < 1839:
        return "pre_photographic"   # only art, manuscripts, artefacts, architecture, maps
    if year < 1895:
        return "early_photography"  # photographs, engravings; no film
    if year < 1928:
        return "silent_film"        # newsreels / silent film exist
    if year < 1950:
        return "sound_film_bw"
    if year < 1980:
        return "color_film"
    return "modern_video"


# anachronism guard: things that must NOT appear for a period (search exclusions)
ANACHRONISMS = [
    (1885, ["car", "automobile", "машина"]),
    (1903, ["airplane", "aircraft", "самолет"]),
    (1916, ["tank", "танк"]),
    (1830, ["train", "railway", "поезд"]),
    (1839, ["photo", "photograph", "фото"]),
    (1895, ["film", "newsreel", "кинохроника", "footage"]),
    (1945, ["nuclear explosion", "ядерный взрыв"]),
    (1950, ["color film"]),
]


def anachronism_terms(period: dict) -> list[str]:
    end = period.get("end")
    if end is None:
        return []
    out = []
    for year, words in ANACHRONISMS:
        if end < year:
            out += words
    return out


# --------------------------------------------------------------------------
# queries
# --------------------------------------------------------------------------
def build_queries(scene: dict, langs: list[str], topic: str) -> dict:
    places, persons, terms = scene["places"], scene["persons"], scene["terms"]
    era = scene["period"]["media_era"]
    start = scene["period"].get("start")
    decade = f"{(start // 10) * 10}s" if isinstance(start, int) and start >= 1839 else ""
    q: dict[str, list[str]] = {}
    for lang in langs:
        items: list[str] = []

        def name(kind, canon):
            d = LEXICON[kind][canon]
            return canon if lang == "en" else d.get(lang, canon)

        pl = [name("places", p) for p in places[:2]]
        pe = [name("persons", p) for p in persons[:2]]
        tv = []
        for t in terms[:3]:
            d = LEXICON["terms"][t]
            tv.append(d["visual"] if lang == "en" else d.get(lang, t))
        arch = {"en": "archive footage", "ru": "кинохроника", "uz": "arxiv kadrlari"}.get(lang, "archive")
        if era == "modern_video":
            arch = {"en": "footage", "ru": "кадры", "uz": "kadrlar"}.get(lang, arch)
        elif lang == "en" and era in ("pre_photographic",):
            arch = "historical painting"
        elif lang == "ru" and era == "pre_photographic":
            arch = "миниатюра"
        elif lang == "uz" and era == "pre_photographic":
            arch = "miniatyura"
        for p in pe:
            items.append(p)
            items.append(f"{p} {'portrait' if lang == 'en' else 'портрет' if lang == 'ru' else 'portret'}")
        for p in pl:
            if tv:
                items.append(f"{p} {tv[0]}")
            items.append(f"{p} {arch}" + (f" {decade}" if decade and lang == "en" else ""))
        for t in tv:
            plain = era == "pre_photographic" or any(w in t.lower() for w in ("footage", "map", "карта", "xarita"))
            items.append(t if plain else f"{t} {arch}")
        if not items:
            items.append(f"{topic} {arch}")
        seen, uniq = set(), []
        for it in items:
            k = it.lower().strip()
            if k and k not in seen:
                seen.add(k)
                uniq.append(it.strip())
        q[lang] = uniq[:8]
    # map query
    maps = []
    if scene["needs_map"]:
        base = places[0] if places else topic
        when = scene["period"]["label"] if scene["period"]["label"] != "unknown" else ""
        maps = [f"{base} historical map {when}".strip(), f"{LEXICON['places'].get(base, {}).get('ru', base)} историческая карта"]
    q["maps"] = maps
    return q


# --------------------------------------------------------------------------
# durations
# --------------------------------------------------------------------------
def assign_durations(scenes: list[dict], total: float | None, wpm: float) -> float:
    weights = [max(1, len(s["narration"])) for s in scenes]
    if not total:
        words = sum(len(s["narration"].split()) for s in scenes)
        total = words / wpm * 60.0
    wsum = float(sum(weights))
    t = 0.0
    for s, w in zip(scenes, weights):
        d = round(total * w / wsum, 2)
        s["start"], s["duration"] = round(t, 2), d
        t += d
    return round(t, 2)


def align_with_whisper(scenes: list[dict], audio: Path, lang: str) -> bool:
    """Word-level alignment with faster-whisper if installed. Returns True on success."""
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError:
        return False
    import os
    model = WhisperModel(os.environ.get("WHISPER_MODEL", "small"), compute_type="int8")
    segs, _ = model.transcribe(str(audio), language=None if lang == "uz" else lang, word_timestamps=True)
    words = [w for s in segs for w in (s.words or [])]
    if not words:
        return False
    total_words = sum(len(s["narration"].split()) for s in scenes)
    ratio = len(words) / max(1, total_words)
    idx = 0
    for s in scenes:
        n = max(1, round(len(s["narration"].split()) * ratio))
        chunk = words[idx: idx + n] or words[-1:]
        s["start"] = round(chunk[0].start, 2)
        s["duration"] = round(chunk[-1].end - chunk[0].start, 2)
        idx += n
    # close gaps so scenes are contiguous
    for a, b in zip(scenes, scenes[1:]):
        a["duration"] = round(b["start"] - a["start"], 2)
    scenes[-1]["duration"] = round(max(scenes[-1]["duration"], float(words[-1].end) - scenes[-1]["start"]), 2)
    return True


# --------------------------------------------------------------------------
# main analysis
# --------------------------------------------------------------------------
def analyse(text: str, title: str, cfg: dict, narration: Path | None = None,
            duration: float | None = None) -> dict:
    lang = cfg["project"]["language"]
    langs = cfg["project"]["search_languages"]
    raw = split_scenes(text)
    if not raw:
        raise ValueError("script is empty")
    topic_dates = find_dates(norm(title + " " + text))
    topic_persons = find_entities(norm(title + " " + text), "persons")
    topic_period = period_of(topic_dates, topic_persons[:3])
    scenes = []
    seen_persons: set[str] = set()
    prev_period = topic_period
    for i, r in enumerate(raw, 1):
        t = r["text"]
        places = find_entities(t, "places")
        persons = find_entities(t, "persons")
        terms = find_entities(t, "terms")
        dates = find_dates(t)
        period = period_of(dates, persons, fallback=prev_period)
        if period["start"] is None:
            period = dict(topic_period)
        prev_period = period
        moods = [LEXICON["terms"][x]["mood"] for x in terms]
        mood = max(set(moods), key=moods.count) if moods else "neutral"
        emphasis = [m.group(0) for m in EMPHASIS.finditer(t)]
        needs_map = any(LEXICON["terms"][x].get("map") for x in terms) or len(places) >= 2
        new_people = [p for p in persons if p not in seen_persons]
        persons = new_people + [p for p in persons if p not in new_people]  # newly introduced people first
        seen_persons.update(persons)
        sfx = []
        for x in terms:
            sfx += LEXICON["terms"][x]["sfx"]
        effects = []
        if dates["years"]:
            effects.append({"type": "date_card", "text": str(abs(dates["years"][0])) + (" BC" if dates["years"][0] < 0 else ""), "at": 0.0})
        for p in new_people:
            d = LEXICON["persons"][p]
            label = d.get(lang, p)
            effects.append({"type": "lower_third", "title": label,
                            "subtitle": f"{era_label(d['born'], d['died'])} · {d['role']}", "at": 0.3})
        if emphasis or mood == "dramatic":
            effects.append({"type": "impact_cut", "reason": (emphasis or ["dramatic"])[0]})
        if needs_map:
            effects.append({"type": "map_animation", "places": places[:4]})
        if r["heading"] and (i == 1 or raw[i - 2]["heading"] != r["heading"]):
            effects.append({"type": "chapter_title", "text": r["heading"]})
        scene = {
            "id": f"s{i:03d}",
            "index": i,
            "chapter": r["heading"],
            "narration": t,
            "director_notes": r.get("notes", []),
            "words": len(t.split()),
            "period": period,
            "places": places,
            "persons": persons,
            "terms": terms,
            "dates": dates,
            "mood": mood,
            "emphasis": emphasis,
            "needs_map": needs_map,
            "effects": effects,
            "sfx": sorted(set(sfx)),
            "exclude_terms": anachronism_terms(period),
            "visual_notes": visual_notes(period),
        }
        scene["queries"] = build_queries(scene, langs, title)
        scenes.append(scene)

    total = None
    aligned = False
    if narration and narration.exists():
        total = media_info(narration)["duration"]
        aligned = align_with_whisper(scenes, narration, lang)
    if not aligned:
        target = duration or cfg["project"].get("target_duration_sec") or None
        total = assign_durations(scenes, total or target, cfg["project"]["words_per_minute"])
    else:
        total = round(scenes[-1]["start"] + scenes[-1]["duration"], 2)

    for s in scenes:
        s["shots"] = max(1, round(s["duration"] / ((cfg["timeline"]["min_shot_sec"] + cfg["timeline"]["max_shot_sec"]) / 2)))

    return {
        "schema": "hve.storyboard/1",
        "title": title,
        "slug": slugify(title),
        "language": lang,
        "search_languages": langs,
        "topic_period": topic_period,
        "total_duration": total,
        "timing_source": "whisper" if aligned else ("narration_length" if narration else "words_per_minute"),
        "narration_audio": str(narration) if narration else None,
        "scenes": scenes,
        "review_required": True,
        "review_notes": [
            "Check periods/places detected automatically; add missing entities and English keywords.",
            "Pre-photographic periods cannot have authentic archive footage: use art, manuscripts, artefacts, "
            "present-day location footage (labelled) and animated maps.",
        ],
    }


def visual_notes(period: dict) -> str:
    era = period.get("media_era")
    return {
        "pre_photographic": "No photos/film exist. Use miniatures, manuscripts, paintings, coins, architecture "
                            "(present-day footage labelled 'Present day'), maps. Never present reenactments as archive.",
        "early_photography": "Photographs and engravings only (no film before 1895).",
        "silent_film": "Silent newsreels and photos. B/W only.",
        "sound_film_bw": "B/W newsreels and photos; colour footage is rare — verify.",
        "color_film": "Newsreels, colour film possible.",
        "modern_video": "Video and photo widely available; prefer news agencies / official archives.",
    }.get(era, "Verify era of every asset.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--script", required=True, help="script/narration text file (.txt/.md)")
    ap.add_argument("--title", required=True)
    ap.add_argument("--narration", help="narration audio (mp3/wav/m4a)")
    ap.add_argument("--duration", type=float, help="target duration in seconds (if no narration)")
    ap.add_argument("--lang", help="narration language (uz/ru/en)")
    ap.add_argument("--project", help="project slug (default: from title)")
    ap.add_argument("--config")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    setup_logging(a.verbose)
    cfg = load_config(a.config)
    if a.lang:
        cfg["project"]["language"] = a.lang
    text = Path(a.script).read_text(encoding="utf-8")
    sb = analyse(text, a.title, cfg, Path(a.narration) if a.narration else None, a.duration)
    if a.project:
        sb["slug"] = a.project
    out = project_dir(cfg, sb["slug"]) / "storyboard.json"
    write_json(out, sb)
    log.info("storyboard: %d scenes, %.1fs (%s) -> %s", len(sb["scenes"]), sb["total_duration"], sb["timing_source"], out)
    print(out)


if __name__ == "__main__":
    main()
