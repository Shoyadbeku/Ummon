#!/bin/bash
# "Oyoq uvishishi" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Sitting_7 Sitting_Idle_5 Sitting_4 Sit_To_Stand Stand_Up Injured_Hurting_Idle Injured_Stumble_Idle Injured_Walk Shaking_It_Off \
         Relieved_Sigh Texting Sitting_Disbelief_3 Female_Walk; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky laminate_floor_02 painted_plaster_wall \
  Sofa_01 modern_coffee_table_01 potted_plant_01 fancy_picture_frame_01 asphalt_02 concrete_pavement \
  Shelf_01 book_encyclopedia_set_01 aerial_grass_rock
ls -la $D/chars $D/anims | awk '{print $5, $9}'
