#!/usr/bin/env python3
"""Step 11: synchronise visuals with narration and build timeline.json.

Decisions taken here (all configurable in config.yaml -> timeline):
  * shot lengths per scene from mood (dramatic = shorter shots / impact cuts)
  * media type mix aims at visual_ratio (default 80% video / 15% images / 5% graphics)
    and adapts to what was actually downloaded (pre-photographic topics get more stills)
  * no asset segment is used twice; a clip may be reused only with a different time range
  * clip in/out points respect shot cuts detected in the source
  * transitions: cut inside scenes, dissolve between calm scenes, fade-to-black on chapter
    change, white "impact" flash on dramatic emphasis
  * cut points optionally snapped to music beats (audio/beats.json)
  * overlays: per-clip source credit, lower thirds, date cards, chapter titles, subtitles
  * audio events: narration, J/L-cut clip audio, ambience and SFX hits

Usage: python scripts/scene_builder.py --project <slug>
"""
from __future__ import annotations

import argparse
import math
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import SKILL_ROOT, load_config, log, project_dir, read_json, setup_logging, write_json  # noqa: E402
from licenses import credit_line  # noqa: E402

MOOD_SHOT = {"dramatic": 0.72, "tense": 0.85, "epic": 1.0, "neutral": 1.0, "calm": 1.25, "solemn": 1.35}
MAP_WORDS = re.compile(r"\b(map|xarita|карта|atlas|chart)\b", re.I)


def shot_plan(duration: float, mood: str, cfg: dict, rnd: random.Random) -> list[float]:
    t = cfg["timeline"]
    base = (t["min_shot_sec"] + t["max_shot_sec"]) / 2 * MOOD_SHOT.get(mood, 1.0)
    n = max(1, round(duration / base), math.ceil(duration / t["max_shot_sec"]))
    raw = [rnd.uniform(0.8, 1.2) for _ in range(n)]
    s = sum(raw)
    shots = [duration * r / s for r in raw]
    # enforce minimum shot length by merging
    while len(shots) > 1 and min(shots) < t["min_shot_sec"]:
        i = shots.index(min(shots))
        j = i - 1 if i > 0 else i + 1
        shots[j] += shots.pop(i)
    return [round(x, 3) for x in shots]


def snap_to_beats(times: list[float], beats: list[float], window: float) -> list[float]:
    if not beats:
        return times
    out = []
    import bisect
    for t in times:
        i = bisect.bisect_left(beats, t)
        cands = [beats[k] for k in (i - 1, i) if 0 <= k < len(beats)]
        best = min(cands, key=lambda b: abs(b - t)) if cands else t
        out.append(round(best, 3) if abs(best - t) <= window else t)
    return out


class Picker:
    """Chooses assets per shot keeping the global visual ratio and avoiding reuse."""

    def __init__(self, assets: list[dict], cfg: dict):
        self.assets = assets
        self.cfg = cfg
        self.used: dict[str, list[tuple[float, float]]] = {}
        self.secs = {"video": 0.0, "image": 0.0, "graphic": 0.0}
        self.ratio = cfg["timeline"]["visual_ratio"]

    def _free_range(self, a: dict, need: float) -> tuple[float, float] | None:
        dur = a.get("duration") or 0
        if a["media_type"] == "image":
            return None if a["asset_id"] in self.used else (0.0, need)
        if dur < 1.0:
            return None
        lead = min(0.5, dur * 0.05)
        cuts = [0.0] + [c for c in a.get("cuts", []) if 0 < c < dur] + [dur]
        spans = [(cuts[i] + (lead if i == 0 else 0.12), cuts[i + 1] - 0.12) for i in range(len(cuts) - 1)]
        spans = [s for s in spans if s[1] - s[0] >= min(need, 1.6)]
        spans.sort(key=lambda s: s[1] - s[0], reverse=True)
        taken = self.used.get(a["asset_id"], [])
        for s0, s1 in spans + [(lead, dur - 0.1)]:
            length = min(need, s1 - s0)
            # slide inside span to avoid used ranges
            x = s0
            while x + length <= s1 + 1e-6:
                if all(x + length <= u0 or x >= u1 for u0, u1 in taken):
                    return (round(x, 3), round(x + length, 3))
                x += 0.5
        return None

    def want_type(self, scene: dict, total_so_far: float) -> str:
        if total_so_far <= 0:
            return "video"
        deficit = {k: self.ratio.get(k, 0) - self.secs[k] / total_so_far for k in self.secs}
        return max(deficit, key=deficit.get)

    def pick(self, scene: dict, kind: str, need: float, near: list[str]) -> tuple[dict, tuple[float, float]] | None:
        order = [scene["id"]] + near

        def ranked(mt):
            pool = [a for a in self.assets if a["media_type"] == mt]
            pool.sort(key=lambda a: (order.index(a["scene_id"]) if a["scene_id"] in order else 99,
                                     len(self.used.get(a["asset_id"], []))))
            return pool

        for mt in ([kind] + [k for k in ("video", "image") if k != kind]):
            if mt == "graphic":
                continue
            for a in ranked(mt):
                if a["scene_id"] not in order:
                    continue
                rng = self._free_range(a, need)
                if rng:
                    return a, rng
        return None

    def mark(self, a: dict, rng: tuple[float, float], secs: float, kind: str):
        self.used.setdefault(a["asset_id"], []).append(rng)
        self.secs[kind] += secs


