#!/bin/bash
# "O'lim uchburchagi" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Breathing_Idle Agony Death; do [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
python3 -I "$(dirname "$0")/ph_get.py" studio_small_09 painted_plaster_wall laminate_floor_02 potted_plant_01
ls -la $D/chars $D/anims | awk '{print $5, $9}'
