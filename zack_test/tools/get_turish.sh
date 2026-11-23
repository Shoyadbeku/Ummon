#!/bin/bash
# "Keskin o'rindan turish" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Laying_Idle Sit_To_Stand Dizzy_Idle Injured_Stumble_Idle Dying_10; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky laminate_floor_02 painted_plaster_wall \
  WoodenTable_01 modern_arm_chair_01 desk_lamp_arm_01 alarm_clock_01 potted_plant_01 fancy_picture_frame_01 \
  Shelf_01 book_encyclopedia_set_01
ls -la $D/chars $D/anims | awk '{print $5, $9}'
