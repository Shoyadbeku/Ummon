#!/bin/bash
# "Ko'zdagi qizil dog'" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan Adam; do curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Breathing_Idle Back_Squat_3 Lifting_Object Terrified Reacting Relieved_Sigh Female_Walk Looking_Down Crying; do
  curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_overcast_puresky kloofendal_48d_partly_cloudy_puresky studio_small_09 \
  long_white_tiles marble_tiles painted_plaster_wall laminate_floor_02 concrete_floor_02
$H/bk_get.sh "bathroom sink" a541b293 /tmp/claude-0/assets/bk
mkdir -p /tmp/claude-0/tools && [ -x /tmp/claude-0/tools/node_modules/.bin/gltf-transform ] || (cd /tmp/claude-0/tools && npm i --silent @gltf-transform/cli@4.1.1)
/tmp/claude-0/tools/node_modules/.bin/gltf-transform copy /tmp/claude-0/assets/bk/a541b293.glb /tmp/claude-0/assets/bk/a541b293_u.glb
ls -la $D/chars $D/anims | awk '{print $5, $9}'
