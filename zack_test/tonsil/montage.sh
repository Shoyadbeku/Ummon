#!/usr/bin/env bash
# Kadrlarni 24 fps vertikal MP4 ga yig'ish + ovoz + o'tish "whoosh" lari.
# Foydalanish: montage.sh FRAMES_DIR AUDIO.wav OUT.mp4
# FRAMES_DIR/sNN/####.jpg — har bir shot global kadr raqami bilan.
set -euo pipefail
FR=${1:?frames dir}; AUD=${2:?audio}; OUT=${3:?out.mp4}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# 1) barcha shotlarni bitta ketma-ketlikka (global raqam bo'yicha)
for d in "$FR"/s[0-9][0-9]; do
  for f in "$d"/*.jpg; do ln -sf "$(realpath "$f")" "$TMP/$(basename "$f")"; done
done
N=$(ls "$TMP"/*.jpg | wc -l)
echo "kadrlar: $N"

# 2) whoosh: oq shovqin, band-pass, tez kuchayib-so'nuvchi (o'tishlarda)
#    tomoqqa sho'ng'ish (278-kadr = 11.58 s) va qon tomiri (977 = 40.67 s)
ffmpeg -loglevel error -y -f lavfi -i "anoisesrc=d=0.9:c=pink:a=0.6" \
  -af "bandpass=f=900:width_type=o:w=2,afade=t=in:d=0.55:curve=exp,afade=t=out:st=0.55:d=0.35,volume=0.35" \
  -ar 48000 -ac 1 "$TMP/whoosh.wav"

# 3) video: 576x1024 -> 1080x1920 (lanczos + yengil keskinlik), vinyetka, (donadorliksiz — fayl hajmi kichik bo'lsin)
ffmpeg -loglevel error -y -framerate 24 -start_number 1 -i "$TMP/%04d.jpg" \
  -i "$AUD" -i "$TMP/whoosh.wav" -i "$TMP/whoosh.wav" \
  -filter_complex "\
[0:v]scale=1080:1920:flags=lanczos,unsharp=5:5:0.6,vignette=PI/5,format=yuv420p[v];\
[2:a]adelay=11000|11000[w1];[3:a]adelay=40100|40100[w2];\
[1:a][w1][w2]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.95[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 20 -profile:v high -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart -shortest "$OUT"
echo "tayyor: $OUT"
