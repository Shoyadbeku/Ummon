#!/usr/bin/env bash
# Mixamo qahramon va harakatlarini HF to'plamidan yuklash (login kerak emas).
# Foydalanish: get_mixamo.sh OUT_DIR Megan Kate -- Stomach_Hit Taking_Item ...
set -euo pipefail
OUT=${1:?out dir}; shift
B=https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main
mkdir -p "$OUT/char" "$OUT/anim"
mode=char
for x in "$@"; do
  if [ "$x" = "--" ]; then mode=anim; continue; fi
  if [ $mode = char ]; then src="character_refined/$x.fbx"; dst="$OUT/char/$x.fbx"
  else src="animation_motion/$x.fbx"; dst="$OUT/anim/$x.fbx"; fi
  [ -s "$dst" ] || curl -sSfL --retry 4 -o "$dst" "$B/$src"
  echo "ok $dst"
done
