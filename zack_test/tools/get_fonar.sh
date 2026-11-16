#!/bin/bash
# "Telefon fonari" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Bryce Brian; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Laying_Idle_2 Look_Around Nervously_Look_Around Rummaging Throw_Object Opening_3 Standing_Torch_Idle_02 \
  Standing_Torch_Inspect_Downward Crouch_Torch_Idle_02 Talking_On_A_Cell_Phone Talking_Phone_Pacing Standing_Yell_2 Yelling \
  Texting Texting_While_Standing Thinking Disappointed Sitting_Talking Talking_3; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_48d_partly_cloudy_puresky laminate_floor_02 painted_plaster_wall \
  Sofa_01 modern_coffee_table_01 potted_plant_01 fancy_picture_frame_01 ClassicNightstand_01 alarm_clock_01 \
  throw_pillows_01 Shelf_01 book_encyclopedia_set_01 desk_lamp_arm_01
# smartfon (BlenderKit, bepul) -> Draco'siz nusxa
BK=/tmp/claude-0/assets/bk; mkdir -p $BK
[ -s $BK/a6d503d4.glb ] || $H/bk_get.sh "smartphone" a6d503d4 $BK
if [ ! -s $BK/a6d503d4_u.glb ]; then
  [ -x /tmp/claude-0/tools/node_modules/.bin/gltf-transform ] || (mkdir -p /tmp/claude-0/tools && cd /tmp/claude-0/tools && npm i --silent @gltf-transform/cli@4.1.1)
  /tmp/claude-0/tools/node_modules/.bin/gltf-transform copy $BK/a6d503d4.glb $BK/a6d503d4_u.glb
fi
ls -la $D/chars $D/anims $BK | awk '{print $5, $9}'
