#!/bin/bash
# Mixamo qahramon va harakatlarini Hugging Face to'plamidan yuklash (login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan Kate; do curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx"; done
for a in Angry_Point Angry_Gesture_3 Annoyed_Head_Shake Dismissing_Gesture_2 Catwalk_Walk_Start_Turn_180_Right_2 Female_Walk Entering_Car; do
  curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx"; done