def find_audio(dirpath: Path, names: list[str], exts=(".wav", ".mp3", ".ogg", ".flac", ".m4a")) -> list[Path]:
    if not dirpath.exists():
        return []
    files = [f for f in dirpath.rglob("*") if f.suffix.lower() in exts]
    out = []
    for n in names:
        out += [f for f in files if n.lower() in f.stem.lower()]
    return out


def subtitle_lines(text: str, start: float, dur: float, max_chars: int = 42) -> list[dict]:
    words = text.split()
    chunks, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > max_chars * 2 or (cur and re.search(r"[.!?…]$", cur) and len(cur) > max_chars * 0.6):
            chunks.append(cur.strip())
            cur = ""
        cur += " " + w
    if cur.strip():
        chunks.append(cur.strip())
    total = sum(len(c) for c in chunks) or 1
    t, out = start, []
    for c in chunks:
        d = dur * len(c) / total
        # break into two lines near the middle
        if len(c) > max_chars:
            mid = len(c) // 2
            sp = c.rfind(" ", 0, mid + 8)
            c = c[:sp] + "\\N" + c[sp + 1:] if sp > 0 else c
        out.append({"start": round(t, 3), "end": round(t + d - 0.04, 3), "text": c})
        t += d
    return out


def build(sb: dict, index: dict, cfg: dict, beats: list[float], seed: int = 7) -> dict:
    rnd = random.Random(seed)
    tl_cfg = cfg["timeline"]
    lang = sb.get("language", cfg["project"]["language"])
    picker = Picker(index.get("assets", []), cfg)
    clips, overlays, subs, audio_events = [], [], [], []
    scenes = sb["scenes"]
    T = tl_cfg["transition_sec"]
    missing = []
    for si, sc in enumerate(scenes):
        start, dur = sc["start"], sc["duration"]
        shots = shot_plan(dur, sc["mood"], cfg, rnd)
        bounds = [start]
        for d in shots[:-1]:
            bounds.append(bounds[-1] + d)
        if tl_cfg.get("snap_cuts_to_beats") and beats:
            inner = snap_to_beats(bounds[1:], beats, tl_cfg["beat_snap_window_sec"])
            bounds = [start] + inner
        bounds.append(start + dur)
        bounds = sorted(set(round(b, 3) for b in bounds))
        near = [scenes[k]["id"] for k in (si - 1, si + 1, si - 2, si + 2) if 0 <= k < len(scenes)]
        impact = any(e["type"] == "impact_cut" for e in sc["effects"])
        map_effect = next((e for e in sc["effects"] if e["type"] == "map_animation"), None)
        total_so_far = sum(c["duration"] for c in clips)
        for k in range(len(bounds) - 1):
            cs, ce = bounds[k], bounds[k + 1]
            need = round(ce - cs, 3)
            if need < 0.3:
                continue
            kind = picker.want_type(sc, total_so_far)
            clip = {"id": f"c{len(clips) + 1:04d}", "scene_id": sc["id"], "start": round(cs, 3), "duration": need,
                    "transition_in": {"type": "cut", "duration": 0.0}}
            if kind == "graphic" and map_effect and len(map_effect.get("places", [])) >= 1 and \
                    not any(c["kind"] == "map" and c["scene_id"] == sc["id"] for c in clips):
                clip.update(kind="map", places=map_effect["places"], effect={"type": "map_route"},
                            credit={"text": {"uz": "Sxematik xarita", "ru": "Схематичная карта",
                                             "en": "Schematic map"}.get(lang, "Schematic map"), "asset_id": None})
                picker.secs["graphic"] += need
            else:
                choice = picker.pick(sc, "image" if kind == "graphic" else kind, need, near)
                if not choice:
                    missing.append(sc["id"])
                    clip.update(kind="card", text=(sc.get("chapter") or sb["title"]), effect={"type": "slow_push"},
                                credit=None)
                    picker.secs["graphic"] += need
                else:
                    a, rng = choice
                    is_map = bool(MAP_WORDS.search(a["meta"].get("title") or ""))
                    meta = a["meta"]
                    credit_src = dict(meta, media_type=a["media_type"])
                    if meta.get("present_day"):
                        credit_src["present_day"] = True
                    text = meta.get("credit") or credit_line(credit_src, lang, cfg["overlay"]["source_prefix"])
                    if a["media_type"] == "video":
                        src_in = (a.get("src_in") or 0.0) + rng[0]
                        speed = 1.0
                        avail = rng[1] - rng[0]
                        if avail < need:  # gentle slow-motion (max 0.75x) then hold
                            speed = max(0.75, avail / need)
                        clip.update(kind="video", asset_id=a["asset_id"], path=a["path"], in_point=rng[0],
                                    out_point=round(rng[0] + min(avail, need * speed), 3), speed=round(speed, 3),
                                    src_range=[round(src_in, 2), round(src_in + min(avail, need * speed), 2)],
                                    width=a.get("width"), height=a.get("height"),
                                    effect={"type": "smooth_zoom" if rnd.random() < 0.35 else "none"},
                                    has_audio=a.get("has_audio", False))
                        picker.mark(a, (rng[0], rng[0] + min(avail, need * speed)), need, "video")
                    else:
                        aspect = (a.get("width") or 16) / max(1, a.get("height") or 9)
                        if is_map:
                            eff = "map_zoom"
                        elif aspect < 1.2 and cfg["render"].get("parallax"):
                            eff = "parallax"  # portraits / documents: never crop heads or text away
                        else:
                            eff = "parallax" if cfg["render"].get("parallax") and rnd.random() < 0.3 else "ken_burns"
                        direction = rnd.choice(["in", "out", "left", "right", "up"])
                        clip.update(kind="image", asset_id=a["asset_id"], path=a["path"],
                                    width=a.get("width"), height=a.get("height"),
                                    effect={"type": eff, "direction": direction, "zoom": cfg["render"]["ken_burns_zoom"]})
                        picker.mark(a, rng, need, "graphic" if is_map else "image")
                    clip["credit"] = {"text": text, "asset_id": a["asset_id"], "page_url": meta.get("page_url")}
            # transitions
            if k == 0 and si > 0:
                prev = scenes[si - 1]
                if sc.get("chapter") != prev.get("chapter"):
                    clip["transition_in"] = {"type": "fadeblack", "duration": T}
                elif impact:
                    clip["transition_in"] = {"type": "impact", "duration": tl_cfg["impact_flash_sec"]}
                elif sc["mood"] in ("calm", "solemn", "neutral") and prev["mood"] in ("calm", "solemn", "neutral"):
                    clip["transition_in"] = {"type": "dissolve", "duration": T}
            elif k > 0 and impact and k == 1 and sc["mood"] == "dramatic":
                clip["transition_in"] = {"type": "impact", "duration": tl_cfg["impact_flash_sec"]}
            clips.append(clip)
            total_so_far += need

        # overlays from scene effects (chapter title first, date card after it, never stacked)
        has_chapter = any(e["type"] == "chapter_title" and e.get("text") for e in sc["effects"])
        date_at = start + (3.9 if has_chapter else 0.2)
        for e in sc["effects"]:
            if e["type"] == "lower_third":
                overlays.append({"type": "lower_third", "start": round(start + 0.6, 3),
                                 "end": round(min(start + dur, start + 5.6), 3), "title": e["title"], "subtitle": e.get("subtitle", "")})
            elif e["type"] == "date_card":
                if date_at + 2.0 <= start + dur:
                    overlays.append({"type": "date_card", "start": round(date_at, 3),
                                     "end": round(min(start + dur - 0.1, date_at + 3.2), 3), "text": e["text"]})
            elif e["type"] == "chapter_title" and e.get("text"):
                overlays.append({"type": "chapter_title", "start": round(start + 0.1, 3),
                                 "end": round(min(start + dur, start + 3.6), 3), "text": e["text"]})
        if cfg["overlay"].get("subtitles", True):
            subs += subtitle_lines(sc["narration"], start, dur)

        # audio: ambience and impact hits
        sfx_dir = SKILL_ROOT / cfg["paths"]["sfx_dir"]
        amb = find_audio(sfx_dir, sc.get("sfx", []))
        if amb:
            audio_events.append({"type": "ambience", "path": str(amb[0]), "start": start, "duration": dur,
                                 "gain_db": cfg["audio"]["ambient_volume_db"]})
        if impact:
            hit = find_audio(sfx_dir, ["impact", "boom", "hit", "whoosh"])
            if hit:
                audio_events.append({"type": "sfx", "path": str(hit[0]), "start": max(0, start - 0.05),
                                     "duration": 2.5, "gain_db": -8})

    # clip-audio J/L cuts for archive clips that have sound
    jl = cfg["audio"]["jl_cut_sec"]
    for i, c in enumerate(clips):
        if c.get("kind") == "video" and c.get("has_audio"):
            lead = jl if i > 0 else 0.0
            audio_events.append({"type": "clip_audio", "path": c["path"], "clip_id": c["id"],
                                 "start": round(max(0, c["start"] - lead), 3),
                                 "src_in": round(max(0, c["in_point"] - lead), 3),
                                 "duration": round(c["duration"] + lead + jl, 3),
                                 "gain_db": cfg["audio"]["source_clip_audio_db"], "speed": c.get("speed", 1.0)})

    # merge consecutive identical credits -> one stable caption
    credits = []
    for c in clips:
        cr = c.get("credit")
        if not cr:
            continue
        if credits and credits[-1]["text"] == cr["text"] and abs(credits[-1]["end"] - c["start"]) < 0.05:
            credits[-1]["end"] = round(c["start"] + c["duration"], 3)
            credits[-1]["clips"].append(c["id"])
        else:
            credits.append({"type": "credit", "text": cr["text"], "start": c["start"],
                            "end": round(c["start"] + c["duration"], 3), "clips": [c["id"]]})
    overlays = credits + overlays

    total = round(scenes[-1]["start"] + scenes[-1]["duration"], 3)
    achieved = {k: round(v / max(0.001, total), 3) for k, v in picker.secs.items()}
    music = sorted(find_audio(SKILL_ROOT / cfg["paths"]["music_dir"], [""]))
    moods = [s["mood"] for s in scenes]
    main_mood = max(set(moods), key=moods.count)
    pick_music = next((m for m in music if main_mood in m.stem.lower()), music[0] if music else None)
    return {
        "schema": "hve.timeline/1",
        "title": sb["title"],
        "slug": sb["slug"],
        "language": lang,
        "settings": {k: cfg["render"][k] for k in ("width", "height", "fps")},
        "total_duration": total,
        "visual_ratio_target": tl_cfg["visual_ratio"],
        "visual_ratio_achieved": achieved,
        "scenes_missing_visuals": sorted(set(missing)),
        "chapters": chapters(sb),
        "clips": clips,
        "overlays": overlays,
        "subtitles": subs,
        "audio": {"narration": sb.get("narration_audio"), "music": str(pick_music) if pick_music else None,
                  "music_mood": main_mood, "events": audio_events},
    }


def chapters(sb: dict) -> list[dict]:
    out = []
    for s in sb["scenes"]:
        name = s.get("chapter") or ""
        if name and (not out or out[-1]["title"] != name):
            out.append({"start": s["start"], "title": name})
    if out and out[0]["start"] > 0:
        out.insert(0, {"start": 0.0, "title": "Intro"})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--config")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    setup_logging(a.verbose)
    cfg = load_config(a.config)
    pdir = project_dir(cfg, a.project)
    sb = read_json(pdir / "storyboard.json")
    idx = read_json(pdir / "media_index.json") if (pdir / "media_index.json").exists() else {"assets": []}
    beats_f = pdir / "audio" / "beats.json"
    beats = read_json(beats_f).get("beats", []) if beats_f.exists() else []
    tl = build(sb, idx, cfg, beats, a.seed)
    write_json(pdir / "timeline.json", tl)
    log.info("timeline: %d clips, ratio %s, missing visuals in %s", len(tl["clips"]), tl["visual_ratio_achieved"],
             tl["scenes_missing_visuals"] or "none")
    print(pdir / "timeline.json")


if __name__ == "__main__":
    main()
