#!/bin/bash
# "Tirnoq ostidagi qon" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan Olivia; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Breathing_Idle Shaking_It_Off Injured_Idle Seated_Idle Relieved_Sigh Standing_Idle_2 Looking_Down; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky hospital_room studio_small_09 laminate_floor_02 painted_plaster_wall \
  wood_table_001 long_white_tiles cross_pein_hammer pliers bunsen_burner medical_box metal_office_desk SchoolChair_01 \
  potted_plant_01 fancy_picture_frame_01 clipboard
ls -la $D/chars $D/anims | awk '{print $5, $9}'
