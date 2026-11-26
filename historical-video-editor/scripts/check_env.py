#!/usr/bin/env python3
"""Environment / integration self-check.

Shows which binaries, Python packages, API keys and providers are available, and (with
--ping) whether each free provider answers from this network. Nothing is faked: a provider
is reported "ready" only if its requirements are met, "reachable" only if a real request
succeeded.

Usage: python scripts/check_env.py [--ping]
"""
from __future__ import annotations

import argparse
import importlib
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import Http, ffmpeg_has, load_config, run  # noqa: E402
from providers.base import REGISTRY, ProviderUnavailable  # noqa: E402

PINGS = {
    "internet_archive": ("https://archive.org/advancedsearch.php", {"q": "samarkand", "rows": 1, "output": "json", "fl[]": "identifier"}),
    "wikimedia_commons": ("https://commons.wikimedia.org/w/api.php", {"action": "query", "meta": "siteinfo", "format": "json"}),
    "library_of_congress": ("https://www.loc.gov/photos/", {"q": "samarkand", "fo": "json", "c": 1}),
    "met_museum": ("https://collectionapi.metmuseum.org/public/collection/v1/objects/451958", {}),
    "openverse": ("https://api.openverse.org/v1/images/", {"q": "samarkand", "page_size": 1}),
    "rutube": ("https://rutube.ru/api/search/video/", {"query": "samarkand"}),
}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ping", action="store_true", help="send one real request to each free provider")
    ap.add_argument("--config")
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    ok = True
    print("== Binaries")
    for b in ("ffmpeg", "ffprobe", "yt-dlp", "fc-match"):
        path = shutil.which(b)
        print(f"  {'✅' if path else ('❌' if b in ('ffmpeg', 'ffprobe') else '⚠️ ')} {b:9s} {path or 'not found'}")
        ok &= bool(path) or b not in ("ffmpeg", "ffprobe")
    if shutil.which("ffmpeg"):
        print("  ffmpeg:", run(["ffmpeg", "-version"]).stdout.splitlines()[0])
        for f in ("ass", "drawtext", "xfade", "loudnorm", "sidechaincompress", "zoompan", "libx264", "libx265"):
            have = ffmpeg_has(f)
            print(f"    {'✅' if have else ('⚠️ ' if f == 'libx265' else '❌')} {f}")
            ok &= have or f == "libx265"
    print("== Python packages")
    for m, req in (("requests", 1), ("yaml", 1), ("PIL", 1), ("numpy", 1), ("dotenv", 0), ("yt_dlp", 0),
                   ("edge_tts", 0), ("faster_whisper", 0), ("pytest", 0)):
        try:
            importlib.import_module(m)
            print(f"  ✅ {m}")
        except ImportError:
            print(f"  {'❌' if req else '⚠️ '} {m}{' (optional)' if not req else ''}")
            ok &= not req
    print("== Providers")
    from providers import archives, platforms, search_engines, stock  # noqa: F401  (registers providers)
    http = Http(cfg)
    for name, cls in REGISTRY.items():
        try:
            cls(cfg, http)
            state = "ready"
        except ProviderUnavailable as e:
            state = f"unavailable — {e}"
        line = f"  {'✅' if state == 'ready' else '⚪'} {name:22s} {state}"
        if a.ping and state == "ready" and name in PINGS:
            url, params = PINGS[name]
            try:
                r = http.request("GET", url, params=params, timeout=20)
                line += f" | ping HTTP {r.status_code}"
            except Exception as e:  # noqa: BLE001
                line += f" | ping failed: {str(e)[:80]}"
        print(line)
    print("\nRESULT:", "core requirements OK" if ok else "missing core requirements (see ❌)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
