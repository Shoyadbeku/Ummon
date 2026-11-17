#!/bin/bash
# "O'g'ri va televizor" videosi uchun assetlar (hammasi bepul, login kerak emas).
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in David Brian; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Sneak_Walk Look_Around Lifting_Object Push_2 Jogging_With_Box Box_Idle Thinking Searching_Pockets Working_On_Device \
         Walking_With_Shopping_Bag Reacting Running_2 Kneeling_Down Sprint Idle Terrified; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
python3 -I "$(dirname "$0")/ph_get.py" Sofa_01 modern_coffee_table_01 potted_plant_01 laminate_floor_02 painted_plaster_wall \
  concrete_pavement asphalt_02 kloofendal_48d_partly_cloudy_puresky
# BlenderKit (bepul): TV 75", eski mikroto'lqinli pech (CC0), oshxona, otvyortka -> Draco'ni yechish
BK=/tmp/claude-0/assets/bk; T="$(dirname "$0")"
"$T/bk_get.sh" "television" 5baba85b $BK; "$T/bk_get.sh" "microwave" cab01678 $BK
"$T/bk_get.sh" "kitchen" 984fd8f8 $BK; "$T/bk_get.sh" "screwdriver" c0e7f651 $BK
mkdir -p /tmp/claude-0/tools && [ -x /tmp/claude-0/tools/node_modules/.bin/gltf-transform ] || (cd /tmp/claude-0/tools && npm i --silent @gltf-transform/cli@4.1.1)
for a in 5baba85b cab01678 984fd8f8 c0e7f651; do /tmp/claude-0/tools/node_modules/.bin/gltf-transform copy $BK/$a.glb $BK/${a}_u.glb; done
ls -la $D/chars $D/anims | awk '{print $5, $9}'
