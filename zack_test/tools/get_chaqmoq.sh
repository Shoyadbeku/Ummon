#!/bin/bash
# "Chaqmoq" videosi uchun manbalar: Mixamo (HF to'plami) + Poly Haven (CC0). Login kerak emas.
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
D=${1:-/tmp/claude-0/assets/mixamo}; mkdir -p $D/chars $D/anims
for c in Remy Brian Josh Bryce David Kate Megan Sophie Jody Louise Leonard; do
  [ -s $D/chars/$c.fbx ] || curl -sSL -o $D/chars/$c.fbx "$B/character_refined/$c.fbx"; done
for a in Being_Electrocuted Getting_Up_3 Flying_Back_Death Falling_Down Breathing_Idle Death Getting_Bit \
         Catwalk_Idle_01 Catwalk_Idle_02 Happy_Idle Bored Dizzy_Idle Gunplay_4 Agony; do
  [ -s $D/anims/$a.fbx ] || curl -sSL -o $D/anims/$a.fbx "$B/animation_motion/$a.fbx"; done
python3 -I "$(dirname "$0")/ph_get.py" jacaranda_tree grass_medium_02 leafy_grass sparse_grass bark_brown_02 \
  concrete_tile_facade asphalt_02 concrete_pavement kloofendal_48d_partly_cloudy_puresky modern_buildings_night
