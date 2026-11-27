#!/bin/bash
# "Batut qanday ixtiro qilingan" videosi uchun assetlar (hammasi bepul, login kerak emas).
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Remy Brian Aj; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Joyful_Jump Jump Jumping_Jacks Falling_2 Floating Falling_Idle Treading_Water Happy_Idle Excited Cheering \
         Disappointed Angry Sad_Idle Injured_Hurting_Idle Falling_Down Hard_Landing Waving Waving_2 Idle Thinking \
         Defeated Kneeling_Inspecting Plant_A_Plant Sitting_Idle_5 Sit_To_Stand Male_Crouch_Pose_4 Walking Pointing_Forward \
         Swimming_To_Edge Big_Jump Landing; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
python3 -I "$(dirname "$0")/ph_get.py" kloofendal_48d_partly_cloudy_puresky brick_wall_02 leafy_grass blue_floor_tiles_01 \
  patio_tiles brown_planks_05 concrete_pavement shrub_01 shrub_02 outdoor_table_chair_set_01 garden_gnome \
  plastic_monobloc_chair_01 painted_plaster_wall clay_roof_tiles
ls -la $D/chars $D/anims | awk '{print $5, $9}'
