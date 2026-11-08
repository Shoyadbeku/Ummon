#!/bin/bash
# "Quloqqa tarakan" videosi uchun assetlar (hammasi bepul, login kerak emas).
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Brian Kate; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Laying_Sleeping Laying_Idle Laying_Moaning Sitting_Disbelief_3 Sitting_Idle_4 Sitting_Yell_3 Relieved_Sigh Idle_14 Breathing_Idle Agony; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
python3 -I "$(dirname "$0")/ph_get.py" potted_plant_01 fancy_picture_frame_01 kloofendal_48d_partly_cloudy_puresky \
  laminate_floor_02 painted_plaster_wall
BK=/tmp/claude-0/assets/bk
for p in "cockroach:e34efe7c" "spider:72f27245" "oil bottle:9bb74de4" "bed:9d002926"; do
  [ -s $BK/${p#*:}.glb ] || "$(dirname "$0")/bk_get.sh" "${p%:*}" ${p#*:} $BK; done
mkdir -p /tmp/claude-0/tools && (cd /tmp/claude-0/tools && [ -x node_modules/.bin/gltf-transform ] || npm i --silent @gltf-transform/cli@4.1.1)
for id in e34efe7c 72f27245 9bb74de4 9d002926; do
  [ -s $BK/${id}_u.glb ] || /tmp/claude-0/tools/node_modules/.bin/gltf-transform copy $BK/$id.glb $BK/${id}_u.glb; done
ls -la $D/chars $D/anims | awk '{print $5, $9}'
