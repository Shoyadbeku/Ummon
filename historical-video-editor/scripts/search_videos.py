#!/usr/bin/env python3
"""Step 5-5: search video material for every scene of storyboard.json
across all configured providers (see config.yaml -> search.video_providers).

Writes <project>/candidates_video.json, reports/search_report_video.json and
reports/manual_search_links.md (links for platforms without API access).

Usage:
  python scripts/search_videos.py --project <slug> [--providers internet_archive,wikimedia_commons]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_config, project_dir, read_json, setup_logging  # noqa: E402
from search_core import run_search  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--providers", help="comma separated subset of providers")
    ap.add_argument("--config")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    setup_logging(a.verbose)
    cfg = load_config(a.config)
    pdir = project_dir(cfg, a.project)
    sb = read_json(pdir / "storyboard.json")
    rep = run_search(sb, cfg, "video", pdir, a.providers.split(",") if a.providers else None)
    print(json.dumps(rep, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
