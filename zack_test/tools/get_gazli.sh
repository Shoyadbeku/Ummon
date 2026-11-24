#!/bin/bash
# "Gazli ichimlik" videosi uchun qahramon va harakatlar (HF: Linzhan/Mixamo-Animations-Characters) + Poly Haven
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan; do curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Drinking Drunk_Idle_Variation Big_Stomach_Hit Dizzy_Idle Sad_Idle Annoyed_Head_Shake \
         Sitting_Dazed Sitting_Angry Picking_Up Reaching_Out Breathing_Idle Bored Look_Around_3; do
  curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait; ls -la $D/chars $D/anims | awk '{print $5, $9}'
python3 -I "$(dirname "$0")/ph_get.py" Sofa_01 modern_coffee_table_01 potted_plant_01 fancy_picture_frame_01 \
  kloofendal_48d_partly_cloudy_puresky laminate_floor_02 painted_plaster_wall
