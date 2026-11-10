#!/bin/bash
# "Ko'zni ishqalash" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Typing Crying Yawn Sitting_Disbelief Sitting_Idle_4 Laying_Idle Rubbing_Eyes Rifle_Rubbing_Eyes; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky laminate_floor_02 painted_plaster_wall \
  Sofa_01 modern_coffee_table_01 potted_plant_01 fancy_picture_frame_01 WoodenTable_01 modern_arm_chair_01 \
  desk_lamp_arm_01 Shelf_01 book_encyclopedia_set_01
# ayol bosh suyagi (BlenderKit, bepul) -> Draco'siz nusxa
BK=/tmp/claude-0/assets/bk; mkdir -p $BK
[ -s $BK/49c13194.glb ] || $H/bk_get.sh "female skull" 49c13194 $BK
if [ ! -s $BK/49c13194_u.glb ]; then
  [ -x /tmp/claude-0/tools/node_modules/.bin/gltf-transform ] || (mkdir -p /tmp/claude-0/tools && cd /tmp/claude-0/tools && npm i --silent @gltf-transform/cli@4.1.1)
  /tmp/claude-0/tools/node_modules/.bin/gltf-transform copy $BK/49c13194.glb $BK/49c13194_u.glb
fi
ls -la $D/chars $D/anims $BK | awk '{print $5, $9}'
