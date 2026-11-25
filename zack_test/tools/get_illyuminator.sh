#!/bin/bash
# "Illyuminatorni sindirsangiz" videosi uchun assetlar (hammasi bepul, login kerak emas).
# Salon, A320 va illyuminator ramkasi samolyot/ loyihasidan: get_samolyot.sh ni ham ishga tushir.
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Megan Kate Josh David Pete; do [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Sitting_Idle_5 Sitting_Idle_3 Sitting_Swinging_Weapon Knock_Off_Assailant Jostled_Passenger Sitting_Disbelief_3 \
         Knocked_Unconscious Sitting_Rubbing_Arm Falling_Into_Pool_2 Edge_Slip Piloting Relieved_Sigh Sitting_Dazed Sitting_Disbelief; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait
ls -la $D/chars $D/anims | awk '{print $5, $9}'
