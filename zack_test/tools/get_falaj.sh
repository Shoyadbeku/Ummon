#!/bin/bash
# "Uyqu falaji" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan Parasite_L_Starkie; do curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Laying_Sleeping Laying_3 Laying_Idle_2 Laying_Breathless Laying_Moaning Crouching_Idle Breathing_Idle Mutant_Idle \
         Running_8 Fast_Run Terrified Zombie_Idle; do
  curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky studio_small_09 laminate_floor_02 painted_plaster_wall \
  WoodenTable_01 modern_arm_chair_01 classic_laptop desk_lamp_arm_01 alarm_clock_01 potted_plant_01 \
  painted_wooden_nightstand fancy_picture_frame_01 Shelf_01 book_encyclopedia_set_01 fabric_pattern_07 denim_fabric
ls -la $D/chars $D/anims | awk '{print $5, $9}'
