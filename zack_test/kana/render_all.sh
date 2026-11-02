#!/bin/bash
# Uch sahnani ketma-ket render qiladi (to'xtab qolsa, qayta ishga tushirsa davom etadi)
D=$(cd "$(dirname "$0")" && pwd)
export OUT=${OUT:-/tmp/claude-0/kana_frames/} PCT=${PCT:-50} SAMPLES=${SAMPLES:-8} SKIP_EXISTING=1
PY=${PY:-/tmp/claude-0/bvenv/bin/python}
for s in set_grass set_room set_skin; do
  echo "== $s $(date)"; $PY -I "$D/$s.py" --render 2>&1 | grep -E "RENDERED|Error|Traceback"
done
echo "DONE $(date)"
