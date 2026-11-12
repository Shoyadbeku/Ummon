#!/bin/bash
# Render shots to renders/frames/shotN/f_####.png (resumable: existing frames are skipped).
# usage: bash render_all.sh 1 2 3 ...   (PCT env var, default 50 -> 540x960, upscaled in edit.sh)
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(cd "$HERE/../.." && pwd)
PCT=${PCT:-50}
for n in "$@"; do
  out="$ROOT/renders/frames/shot$n"; mkdir -p "$out"
  echo "=== shot $n start $(date +%T)"
  (cd /tmp && python3 "$HERE/film.py" --shot "$n" --pct "$PCT" --out "$out/") > "$ROOT/renders/log_shot$n.txt" 2>&1
  echo "=== shot $n done $(date +%T) frames: $(ls "$out" | wc -l)"
done
