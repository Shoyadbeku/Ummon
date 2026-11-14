#!/bin/bash
# "Oq ko'ylakdagi qora nuqta" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan Jody Bryce Sophie Leonard Josh Suzie Shannon Martha; do
  [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Seated_Idle Sitting_And_Pointing Writing Sitting_5 Sitting_Disbelief_2 Talking_7 Talking_2 Hands_Forward_Gesture \
         Happy_Idle Looking_Around Sad_Idle Happy_Hand_Gesture Dismissing_Gesture_2 Look_Away_Gesture; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py SchoolDesk_01 SchoolChair_01 food_apple_01 kloofendal_48d_partly_cloudy_puresky \
  painted_plaster_wall laminate_floor_02
ls -la $D/chars $D/anims | awk '{print $5, $9}'
