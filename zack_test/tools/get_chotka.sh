#!/bin/bash
# "Unitaz aerozoli va tish cho'tkasi" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
[ -s $D/chars/Megan.fbx ] || curl -sSL -o $D/chars/Megan.fbx "$B/character_refined/Megan.fbx" &
for a in Idle Breathing_Idle Button_Pushing Female_Walk Bored Laying_Sleeping; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky long_white_tiles floor_tiles_06 interior_tiles painted_plaster_wall potted_plant_01
# BlenderKit (bepul): unitaz, tish cho'tkasi, lavabo -> Draco'ni yechish
BK=/tmp/claude-0/assets/bk
mkdir -p /tmp/claude-0/tools && [ -x /tmp/claude-0/tools/node_modules/.bin/gltf-transform ] || (cd /tmp/claude-0/tools && npm i --silent @gltf-transform/cli@4.1.1)
for p in "toilet ceramic white:6a342733" "toothbrush:492e383d" "toothbrushes:f70efd3c" "bathroom sink:a541b293"; do
  q=${p%%:*}; id=${p##*:}
  [ -s $BK/${id}_u.glb ] && continue
  "$H/bk_get.sh" "$q" $id $BK && /tmp/claude-0/tools/node_modules/.bin/gltf-transform copy $BK/$id.glb $BK/${id}_u.glb
done
ls -la $D/chars $D/anims | awk '{print $5, $9}'
