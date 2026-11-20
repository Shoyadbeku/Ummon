#!/bin/bash
# Phineas Gage videosi uchun qahramon va harakatlar (HF: Linzhan/Mixamo-Animations-Characters)
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Pete Peasant_Man Josh; do curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx" & done
for a in Digging Big_Hit_To_Head Falling_Down Fallen_Idle Getting_Up Injured_Walk Idle_14 Breathing_Idle \
         Angry_Gesture Angry_Point Insult Annoyed_Head_Shake Terrified Walk_Backwards Jump_Away Look_Around Agreeing; do
  curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx" & done
wait; ls -la $D/chars $D/anims | awk '{print $5, $9}'
