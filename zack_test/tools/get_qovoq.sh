#!/bin/bash
# "Ko'z qovog'i uchishi" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan Kate; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Typing Crying Drinking Yawn Sitting_Talking Shrugging Whatever_Gesture Thinking Dismissing_Gesture_2 \
         Annoyed_Head_Shake Sitting_Idle_4 Female_Walk; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky laminate_floor_02 painted_plaster_wall \
  Sofa_01 modern_coffee_table_01 potted_plant_01 fancy_picture_frame_01 WoodenTable_01 modern_arm_chair_01 \
  desk_lamp_arm_01 Shelf_01 book_encyclopedia_set_01
ls -la $D/chars $D/anims | awk '{print $5, $9}'
