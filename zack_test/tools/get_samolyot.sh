#!/bin/bash
# "Samolyot derazalari" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan Josh Pete David; do curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Sitting_Idle_5 Pointing_Forward Looking_Down Idle_14 Head_Nod_Yes Reacting; do
  curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky concrete_pavement painted_plaster_wall
K=/tmp/claude-0/assets/bk
$H/bk_get.sh "airplane" 536fac67 $K      # Airbus A320
$H/bk_get.sh "airplane" 7250f009 $K      # illyuminator ramkasi
[ -x /tmp/claude-0/tools/node_modules/.bin/gltf-transform ] || (mkdir -p /tmp/claude-0/tools && cd /tmp/claude-0/tools && npm i --silent @gltf-transform/cli@4.1.1)
for f in $K/{536fac67,7250f009}.glb; do /tmp/claude-0/tools/node_modules/.bin/gltf-transform copy $f ${f%.glb}_u.glb; done
ls -la $D/chars $D/anims | awk '{print $5, $9}'
