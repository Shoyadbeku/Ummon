#!/bin/bash
# "G'oz terisi" videosi uchun manbalar: Mixamo (HF), Poly Haven (CC0). Login kerak emas.
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan Brute; do curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx"; done
for a in Shoulder_Rubbing Terrified Look_Around_2 Breathing_Idle Reacting Roar; do
  curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx"; done
H=$(dirname "$0")
PH_RES=2k python3 -I $H/ph_get.py snowy_forest winter_evening
python3 -I $H/ph_get.py snow_02 rock_face asphalt_snow concrete_pavement
