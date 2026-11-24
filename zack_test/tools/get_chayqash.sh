#!/bin/bash
# "Og'iz chayqash suyuqligi" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Kate Megan; do curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Drinking Dizzy_Idle Standing_React_Large_Gut Reaching_Out Laying_Breathless Idle_9; do
  curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
python3 -I $(dirname "$0")/ph_get.py modern_bathroom long_white_tiles marble_01 large_grey_tiles rubber_duck_toy
