#!/bin/bash
# "Tatuirovka nega o'chmaydi" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan Leonard; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Sitting_Idle_4 Seated_Idle Typing Sitting_Rubbing_Arm Sitting_Thumbs_Up; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky laminate_floor_02 painted_plaster_wall brick_wall_001 \
  modern_arm_chair_01 metal_stool_02 WoodenTable_01 hanging_industrial_lamp potted_plant_01 fancy_picture_frame_01 \
  wooden_bookshelf_worn spray_paint_bottles drawer_cabinet Sofa_01
ls -la $D/chars $D/anims | awk '{print $5, $9}'
