#!/usr/bin/env bash
# Downloads the Mixkit stock clips (Mixkit Free License) into public/clips
# and rebuilds the speed-ramped training clip. Run from the project root.
set -euo pipefail
mkdir -p public/clips
for id in 46365 49226 46368 6562 5992 11850 47020 46366 48805 43484 42541 43501 43495 4262 9585 30326 45912 4064 30601 21751 17398 2923 43494; do
  [ -f public/clips/$id.mp4 ] && continue
  curl -fsSL -o public/clips/$id.mp4 "https://assets.mixkit.co/videos/$id/$id-1080.mp4" \
    || curl -fsSL -o public/clips/$id.mp4 "https://assets.mixkit.co/videos/$id/$id-720.mp4"
done
ffmpeg -loglevel error -y -ss 2 -t 3.2 -i public/clips/42541.mp4 -filter_complex \
 "[0:v]split=3[a][b][c];[a]trim=0:0.25,setpts=(PTS-STARTPTS)/0.5[a1];[b]trim=0.25:1.95,setpts=(PTS-STARTPTS)/1.6[b1];[c]trim=1.95:2.25,setpts=(PTS-STARTPTS)/0.6[c1];[a1][b1][c1]concat=n=3:v=1,fps=30,format=yuv420p[v]" \
 -map "[v]" -an -c:v libx264 -crf 18 public/clips/42541r.mp4
echo done
