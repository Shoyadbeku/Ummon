#!/bin/bash
# "Qo'tir nega qichishadi" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Fall_Flat Sitting_Rubbing_Arm; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky studio_small_09 laminate_floor_02 painted_plaster_wall \
  concrete_pavement asphalt_02 Sofa_01 modern_coffee_table_01 potted_plant_01
ls -la $D/chars $D/anims | awk '{print $5, $9}'
