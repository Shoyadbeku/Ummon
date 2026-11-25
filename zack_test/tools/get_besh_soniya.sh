#!/bin/bash
# "5 soniya qoidasi" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Unarmed_Grab_Torch_From_Floor Drinking Idle_9; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky laminate_floor_02 painted_plaster_wall \
  dining_table dining_chair_02 drawer_cabinet modern_wooden_cabinet wooden_cutting_board carved_wooden_plate \
  food_apple_01 food_kiwi_01 potted_plant_01 fancy_picture_frame_01
# makro kadrlar uchun pol teksturasi 4k da
PH_DIR=/tmp/claude-0/assets/ph4k/ PH_RES=4k python3 -I $H/ph_get.py laminate_floor_02
ls -la $D/chars $D/anims | awk '{print $5, $9}'
