#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920 ga kattalashtirish) va ovozni qo'shish
D=$(cd "$(dirname "$0")" && pwd)
F=${FRAMES_DIR:-/tmp/claude-0/kana_frames}
OUTV=${1:-$D/kana_tishlashi.mp4}
ffmpeg -y -loglevel error -framerate 24 -start_number 1 -i "$F/%04d.png" -i "$D/ovoz.mp3" \
  -vf "scale=1080:1920:flags=lanczos,unsharp=5:5:0.6,format=yuv420p" \
  -c:v libx264 -preset slow -crf 18 -c:a aac -b:a 192k -af "apad" -shortest -movflags +faststart "$OUTV"
ls -la "$OUTV"
