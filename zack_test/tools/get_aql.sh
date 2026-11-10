#!/bin/bash
# "Aql tishlari" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan; do curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Sitting_Idle_4 Sitting_Idle_5 Sitting_Laughing Sitting_Talking Sitting_Yell Sitting_Yell_2 Sitting_Disbelief_3 Agony Focus; do
  curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
H=$(dirname "$0")
python3 -I $H/ph_get.py studio_small_09 kloofendal_48d_partly_cloudy_puresky laminate_floor_02 painted_plaster_wall \
  wood_table_001 modern_coffee_table_01 potted_plant_01
K=/tmp/claude-0/assets/bk
$H/bk_get.sh "Female skull" 49c13194 $K       # bosh suyagi (jag' + tishlar)
$H/bk_get.sh "Male skull" d8f85f94 $K
$H/bk_get.sh "Tooth Cross Section" 86d1e900 $K  # tish kesimi
$H/bk_get.sh "Toothbrush" 492e383d $K
$H/bk_get.sh "Small Bulldozer" 1378b964 $K
$H/bk_get.sh "Bitten burger" f0052100 $K
$H/bk_get.sh "Dining Table" 8c7111e8 $K
[ -x /tmp/claude-0/tools/node_modules/.bin/gltf-transform ] || (mkdir -p /tmp/claude-0/tools && cd /tmp/claude-0/tools && npm i --silent @gltf-transform/cli@4.1.1)
for f in $K/{49c13194,d8f85f94,86d1e900,492e383d,1378b964,f0052100,8c7111e8}.glb; do
  [ -f ${f%.glb}_u.glb ] || /tmp/claude-0/tools/node_modules/.bin/gltf-transform copy $f ${f%.glb}_u.glb; done
ls -la $D/chars $D/anims | awk '{print $5, $9}'
