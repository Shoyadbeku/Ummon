#!/bin/bash
# "Ko'cha shimida karavotga yotish" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Brian Kate Joe Pete Jody; do
  [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Sad_Walk Lying_Down Laying_3 Stand_To_Sit Jostled_Passenger Sitting_Idle_3 Sitting_Idle_4 Sitting_Idle_5 \
         Laying_Sleeping Sleeping_Idle_2 Entering_Car Sitting_Talking Texting_While_Standing; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky laminate_floor_02 painted_plaster_wall asphalt_02 concrete_pavement \
  interior_tiles floor_tiles_06 GothicBed_01 ClassicNightstand_01 potted_plant_01 Sofa_01 modern_coffee_table_01 \
  GreenChair_01 round_wooden_table_01 WetFloorSign_01 Shelf_01
# taksi: Audi e-tron GT (BlenderKit, bepul) -> Draco'ni yechish
BK=/tmp/claude-0/assets/bk; [ -s $BK/c3c28d91.glb ] || "$H/bk_get.sh" "car" c3c28d91 $BK
mkdir -p /tmp/claude-0/tools && [ -x /tmp/claude-0/tools/node_modules/.bin/gltf-transform ] || (cd /tmp/claude-0/tools && npm i --silent @gltf-transform/cli@4.1.1)
[ -s $BK/c3c28d91_u.glb ] || /tmp/claude-0/tools/node_modules/.bin/gltf-transform copy $BK/c3c28d91.glb $BK/c3c28d91_u.glb
ls -la $D/chars $D/anims | awk '{print $5, $9}'
