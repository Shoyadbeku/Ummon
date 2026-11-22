#!/bin/bash
# Re-downloads the Mixkit stock media (not stored in git: Mixkit's license forbids
# redistributing the raw files) and transcodes clips for fast seeking in Remotion.
# Usage (from gta_video/):  bash scripts/fetch_media.sh
set -e
mkdir -p public/media public/music public/sfx .cache/raw
while read -r id name; do
  [ -f "public/media/$name.mp4" ] && continue
  slug=$(awk -v i="$id" '$1==i{print $2; exit}' scripts/mixkit_slugs.txt)
  url="https://assets.mixkit.co/videos/$id/$id-1080.mp4"
  if ! curl -sfI "$url" >/dev/null; then
    url=$(curl -s "https://mixkit.co/free-stock-video/$slug-$id/" | grep -oE 'https://assets\.mixkit\.co/[^"]+(1080|720)\.mp4' | sort -r | head -1)
  fi
  echo "video $name <- $url"
  curl -sL -o ".cache/raw/$name.mp4" "$url"
  ffmpeg -hide_banner -loglevel error -y -i ".cache/raw/$name.mp4" -an -vf "fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2" \
    -c:v libx264 -preset veryfast -crf 19 -g 15 -pix_fmt yuv420p -movflags +faststart "public/media/$name.mp4"
done < scripts/mixkit_clips.txt
for id in 283 612 140 399 598 605 370 678; do
  [ -f "public/music/$id.mp3" ] || curl -sL -o "public/music/$id.mp3" "https://assets.mixkit.co/music/$id/$id.mp3"
done
while read -r name id; do
  [ -f "public/sfx/$name.mp3" ] || curl -sL -o "public/sfx/$name.mp3" "https://assets.mixkit.co/active_storage/sfx/$id/$id-preview.mp3"
done < scripts/sfx_ids.txt
echo done
