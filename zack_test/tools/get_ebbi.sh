#!/bin/bash
# "Ebbi va sigir chuvalchangi" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan Olivia; do curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Crying Fishing_Cast Terrified Annoyed_Head_Shake Shrugging Sitting_Idle_5 Sitting_Disbelief_2 Pick_Fruit \
         Breathing_Idle Happy_Idle Looking_Down Look_Around_2 Relieved_Sigh Reacting Scared Sitting_Talking \
         Female_Standing_Pose_5 Looking Nervously_Look_Around Rejected Disappointed; do
  curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py kloofendal_overcast_puresky kloofendal_48d_partly_cloudy_puresky \
  wood_floor_deck weathered_planks white_planks_clean long_white_tiles marble_tiles painted_plaster_wall \
  grass_path_2 sparse_grass snow_02 rusty_metal_02 blue_metal_plate laminate_floor_02
$H/bk_get.sh "cow" b349a5ee /tmp/claude-0/assets/bk          # sigir (oq, teksturasiz)
$H/bk_get.sh "cow" 3bf2e12b /tmp/claude-0/assets/bk          # sigirlar (orqa fon)
$H/bk_get.sh "bathroom sink" a541b293 /tmp/claude-0/assets/bk
for f in /tmp/claude-0/assets/bk/{b349a5ee,3bf2e12b,a541b293}.glb; do
  /tmp/claude-0/tools/node_modules/.bin/gltf-transform copy $f ${f%.glb}_u.glb; done
ls -la $D/chars $D/anims | awk '{print $5, $9}'
