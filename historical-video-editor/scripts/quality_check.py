#!/usr/bin/env python3
"""Step 15: automated quality control of the exported video and of the edit.

Technical checks (ffprobe / ffmpeg)
  container, codec, resolution, 16:9, fps, AAC audio, duration vs. timeline,
  integrated loudness / true peak (ebur128), black segments, long silences, frozen frames
Editorial checks (timeline / media index)
  every clip that shows third-party material has an on-screen credit covering it,
  licence risk of every used asset <= allowed, no asset segment used twice,
  visual ratio vs. target, scenes without visuals (fallback cards), anachronism and
  AI/reconstruction flags, render errors

Writes reports/qc_report.json + qc_report.md. Exit code 1 if a blocking check fails.

Usage: python scripts/quality_check.py --project <slug> [--video file.mp4]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_config, log, media_info, project_dir, read_json, run, setup_logging, write_json  # noqa: E402


def ebur128(path: Path) -> dict:
    p = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-"],
            check=False)
    tail = p.stderr[p.stderr.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", tail)
    tp = re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail)
    lra = re.search(r"LRA:\s+(-?[\d.]+) LU", tail)
    return {"integrated_lufs": float(i.group(1)) if i else None, "true_peak_db": float(tp.group(1)) if tp else None,
            "lra": float(lra.group(1)) if lra else None}


def detect(path: Path, max_black: float, max_sil: float) -> dict:
    p = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vf", "scale=320:-2,blackdetect=d=0.4:pix_th=0.08,freezedetect=n=-60dB:d=4",
             "-af", f"silencedetect=n=-45dB:d={max_sil}", "-f", "null", "-"], check=False)
    blacks, sil, frz = [], [], []
    for line in p.stderr.splitlines():
        if "black_start" in line:
            m = re.search(r"black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)", line)
            if m:
                blacks.append([float(m.group(1)), float(m.group(3))])
        elif "silence_end" in line:
            m = re.search(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", line)
            if m:
                sil.append([round(float(m.group(1)) - float(m.group(2)), 2), float(m.group(2))])
        elif "freeze_duration" in line:
            m = re.search(r"freeze_duration: ([\d.]+)", line)
            if m:
                frz.append(float(m.group(1)))
    return {"black": [b for b in blacks if b[1] > max_black], "silence": sil, "frozen": frz}


def check(pdir: Path, cfg: dict, video: Path | None) -> dict:
    tl = read_json(pdir / "timeline.json")
    idx = read_json(pdir / "media_index.json") if (pdir / "media_index.json").exists() else {"assets": []}
    by_id = {a["asset_id"]: a for a in idx["assets"]}
    q = cfg["quality"]
    res: list[dict] = []

    def add(name, ok, detail="", blocking=True):
        res.append({"check": name, "ok": bool(ok), "blocking": blocking, "detail": detail})

    # ---------------- editorial
    credits = [o for o in tl["overlays"] if o["type"] == "credit"]
    uncovered = []
    for c in tl["clips"]:
        if c.get("kind") in ("video", "image", "map"):
            covered = any(o["start"] <= c["start"] + 0.05 and o["end"] >= c["start"] + c["duration"] - 0.05 for o in credits)
            if not covered:
                uncovered.append(c["id"])
    add("source credit on every third-party shot", not uncovered, f"missing: {uncovered[:12]}")
    risky = []
    max_risk = cfg["licensing"]["max_allowed_risk"]
    for c in tl["clips"]:
        a = by_id.get(c.get("asset_id"))
        if a and (a["meta"].get("license") or {}).get("risk", 4) > max_risk and a["meta"].get("status") != "fair_use_review":
            risky.append(c["id"])
    add(f"all licences risk <= {max_risk}", not risky, f"clips: {risky[:12]}")
    fair = [c["id"] for c in tl["clips"] if by_id.get(c.get("asset_id"), {}).get("meta", {}).get("status") == "fair_use_review"]
    add("fair-use excerpts reviewed by a human", not fair, f"review clips: {fair}", blocking=False)
    overlaps = []
    ranges: dict[str, list] = {}
    for c in tl["clips"]:
        if c.get("asset_id"):
            r = (c.get("in_point", 0), c.get("out_point", c.get("in_point", 0) + c["duration"]))
            for r0 in ranges.get(c["asset_id"], []):
                if c["kind"] == "image" or (r[0] < r0[1] - 0.05 and r[1] > r0[0] + 0.05):
                    overlaps.append(c["id"])
            ranges.setdefault(c["asset_id"], []).append(r)
    add("no repeated footage", not overlaps, f"repeated: {overlaps[:12]}", blocking=False)
    tgt, got = tl["visual_ratio_target"], tl["visual_ratio_achieved"]
    add("visual ratio close to target (video share)", got.get("video", 0) >= tgt["video"] - 0.25,
        f"target {tgt} achieved {got}", blocking=False)
    add("all scenes have licensed visuals", not tl.get("scenes_missing_visuals"),
        f"fallback cards in {tl.get('scenes_missing_visuals')}", blocking=False)
    flags = []
    for c in tl["clips"]:
        m = by_id.get(c.get("asset_id"), {}).get("meta", {})
        for n in m.get("verify_notes") or []:
            if "anachronism" in n or "AI" in n:
                flags.append(f"{c['id']}: {n}")
    add("no anachronism / unlabelled AI material", not flags, "; ".join(flags[:8]), blocking=False)
    errs = (tl.get("render") or {}).get("errors") or {}
    add("all segments rendered", not errs, str(errs)[:300], blocking=False)

    # ---------------- technical
    video = video or Path((tl.get("render") or {}).get("final", ""))
    tech = {}
    if video and video.exists():
        info = media_info(video)
        tech["info"] = info
        W, H = info["width"], info["height"]
        add("container mp4", video.suffix.lower() == ".mp4")
        add("video codec h264/hevc", info["vcodec"] in ("h264", "hevc"), info["vcodec"])
        add("resolution Full HD or 4K", (W, H) in ((1920, 1080), (3840, 2160)), f"{W}x{H}",
            blocking=not (tl.get("render") or {}).get("preview"))
        add("aspect ratio 16:9", abs(W / max(1, H) - 16 / 9) < 0.01, f"{W}x{H}")
        add("fps 25 or 30", round(info["fps"]) in (24, 25, 30, 50, 60), str(info["fps"]))
        add("audio AAC", info["acodec"] == "aac", info["acodec"])
        dev = abs(info["duration"] - tl["total_duration"]) / max(1, tl["total_duration"])
        add("duration matches timeline", dev <= q["max_duration_deviation"], f"{info['duration']:.2f}s vs {tl['total_duration']:.2f}s")
        loud = ebur128(video)
        tech["loudness"] = loud
        if loud["integrated_lufs"] is not None:
            narr = bool(tl["audio"].get("narration"))
            add("loudness ≈ -14 LUFS", (not narr) or abs(loud["integrated_lufs"] - cfg["audio"]["final_lufs"]) <= q["loudness_tolerance_lu"],
                f"{loud}", blocking=False)
            add("true peak <= -1 dBTP (+0.5 tol)", loud["true_peak_db"] is None or loud["true_peak_db"] <= cfg["audio"]["true_peak_db"] + 0.5,
                f"{loud['true_peak_db']}", blocking=False)
        d = detect(video, q["max_black_sec"], q["max_silence_sec"])
        tech["detect"] = d
        add("no long black segments", not d["black"], str(d["black"][:5]), blocking=False)
        add("no long silences", (not tl["audio"].get("narration")) or not d["silence"], str(d["silence"][:5]), blocking=False)
        add("no frozen picture > 4s", not d["frozen"], str(d["frozen"][:5]), blocking=False)
    else:
        add("final video exists", False, str(video))
    blocking_fail = [r for r in res if r["blocking"] and not r["ok"]]
    report = {"passed": not blocking_fail, "checks": res, "technical": tech}
    write_json(pdir / "reports" / "qc_report.json", report)
    md = ["# Quality control", "", f"**Result: {'PASS' if report['passed'] else 'FAIL'}**", "",
          "| Check | Result | Blocking | Detail |", "|---|---|---|---|"]
    for r in res:
        md.append(f"| {r['check']} | {'✅' if r['ok'] else ('❌' if r['blocking'] else '⚠️')} | {'yes' if r['blocking'] else 'no'} | {str(r['detail'])[:180]} |")
    (pdir / "reports" / "qc_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--video")
    ap.add_argument("--config")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    setup_logging(a.verbose)
    cfg = load_config(a.config)
    pdir = project_dir(cfg, a.project)
    rep = check(pdir, cfg, Path(a.video) if a.video else None)
    for r in rep["checks"]:
        log.info("%s %s %s", "OK  " if r["ok"] else ("FAIL" if r["blocking"] else "WARN"), r["check"], r["detail"] if not r["ok"] else "")
    print(pdir / "reports" / "qc_report.md")
    sys.exit(0 if rep["passed"] else 1)


if __name__ == "__main__":
    main()
