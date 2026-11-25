#!/bin/bash
# "Qorong'ida o'qish" videosi uchun qahramon va harakatlar (HF: Linzhan/Mixamo-Animations-Characters) + Poly Haven
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan; do curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Writing Typing Sitting_Idle_4 Sitting_Idle_5 Sitting_Idle_3 Texting Crying Yawn Neck_Stretching \
         Sleeping_Idle Sitting_Dazed Sitting_Disbelief Shaking_Head_No; do
  curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait; ls -la $D/chars $D/anims | awk '{print $5, $9}'
python3 -I "$(dirname "$0")/ph_get.py" WoodenTable_02 WoodenChair_01 desk_lamp_arm_01 book_encyclopedia_set_01 \
  wooden_bookshelf_worn wall_clock Sofa_01 potted_plant_01 fancy_picture_frame_01 \
  kloofendal_48d_partly_cloudy_puresky laminate_floor_02 painted_plaster_wall
