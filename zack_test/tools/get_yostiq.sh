#!/bin/bash
# "Yostiq jildi va bakteriyalar" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
[ -s $D/chars/Megan.fbx ] || curl -sSL -o $D/chars/Megan.fbx "$B/character_refined/Megan.fbx" &
for a in Laying_Sleeping Laying_Idle Crying Sleeping_Idle Idle; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky laminate_floor_02 painted_plaster_wall long_white_tiles floor_tiles_06 \
  potted_plant_01 GothicBed_01 ClassicNightstand_01 alarm_clock_01 Shelf_01 book_encyclopedia_set_01 interior_tiles
# unitaz (BlenderKit, bepul) -> Draco'ni yechish
BK=/tmp/claude-0/assets/bk; "$H/bk_get.sh" "toilet ceramic white" 6a342733 $BK
mkdir -p /tmp/claude-0/tools && [ -x /tmp/claude-0/tools/node_modules/.bin/gltf-transform ] || (cd /tmp/claude-0/tools && npm i --silent @gltf-transform/cli@4.1.1)
/tmp/claude-0/tools/node_modules/.bin/gltf-transform copy $BK/6a342733.glb $BK/6a342733_u.glb
ls -la $D/chars $D/anims | awk '{print $5, $9}'
