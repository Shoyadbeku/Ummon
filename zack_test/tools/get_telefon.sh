#!/bin/bash
# "Telefon portlashi" videosi uchun assetlar (hammasi bepul, login kerak emas). Telefon, batareya, olov — protsedural (telefon.py).
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
[ -s $D/chars/Megan.fbx ] || curl -sSL -o $D/chars/Megan.fbx "$B/character_refined/Megan.fbx"
for a in Gaming Scared; do [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
python3 -I "$(dirname "$0")/ph_get.py" Sofa_01 modern_coffee_table_01 potted_plant_01 laminate_floor_02 painted_plaster_wall \
  kloofendal_48d_partly_cloudy_puresky
ls -la $D/chars $D/anims | awk '{print $5, $9}'
