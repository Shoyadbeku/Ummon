#!/bin/bash
# "Chivin chaqishi" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan; do curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Sitting_Idle_5 Sitting_Idle_3 Sitting_Rubbing_Arm Sitting_Laughing Sitting_Angry Getting_Bit Sitting_Disbelief_2; do
  curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
python3 -I $(dirname "$0")/ph_get.py Sofa_01 modern_coffee_table_01 potted_plant_01 fancy_picture_frame_01 \
  laminate_floor_02 painted_plaster_wall kloofendal_48d_partly_cloudy_puresky
ls -la $D/chars $D/anims | awk '{print $5, $9}'
