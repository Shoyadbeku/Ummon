#!/bin/bash
# "Uzoq o'tirish -> tromb -> o'pka tromboemboliyasi" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan Kate Josh David Pete; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Sitting_Idle_5 Sitting_Idle_3 Sitting_Idle_4 Sitting_Disbelief_3 Sit_To_Stand Stand_Up Female_Walk Catwalk_Walk_Stop_2 \
         Dying_6 Dizzy_Idle Breathing_Idle Typing Injured_Stumble_Idle Reacting; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky laminate_floor_02 painted_plaster_wall \
  potted_plant_01 Sofa_01 WoodenTable_01
K=/tmp/claude-0/assets/bk; mkdir -p $K
[ -s $K/7250f009.glb ] || $H/bk_get.sh "airplane" 7250f009 $K      # illyuminator ramkasi
[ -x /tmp/claude-0/tools/node_modules/.bin/gltf-transform ] || (mkdir -p /tmp/claude-0/tools && cd /tmp/claude-0/tools && npm i --silent @gltf-transform/cli@4.1.1)
[ -s $K/7250f009_u.glb ] || /tmp/claude-0/tools/node_modules/.bin/gltf-transform copy $K/7250f009.glb $K/7250f009_u.glb
ls -la $D/chars $D/anims $K | awk '{print $5, $9}'
