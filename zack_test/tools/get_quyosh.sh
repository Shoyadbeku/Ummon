#!/bin/bash
# "Quyoshga tikilish" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
curl -sSL -o $D/chars/Megan.fbx "$B/character_refined/Megan.fbx" &
for a in Breathing_Idle Idle_9 Crying Female_Walk Happy_Idle; do
  curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky studio_small_09 asphalt_02 concrete_pavement \
  painted_plaster_wall laminate_floor_02 Sofa_01 potted_plant_01 fancy_picture_frame_01 modern_coffee_table_01
ls -la $D/chars $D/anims | awk '{print $5, $9}'
