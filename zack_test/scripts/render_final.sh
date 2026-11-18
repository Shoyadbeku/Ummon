#!/bin/bash
# Final render of all shots (resumable: existing frames are skipped).
# Approved setting: 540x960, 16 samples + OIDN; upscaled to 1080x1920 in assemble_video.py
cd "$(dirname "$0")"
for s in s1 s1b s2 s3 s4 s5 s6; do
  python3 render.py "$s" --res 540x960 --samples 16 --out ../renders/final 2>&1 | grep --line-buffered -E '\[render\]|Error|Traceback'
done
echo ALL_DONE
