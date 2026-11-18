#!/usr/bin/env bash
# Re-downloads the Mixkit stock media (not committed: Mixkit's licence forbids
# redistributing the raw files) and rebuilds the pre-cropped 9:16 clips, music and SFX
# in public/. Commons images, the voice and map data are committed already.
set -euo pipefail
cd "$(dirname "$0")"
RAW=.media_raw; mkdir -p "$RAW" public/clips public/audio

get_video() { # id
  for r in 1080 720; do
    if curl -sf -o "$RAW/mk_$1.mp4" "https://assets.mixkit.co/videos/$1/$1-$r.mp4"; then return; fi
  done
  echo "failed: $1" >&2; exit 1
}

# name  mixkit-id  start  duration  x-centre(0..1)  speed
CLIPS="cranes 31450 1.5 2.0 0.5 1
cranesun 3970 3 1.6 0.46 1
flag 42108 0.3 1.6 0.32 1
shibuya 30137 0.5 2.8 0.5 1
father 7761 4 1.8 0.6 1
boy 4720 0.5 2.4 0.45 1
books 21587 1 1.6 0.42 1
construct 9686 3 2.0 0.5 3
aerial 42333 1.5 1.6 0.5 1
chess 35587 2 3.0 0.47 1
up 40673 1 3.6 0.5 1
money 18305 5.5 1.6 0.62 1
cash 47005 1 3.0 0.5 1
library 21595 2 4.0 0.5 1"

while read -r n src st du xc sp; do
  [ -f "$RAW/mk_$src.mp4" ] || get_video "$src"
  t=$(python3 -c "print($du*$sp)")
  ffmpeg -v error -y -ss "$st" -i "$RAW/mk_$src.mp4" -t "$t" -an \
    -vf "setpts=PTS/$sp,scale=-2:1920:flags=lanczos,crop=1080*1.12:1920:max(0\,min(iw-ow\,iw*$xc-ow/2)):0,scale=1210:2150,fps=30" \
    -c:v libx264 -preset veryfast -crf 17 -g 15 -pix_fmt yuv420p "public/clips/$n.mp4"
  echo "clip $n"
done <<< "$CLIPS"

[ -f "$RAW/mk_43321.mp4" ] || get_video 43321
ffmpeg -v error -y -ss 0.5 -i "$RAW/mk_43321.mp4" -t 4.5 -an \
  -vf "scale=1210:2150:force_original_aspect_ratio=increase,crop=1210:2150,fps=30" \
  -c:v libx264 -preset veryfast -crf 17 -g 15 -pix_fmt yuv420p public/clips/climb.mp4

# Music: "We Will Get It" – Eugenio Mininni (Mixkit #598); offset puts its drop at 26.0 s
curl -sf -o "$RAW/mus_598.mp3" https://assets.mixkit.co/music/598/598.mp3
ffmpeg -v error -y -ss 26.95 -t 36 -i "$RAW/mus_598.mp3" -ar 48000 public/audio/music.wav

for x in 2782 1491 1467 1464 1478 1687 2152 2908 2902 2350 1474; do
  curl -sf -o "$RAW/sfx_$x.mp3" "https://assets.mixkit.co/active_storage/sfx/$x/$x-preview.mp3"
  ffmpeg -v error -y -i "$RAW/sfx_$x.mp3" -ar 48000 "public/audio/sfx_$x.wav"
done
echo "media ready"
