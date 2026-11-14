#!/bin/bash
# "Balkondan yiqilgan bola" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Brian James Jody Swat; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Sitting_Drinking Scared Fast_Run Sprint Goalkeeper_Catch_4 Holding_Idle Carrying Catwalk_Walk_Forward_01 \
         Female_Walk Sad_Idle Reacting Angry_Point Catwalk_Walk_Forward_02 Look_Around Annoyed_Head_Shake; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky asphalt_02 concrete_pavement painted_plaster_wall laminate_floor_02 \
  red_brick_03 white_stucco outdoor_table_chair_set_01 street_lamp_01 fire_hydrant potted_plant_01 rubber_duck_toy planter_box_01
$H/bk_get.sh "car" c3c28d91 /tmp/claude-0/assets/bk
mkdir -p /tmp/claude-0/tools && [ -x /tmp/claude-0/tools/node_modules/.bin/gltf-transform ] || (cd /tmp/claude-0/tools && npm i --silent @gltf-transform/cli@4.1.1)
[ -s /tmp/claude-0/assets/bk/c3c28d91_u.glb ] || /tmp/claude-0/tools/node_modules/.bin/gltf-transform copy /tmp/claude-0/assets/bk/c3c28d91.glb /tmp/claude-0/assets/bk/c3c28d91_u.glb
ls -la $D/chars $D/anims | awk '{print $5, $9}'
