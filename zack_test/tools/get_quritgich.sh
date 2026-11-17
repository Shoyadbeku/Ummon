#!/bin/bash
# "Qo'l quritgich — bakteriyalar" videosi uchun assetlar (hammasi bepul, login kerak emas).
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
[ -s $D/chars/Brian.fbx ] || curl -sSL -o $D/chars/Brian.fbx "$B/character_refined/Brian.fbx" &
for a in Walking_21 Idle_14 Button_Pushing Reacting Rejected Thoughtful_Head_Shake; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
python3 -I "$(dirname "$0")/ph_get.py" interior_tiles potted_plant_01 concrete_pavement painted_plaster_wall kloofendal_48d_partly_cloudy_puresky
# BlenderKit (bepul, royalty free): unitaz, pissuar, rakovina, Petri idishi -> Draco'ni yechish
BK=/tmp/claude-0/assets/bk; mkdir -p /tmp/claude-0/tools
[ -x /tmp/claude-0/tools/node_modules/.bin/gltf-transform ] || (cd /tmp/claude-0/tools && npm i --silent @gltf-transform/cli@4.1.1)
for qa in "toilet ceramic white:6a342733" "urinal:3c10750c" "bathroom sink:a541b293" "petri dish:2ce86051"; do
  q=${qa%%:*}; id=${qa##*:}
  [ -s $BK/${id}_u.glb ] && continue
  "$(dirname "$0")/bk_get.sh" "$q" $id $BK && /tmp/claude-0/tools/node_modules/.bin/gltf-transform copy $BK/$id.glb $BK/${id}_u.glb
done
ls -la $D/chars $D/anims $BK | awk '{print $5, $9}'
