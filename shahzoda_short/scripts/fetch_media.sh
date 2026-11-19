#!/usr/bin/env bash
# Downloads all stock media used by the project (Mixkit Free License).
set -e
cd "$(dirname "$0")/../public/media"
V="474 1038 24621 2850 4743 478 14106 484 472 11942 32591 14756 14084 48509 21617 34314 4856 43390 4269 48506 22052 32559 50326 36190 46722"
for id in $V; do
  [ -s video/$id.mp4 ] && continue
  for q in 1080 720; do
    if curl -sfL -m 120 "https://assets.mixkit.co/videos/$id/$id-$q.mp4" -o video/$id.mp4; then echo "video $id ($q)"; break; fi
  done
done
for id in 601 606 168 599; do
  [ -s music/$id.mp3 ] || curl -sfL -m 60 "https://assets.mixkit.co/music/$id/$id.mp3" -o music/$id.mp3 && echo "music $id"
done
for id in 1492 1490 2908 788 784 3005 2350 166 3115 772 2918 478 22; do
  [ -s sfx/$id.mp3 ] || curl -sfL -m 60 "https://assets.mixkit.co/active_storage/sfx/$id/$id-preview.mp3" -o sfx/$id.mp3 && echo "sfx $id"
done
