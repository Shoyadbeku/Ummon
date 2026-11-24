#!/bin/bash
# "Nafas yo'lidagi kiprikchalar" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Adam; do curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Breathing_Idle Walking Smoking Laying_Sleeping Laying_Severe_Cough; do
  curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky studio_small_09 asphalt_02 concrete_pavement \
  painted_plaster_wall laminate_floor_02 GothicBed_01 alarm_clock_01 ClassicNightstand_01 potted_plant_01 fancy_picture_frame_01
$H/bk_get.sh "car" c3c28d91 /tmp/claude-0/assets/bk
mkdir -p /tmp/claude-0/tools && [ -x /tmp/claude-0/tools/node_modules/.bin/gltf-transform ] || (cd /tmp/claude-0/tools && npm i --silent @gltf-transform/cli@4.1.1)
/tmp/claude-0/tools/node_modules/.bin/gltf-transform copy /tmp/claude-0/assets/bk/c3c28d91.glb /tmp/claude-0/assets/bk/c3c28d91_u.glb
ls -la $D/chars $D/anims | awk '{print $5, $9}'
