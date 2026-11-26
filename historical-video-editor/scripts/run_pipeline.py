#!/usr/bin/env python3
"""One-command pipeline (all 17 steps). Every step is also a standalone script.

  1-4   analyze_script.py   script -> scenes, context, multilingual queries
  (opt) audio_editor tts    narration via edge-tts when no audio is supplied
  5     search_videos.py    multi-platform video search
  6     search_images.py    images (Yandex/Google/Commons/museums/...)
  7-8   verify_license.py   original page, licence, link health, anachronisms
  9-10  download_media.py   best approved assets, dedupe, shot detection
  (opt) audio_editor beats  music beat grid
  11    scene_builder.py    narration sync, ratio 80/15/5, transitions, overlays
  12    video_editor.py     segment rendering, Ken Burns, parallax, maps, xfades
  13    source_overlay.py   credits, lower thirds, date cards, subtitles (ASS)
  14    audio_editor mix    music + ducking + ambience + SFX + J/L cuts, -14 LUFS
  16    export_video.py     grade, grain, overlays, H.264/H.265 + AAC, reports
  15    quality_check.py    QC of the exported file and of the edit
  17    reports             sources.json/csv, SOURCES.md, youtube_description.md, licence report

Usage:
  python scripts/run_pipeline.py --script story.txt --title "Amir Temur" [--narration voice.mp3]
         [--duration 480] [--lang uz] [--tts] [--preview] [--from verify] [--project slug]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import load_config, log, project_dir, setup_logging, slugify  # noqa: E402

STEPS = ["analyze", "tts", "search_videos", "search_images", "verify", "download", "beats", "build",
         "render", "overlay", "mix", "export", "qc"]


def py(script: str, *args) -> list[str]:
    return [sys.executable, str(HERE / script), *map(str, args)]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--script", help="script text file (required for the analyze step)")
    ap.add_argument("--title", required=True)
    ap.add_argument("--project")
    ap.add_argument("--narration")
    ap.add_argument("--duration", type=float)
    ap.add_argument("--lang")
    ap.add_argument("--tts", action="store_true", help="generate narration with edge-tts")
    ap.add_argument("--preview", action="store_true", help="fast 960x540 render for checking the edit")
    ap.add_argument("--four-k", action="store_true")
    ap.add_argument("--codec", choices=["libx264", "libx265"])
    ap.add_argument("--from", dest="start", choices=STEPS, default="analyze")
    ap.add_argument("--to", dest="stop", choices=STEPS, default="qc")
    ap.add_argument("--skip", default="", help="comma separated steps to skip")
    ap.add_argument("--video-providers")
    ap.add_argument("--image-providers")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--config")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    setup_logging(a.verbose)
    cfg = load_config(a.config)
    slug = a.project or slugify(a.title)
    pdir = project_dir(cfg, slug)
    common = ["--project", slug] + (["--config", a.config] if a.config else [])
    skip = set(filter(None, a.skip.split(",")))
    if not a.tts:
        skip.add("tts")
    cmds = {
        "analyze": py("analyze_script.py", "--script", a.script or "", "--title", a.title, *common,
                      *(["--narration", a.narration] if a.narration else []),
                      *(["--duration", a.duration] if a.duration else []), *(["--lang", a.lang] if a.lang else [])),
        "tts": py("audio_editor.py", "tts", *common),
        "search_videos": py("search_videos.py", *common, *(["--providers", a.video_providers] if a.video_providers else [])),
        "search_images": py("search_images.py", *common, *(["--providers", a.image_providers] if a.image_providers else [])),
        "verify": py("verify_license.py", *common),
        "download": py("download_media.py", *common),
        "beats": py("audio_editor.py", "beats", *common),
        "build": py("scene_builder.py", *common),
        "render": py("video_editor.py", *common, "--jobs", a.jobs, *(["--preview"] if a.preview else [])),
        "overlay": py("source_overlay.py", *common),
        "mix": py("audio_editor.py", "mix", *common),
        "export": py("export_video.py", *common, *(["--preview"] if a.preview else []), *(["--4k"] if a.four_k else []),
                     *(["--codec", a.codec] if a.codec else [])),
        "qc": py("quality_check.py", *common),
    }
    optional = {"beats", "tts", "qc"}
    i0, i1 = STEPS.index(a.start), STEPS.index(a.stop)
    if "analyze" in STEPS[i0:i1 + 1] and not a.script and "analyze" not in skip:
        ap.error("--script is required for the analyze step")
    timings = {}
    for step in STEPS[i0:i1 + 1]:
        if step in skip:
            continue
        t0 = time.time()
        log.info("━━ step %s", step)
        p = subprocess.run(cmds[step])
        timings[step] = round(time.time() - t0, 1)
        if p.returncode != 0:
            if step in optional:
                log.warning("step %s returned %d (optional, continuing)", step, p.returncode)
                continue
            log.error("step %s failed (exit %d). Fix and resume with --from %s", step, p.returncode, step)
            sys.exit(p.returncode)
    log.info("done in %s — project folder: %s", timings, pdir)


if __name__ == "__main__":
    main()
