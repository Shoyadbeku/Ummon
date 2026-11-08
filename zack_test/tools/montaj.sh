#!/bin/bash
# montaj.sh <kadrlar_papkasi> <ovoz.mp3> <chiqish.mp4> — PNG kadrlarni 24 fps MP4 ga yig'ib, ovoz qo'shadi (1080x1920)
F="$1"; A="$2"; O="$3"
ffmpeg -y -loglevel error -framerate 24 -pattern_type glob -i "$F/[0-9]*.png" -i "$A" \
  -vf "scale=1080:1920:flags=lanczos,unsharp=5:5:0.4,format=yuv420p" \
  -c:v libx264 -preset slow -crf 19 -c:a aac -b:a 192k -af "apad" -shortest -movflags +faststart "$O"
ffprobe -v error -show_entries format=duration -of default=nw=1 "$O"
