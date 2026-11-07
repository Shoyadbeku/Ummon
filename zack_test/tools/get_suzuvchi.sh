#!/bin/bash
# "Ko'zdagi suzuvchi nuqtalar" videosi uchun qo'shimcha assetlar (hammasi bepul, login kerak emas).
# Avval: get_mixamo.sh (Megan) va CLAUDE.md dagi Poly Haven/gltf-transform qadamlari.
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
[ -f $D/chars/Megan.fbx ] || curl -sSL -o $D/chars/Megan.fbx "$B/character_refined/Megan.fbx"
for a in Looking_3 Looking Crying Look_Around_2 Breathing_Idle Nervously_Look_Around Annoyed_Head_Shake; do
  [ -f $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky Sofa_01 modern_coffee_table_01 potted_plant_01 \
  fancy_picture_frame_01 laminate_floor_02 painted_plaster_wall concrete_pavement asphalt_02 long_white_tiles marble_tiles sparse_grass
$H/bk_get.sh "bathroom sink" a541b293 /tmp/claude-0/assets/bk
G=/tmp/claude-0/tools/node_modules/.bin/gltf-transform
[ -x $G ] || (mkdir -p /tmp/claude-0/tools && cd /tmp/claude-0/tools && npm i --silent @gltf-transform/cli@4.1.1)
$G copy /tmp/claude-0/assets/bk/a541b293.glb /tmp/claude-0/assets/bk/a541b293_u.glb
ls -la $D/anims | awk '{print $5, $9}'
