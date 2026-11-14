#!/usr/bin/env bash
# Resumable render: video in chunks (skips finished ones), audio separately, then join.
set -euo pipefail
cd "$(dirname "$0")"
TOTAL=21855 # = durationInFrames of HistoryVideo (see src/HistoryVideo.tsx)
CH=2200
mkdir -p out/chunks
i=0
for ((s=0; s<TOTAL; s+=CH)); do
  e=$((s+CH-1)); ((e>=TOTAL)) && e=$((TOTAL-1))
  f=$(printf "out/chunks/c%02d.mp4" $i)
  if [ ! -f "$f" ]; then
    npx remotion render HistoryVideo "$f.part.mp4" --frames=$s-$e --muted --concurrency=4 --crf=20 --log=error
    mv "$f.part.mp4" "$f"
  fi
  echo "chunk $i done ($s-$e)"
  i=$((i+1))
done
[ -f out/audio.aac ] || npx remotion render HistoryVideo out/audio.aac --codec=aac --log=error
ls out/chunks/c*.mp4 | sed "s|^out/|file '|;s|$|'|" > out/list.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i out/list.txt -i out/audio.aac -map 0:v -map 1:a -c copy -movflags +faststart out/meri_selest.mp4
echo ALL_DONE
