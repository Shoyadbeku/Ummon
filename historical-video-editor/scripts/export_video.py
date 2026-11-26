#!/usr/bin/env python3
"""Steps 16-17: final encode for YouTube + sources / licence reports.

Final pass (single encode): assembled picture -> colour grade (preset or .cube LUT) ->
film grain -> vignette -> optional letterbox -> ASS overlays (credits, lower thirds,
date cards, chapter titles, subtitles) -> mux with the loudness-normalised mix.

Defaults (config.yaml -> render): MP4, 1920x1080 16:9, 25 fps, H.264 High (or H.265 with
--codec libx265 / --4k), CRF 18, closed GOP, BT.709 tags, AAC 320k 48 kHz, +faststart.

Reports written to <project>/reports/:
  sources.json / sources.csv   every asset used: URL, author, licence, timeline in/out,
                               source time range, credit text, verification notes
  SOURCES.md                   human-readable attribution list
  youtube_description.md       ready to paste: summary, chapters, sources, licences,
                               fair-use / AI disclosure statements

Usage: python scripts/export_video.py --project <slug> [--4k] [--codec libx265] [--preview]
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (SKILL_ROOT, fmt_ts, fmt_yt, load_config, log, media_info, project_dir, read_json, run,  # noqa: E402
                    setup_logging, slugify, write_json)

GRADES = {
    "none": "",
    "documentary_warm": "eq=contrast=1.06:saturation=0.92:gamma=0.98,colorbalance=rs=0.025:bs=-0.025:rh=0.02:bh=-0.02",
    "cold_war": "eq=contrast=1.09:saturation=0.74:gamma=0.97,colorbalance=rs=-0.02:bs=0.045:bm=0.02",
    "sepia_archive": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,eq=contrast=1.05",
    "bleach_bypass": "eq=contrast=1.16:saturation=0.58:brightness=-0.01",
}


def look_chain(cfg: dict, W: int, H: int) -> list[str]:
    r = cfg["render"]
    f = []
    g = r.get("grade", "none")
    if isinstance(g, str) and g.startswith("lut:"):
        lut = SKILL_ROOT / cfg["paths"]["luts_dir"] / g[4:]
        if lut.exists():
            f.append(f"lut3d=file='{lut.as_posix()}'")
        else:
            log.warning("LUT %s not found — grade skipped", lut)
    elif GRADES.get(g):
        f.append(GRADES[g])
    if r.get("film_grain"):
        f.append(f"noise=c0s={int(r['film_grain'])}:c0f=t+u:c1s=0:c2s=0")
    if r.get("vignette"):
        f.append("vignette=angle=PI/5.5:mode=forward")
    if r.get("letterbox"):
        bar = int((H - W / 2.39) / 2)
        f.append(f"drawbox=x=0:y=0:w=iw:h={bar}:color=black:t=fill,drawbox=x=0:y=ih-{bar}:w=iw:h={bar}:color=black:t=fill")
    return f


def ass_path_escape(p: Path) -> str:
    s = p.resolve().as_posix()
    return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace(",", "\\,")


def encode(pdir: Path, cfg: dict, codec: str, four_k: bool, preview: bool) -> Path:
    tl = read_json(pdir / "timeline.json")
    src = pdir / "render" / "assembled.mp4"
    mixf = pdir / "audio" / "mix.wav"
    ass = pdir / "render" / "overlays.ass"
    info = media_info(src)
    W, H = info["width"], info["height"]
    fps = cfg["render"]["fps"]
    vf = look_chain(cfg, W, H)
    if ass.exists():
        fonts = SKILL_ROOT / cfg["paths"]["fonts_dir"]
        if any(fonts.glob("*.[ot]tf")):
            vf.append(f"ass='{ass_path_escape(ass)}':fontsdir='{ass_path_escape(fonts)}'")
        else:
            vf.append(f"ass='{ass_path_escape(ass)}'")
    if four_k and not preview:
        vf.append("scale=3840:2160:flags=lanczos")
    vf.append("format=yuv420p")
    out = pdir / f"{slugify(tl['title'])}{'_preview' if preview else ''}{'_4k' if four_k else ''}.mp4"
    preset = "ultrafast" if preview else cfg["render"]["preset"]
    crf = 26 if preview else cfg["render"]["crf"]
    vcodec = ["-c:v", codec, "-preset", preset, "-crf", str(crf)]
    if codec == "libx264":
        vcodec += ["-profile:v", "high", "-level:v", "5.1" if four_k else "4.2", "-x264-params", "open-gop=0"]
    else:
        vcodec += ["-tag:v", "hvc1", "-x265-params", "open-gop=0:log-level=error"]
    # cap peak bitrate (film grain is expensive) — YouTube recommends 8-12 Mbps (1080p) / 35-45 Mbps (4K) SDR
    vcodec += ["-maxrate", "45M" if four_k else "16M", "-bufsize", "90M" if four_k else "32M"]
    cmd = ["ffmpeg", "-y", "-v", "error", "-stats_period", "10", "-i", src]
    if mixf.exists():
        cmd += ["-i", mixf]
    else:
        cmd += ["-f", "lavfi", "-t", str(info["duration"]), "-i", "anullsrc=r=48000:cl=stereo"]
        log.warning("no audio mix found — exporting silent audio track")
    cmd += ["-map", "0:v:0", "-map", "1:a:0", "-vf", ",".join(vf), *vcodec, "-g", str(max(1, fps // 2)),
            "-bf", "2", "-r", str(fps), "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
            "-colorspace", "bt709", "-c:a", cfg["render"]["audio_codec"], "-b:a", cfg["render"]["audio_bitrate"],
            "-ar", str(cfg["render"]["audio_rate"]), "-ac", "2", "-shortest", "-movflags", "+faststart",
            "-metadata", f"title={tl['title']}", "-metadata", "comment=Edited with Historical Video Editor Skill", out]
    run(cmd, timeout=6 * 3600)
    log.info("exported %s", out)
    return out


# --------------------------------------------------------------------------
def build_sources(pdir: Path, cfg: dict) -> list[dict]:
    tl = read_json(pdir / "timeline.json")
    idx = read_json(pdir / "media_index.json") if (pdir / "media_index.json").exists() else {"assets": []}
    by_id = {a["asset_id"]: a for a in idx["assets"]}
    rows: dict[str, dict] = {}
    for c in tl["clips"]:
        aid = c.get("asset_id")
        if not aid or aid not in by_id:
            if c.get("kind") == "map":
                rows.setdefault("generated-map", {"asset_id": "generated-map", "type": "graphic",
                                                  "title": "Schematic maps (generated by this tool from gazetteer coordinates)",
                                                  "page_url": "", "author": "Historical Video Editor Skill",
                                                  "license": "Original work", "risk": 0, "uses": [], "credit": "Schematic map",
                                                  "provider": "generated", "notes": ""})["uses"].append(
                    {"timeline": [c["start"], round(c["start"] + c["duration"], 3)], "source_range": None, "clip": c["id"]})
            continue
        a = by_id[aid]
        m = a["meta"]
        r = rows.setdefault(aid, {
            "asset_id": aid, "type": a["media_type"], "provider": m.get("provider"), "source": m.get("source_label"),
            "title": m.get("title"), "page_url": m.get("page_url"), "media_url": m.get("media_url"),
            "author": m.get("author") or m.get("handle") or "", "date": m.get("date"),
            "license": (m.get("license") or {}).get("label"), "license_url": (m.get("license") or {}).get("url"),
            "risk": (m.get("license") or {}).get("risk"), "status": m.get("status"),
            "credit": c.get("credit", {}).get("text") if c.get("credit") else m.get("credit"),
            "notes": "; ".join(m.get("verify_notes") or []), "sha1": a.get("sha1"), "uses": []})
        r["uses"].append({"timeline": [c["start"], round(c["start"] + c["duration"], 3)],
                          "source_range": c.get("src_range"), "clip": c["id"]})
    out = list(rows.values())
    write_json(pdir / "reports" / "sources.json", out)
    with open(pdir / "reports" / "sources.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["asset_id", "type", "source", "title", "author", "license", "license_url", "risk", "page_url",
                    "media_url", "timeline_in", "timeline_out", "source_in", "source_out", "credit", "notes"])
        for r in out:
            for u in r["uses"]:
                sr = u.get("source_range") or [None, None]
                w.writerow([r["asset_id"], r["type"], r.get("source", ""), r.get("title", ""), r.get("author", ""),
                            r.get("license", ""), r.get("license_url", ""), r.get("risk", ""), r.get("page_url", ""),
                            r.get("media_url", ""), fmt_ts(u["timeline"][0]), fmt_ts(u["timeline"][1]),
                            "" if sr[0] is None else fmt_ts(sr[0]), "" if sr[1] is None else fmt_ts(sr[1]),
                            r.get("credit", ""), r.get("notes", "")])
    md = [f"# Sources — {tl['title']}", "", "| # | Type | Source / Author | Licence | Used at | Source range | Original page |",
          "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(out, 1):
        used = ", ".join(f"{fmt_ts(u['timeline'][0])}–{fmt_ts(u['timeline'][1])}" for u in r["uses"])
        srs = ", ".join(f"{fmt_ts(u['source_range'][0])}–{fmt_ts(u['source_range'][1])}" for u in r["uses"] if u.get("source_range"))
        md.append(f"| {i} | {r['type']} | {r.get('source') or r.get('provider')} / {r.get('author') or '—'} | "
                  f"{r.get('license')} | {used} | {srs or '—'} | {r.get('page_url') or '—'} |")
    (pdir / "reports" / "SOURCES.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return out


def youtube_description(pdir: Path, cfg: dict, sources: list[dict]) -> Path:
    tl = read_json(pdir / "timeline.json")
    sb = read_json(pdir / "storyboard.json")
    lang = tl.get("language", "uz")
    tpl_path = SKILL_ROOT / "templates" / "youtube_description.md"
    tpl = tpl_path.read_text(encoding="utf-8") if tpl_path.exists() else "{title}\n\n{chapters}\n\n{sources}"
    chapters = tl.get("chapters") or []
    if chapters and chapters[0]["start"] > 0:
        chapters = [{"start": 0, "title": "Intro"}] + chapters
    chap_txt = "\n".join(f"{fmt_yt(c['start'])} {c['title']}" for c in chapters) if len(chapters) >= 3 else ""
    src_lines = []
    for r in sources:
        if r.get("provider") == "generated":
            continue
        who = f" — {r['author']}" if r.get("author") else ""
        lic = r.get("license") or ""
        lic_url = f" ({r['license_url']})" if r.get("license_url") else ""
        src_lines.append(f"• {r.get('title') or r.get('source')}{who}. {r.get('source') or ''}. {lic}{lic_url}. {r.get('page_url')}")
    ai_used = any(r.get("notes") and "AI" in r["notes"] for r in sources)
    first = sb["scenes"][0]["narration"] if sb.get("scenes") else ""
    summary = " ".join(s["narration"] for s in sb["scenes"][:2])[:400] if sb.get("scenes") else ""
    labels = {
        "uz": {"chap": "Bo'limlar", "src": "Manbalar va litsenziyalar",
               "fair": "Ushbu video ta'limiy va tarixiy-tahliliy maqsadda tayyorlangan. Arxiv materiallari asosan Public Domain "
                       "va ochiq litsenziyalar (CC0, CC BY, CC BY-SA) asosida, muallif ko'rsatilgan holda ishlatilgan.",
               "ai": "Ba'zi tasvirlar rekonstruksiya/AI yordamida yaratilgan va videoda shunday belgilangan.",
               "maps": "Xaritalar sxematik bo'lib, aniq tarixiy chegaralarni aks ettirmaydi."},
        "ru": {"chap": "Таймкоды", "src": "Источники и лицензии",
               "fair": "Видео создано в образовательных и историко-аналитических целях. Архивные материалы использованы на "
                       "условиях Public Domain и открытых лицензий (CC0, CC BY, CC BY-SA) с указанием авторов.",
               "ai": "Некоторые изображения являются реконструкциями/созданы ИИ и помечены в кадре.",
               "maps": "Карты схематичны и не отражают точных исторических границ."},
        "en": {"chap": "Chapters", "src": "Sources & licences",
               "fair": "This video was produced for educational and historical commentary. Archive material is used under "
                       "Public Domain and open licences (CC0, CC BY, CC BY-SA) with attribution.",
               "ai": "Some images are reconstructions / AI-generated and are labelled on screen.",
               "maps": "Maps are schematic and do not show exact historical borders."},
    }.get(lang) or {}
    text = tpl.format(
        title=tl["title"], summary=summary or first[:300],
        chapters_heading=labels.get("chap", "Chapters"), chapters=chap_txt or "—",
        sources_heading=labels.get("src", "Sources"), sources="\n".join(src_lines) or "—",
        fair_use=labels.get("fair", ""), ai_note=labels.get("ai", "") if ai_used else "",
        maps_note=labels.get("maps", "") if any(r.get("provider") == "generated" for r in sources) else "",
        hashtags=" ".join("#" + slugify(x).replace("-", "") for x in ([tl["title"]] + list(
            dict.fromkeys(p for s in sb["scenes"] for p in s.get("places", [])))[:4])),
    )
    out = pdir / "reports" / "youtube_description.md"
    out.write_text(text, encoding="utf-8")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--codec", choices=["libx264", "libx265"])
    ap.add_argument("--4k", dest="four_k", action="store_true")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--reports-only", action="store_true")
    ap.add_argument("--config")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    setup_logging(a.verbose)
    cfg = load_config(a.config)
    pdir = project_dir(cfg, a.project)
    sources = build_sources(pdir, cfg)
    yd = youtube_description(pdir, cfg, sources)
    log.info("reports: %d sources, description %s", len(sources), yd)
    if a.reports_only:
        return
    out = encode(pdir, cfg, a.codec or cfg["render"]["codec"], a.four_k, a.preview)
    tl = read_json(pdir / "timeline.json")
    tl.setdefault("render", {})["final"] = str(out)
    write_json(pdir / "timeline.json", tl)
    print(out)


if __name__ == "__main__":
    main()
