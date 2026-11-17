#!/bin/bash
# "Ikkita magnitni yutsang" videosi uchun assetlar (hammasi bepul, login kerak emas).
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan Kate Josh; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Breathing_Idle Sitting_Drinking Sitting_Idle_3 Sitting_Idle_5 Sitting_Laughing Sitting_Disbelief_2 Big_Stomach_Hit Agony \
         Laying_Moaning Laying_3 Laying_Idle Pushing Walking Female_Walk Bartending Looking_Down Sitting_Idle Kneeling_Inspecting; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
python3 -I "$(dirname "$0")/ph_get.py" Sofa_01 modern_coffee_table_01 potted_plant_01 fancy_picture_frame_01 \
  kloofendal_48d_partly_cloudy_puresky laminate_floor_02 painted_plaster_wall concrete_pavement
ls -la $D/chars $D/anims | awk '{print $5, $9}'
