#!/usr/bin/env python3
"""Build Historical_Video_Editor_Skill.zip (skill folder at archive root, without
project outputs, caches, secrets).

Usage: python scripts/package_skill.py [--out ../Historical_Video_Editor_Skill.zip]
"""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", ".venv", ".git"}
EXCLUDE_FILES = {".env"}


def include(p: Path) -> bool:
    rel = p.relative_to(ROOT)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return False
    if p.name in EXCLUDE_FILES or p.suffix in (".pyc", ".part", ".tmp"):
        return False
    if rel.parts[0] == "output" and p.name != ".gitkeep":
        return False
    return p.is_file()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT.parent / "Historical_Video_Editor_Skill.zip"))
    a = ap.parse_args()
    files = sorted(p for p in ROOT.rglob("*") if include(p))
    with zipfile.ZipFile(a.out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in files:
            z.write(f, Path(ROOT.name) / f.relative_to(ROOT))
    print(f"{a.out}: {len(files)} files, {Path(a.out).stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
