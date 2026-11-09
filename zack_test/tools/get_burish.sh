#!/bin/bash
# "Barmoqlar nega burishadi" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan Olivia; do curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Sitting_Idle_2 Sitting_Idle_3 Lifting Looking_Down Reacting Picking_Up_Object Breathing_Idle; do
  curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky kloofendal_overcast_puresky studio_small_09 \
  long_white_tiles marble_tiles painted_plaster_wall asphalt_02 laminate_floor_02 rubber_duck_toy vintage_microscope
K=/tmp/claude-0/assets/bk
$H/bk_get.sh "bathtub" 16bfcc74 $K          # erkin turuvchi oval vanna
$H/bk_get.sh "car tire" 08efeffa $K         # shina (protektor)
$H/bk_get.sh "car" c3c28d91 $K              # Audi e-tron GT
$H/bk_get.sh "towel" 6647001a $K            # sochiqlar
[ -x /tmp/claude-0/tools/node_modules/.bin/gltf-transform ] || (mkdir -p /tmp/claude-0/tools && cd /tmp/claude-0/tools && npm i --silent @gltf-transform/cli@4.1.1)
for f in $K/{16bfcc74,08efeffa,c3c28d91,6647001a}.glb; do
  /tmp/claude-0/tools/node_modules/.bin/gltf-transform copy $f ${f%.glb}_u.glb; done
ls -la $D/chars $D/anims | awk '{print $5, $9}'
