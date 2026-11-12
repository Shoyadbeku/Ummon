#!/bin/bash
# "Bo'yinni qirsillatish -> insult" videosi uchun assetlar (hammasi bepul, login kerak emas).
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Typing Sitting_Idle_4 Neck_Stretching Relieved_Sigh Texting_And_Walking Texting_While_Standing Dizzy_Idle \
         Falling_Forward_Death Dying_9 Dying_2 Dying_7 Crouch_Death Focus Female_Walk; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
python3 -I "$(dirname "$0")/ph_get.py" Sofa_01 modern_coffee_table_01 potted_plant_01 fancy_picture_frame_01 \
  kloofendal_48d_partly_cloudy_puresky laminate_floor_02 painted_plaster_wall asphalt_02 concrete_pavement
"$(dirname "$0")/bk_get.sh" "car" c3c28d91 /tmp/claude-0/assets/bk
mkdir -p /tmp/claude-0/tools && (cd /tmp/claude-0/tools && [ -x node_modules/.bin/gltf-transform ] || npm i --silent @gltf-transform/cli@4.1.1)
[ -s /tmp/claude-0/assets/bk/c3c28d91_u.glb ] || /tmp/claude-0/tools/node_modules/.bin/gltf-transform copy /tmp/claude-0/assets/bk/c3c28d91.glb /tmp/claude-0/assets/bk/c3c28d91_u.glb
ls -la $D/chars $D/anims | awk '{print $5, $9}'
