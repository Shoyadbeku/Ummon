#!/bin/bash
# "Tish sug'urilgach jag' suyagi" videosi uchun assetlar (hammasi bepul, login kerak emas)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan Sporty_Granny; do curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Idle_9 Sad_Idle Thinking Terrified Look_Around_2 Disappointed Breathing_Idle Defeat_Idle_3 Reacting; do
  curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
python3 -I $(dirname "$0")/ph_get.py Sofa_01 potted_plant_01 fancy_picture_frame_01 laminate_floor_02 painted_plaster_wall \
  studio_small_09 kloofendal_48d_partly_cloudy_puresky
ls -la $D/chars $D/anims | awk '{print $5, $9}'
