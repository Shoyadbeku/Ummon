#!/bin/bash
# "Pichoqni sug'urma" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan Leonard; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Injured_Idle Injured_Stumble_Idle Dying_6 Dying_8 Falling_Forward_Death Big_Side_Hit Breathing_Idle; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky Sofa_01 modern_coffee_table_01 potted_plant_01 \
  laminate_floor_02 painted_plaster_wall asphalt_02 concrete_pavement
ls -la $D/chars $D/anims | awk '{print $5, $9}'
