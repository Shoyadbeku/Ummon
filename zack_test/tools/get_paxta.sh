#!/bin/bash
# "Paxtali cho'p / oltingugurt tiqini" videosi uchun assetlar (hammasi bepul, login kerak emas).
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
[ -s $D/chars/Brian.fbx ] || curl -sSL -o $D/chars/Brian.fbx "$B/character_refined/Brian.fbx" &
for a in Breathing_Idle Head_Gesture; do [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
python3 -I "$(dirname "$0")/ph_get.py" interior_tiles potted_plant_01
ls -la $D/chars $D/anims | awk '{print $5, $9}'
