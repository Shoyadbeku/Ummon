#!/bin/bash
# "Hojatxonada telefon — gemorroy" videosi uchun assetlar (hammasi bepul, login kerak emas).
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
[ -s $D/chars/Brian.fbx ] || curl -sSL -o $D/chars/Brian.fbx "$B/character_refined/Brian.fbx" &
for a in Sitting Texting_And_Walking Laying_Idle; do [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
python3 -I "$(dirname "$0")/ph_get.py" interior_tiles potted_plant_01 concrete_pavement asphalt_02 painted_plaster_wall kloofendal_48d_partly_cloudy_puresky
# unitaz (BlenderKit, bepul, royalty free) -> Draco'ni yechish
BK=/tmp/claude-0/assets/bk; "$(dirname "$0")/bk_get.sh" "toilet ceramic white" 6a342733 $BK
mkdir -p /tmp/claude-0/tools && [ -x /tmp/claude-0/tools/node_modules/.bin/gltf-transform ] || (cd /tmp/claude-0/tools && npm i --silent @gltf-transform/cli@4.1.1)
/tmp/claude-0/tools/node_modules/.bin/gltf-transform copy $BK/6a342733.glb $BK/6a342733_u.glb
ls -la $D/chars $D/anims | awk '{print $5, $9}'
