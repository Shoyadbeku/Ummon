#!/bin/bash
# Assemble rendered shots into the final 24 fps MP4 with the narration.
# - hard cuts every 2-4 s (Zack D. pacing), soft whoosh on every cut, low boom on the hook,
# - 540x960 renders upscaled to 1080x1920 (lanczos + light sharpen), fade to black at the end.
# usage: bash edit.sh /path/voice.wav [out.mp4]
set -e
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(cd "$HERE/../.." && pwd)
VOICE=${1:?voice wav}; OUT=${2:-$ROOT/renders/suv_zaharlanishi_zackd.mp4}
FR="$ROOT/renders/frames"; SEQ="$ROOT/renders/frames/_seq"; rm -rf "$SEQ"; mkdir -p "$SEQ"
SHOTS="53 58 74 98 91 94 118 89 88 94 91 72"
i=0; n=1; cuts=()
for len in $SHOTS; do
  [ $i -gt 0 ] && cuts+=("$i")
  for f in $(seq 1 "$len"); do
    i=$((i + 1))
    ln -s "$FR/shot$n/f_$(printf %04d "$f").png" "$SEQ/$(printf %05d $i).png"
  done
  n=$((n + 1))
done
TOTAL=$i; DUR=$(python3 -c "print($TOTAL/24)")
echo "frames: $TOTAL  duration: $DUR s  cuts: ${cuts[*]}"

# --- SFX: whoosh per cut (filtered noise, short swell) + low boom at 0 s
TMP=$(mktemp -d)
ffmpeg -loglevel error -y -f lavfi -i "anoisesrc=d=0.5:c=pink:a=0.6:r=48000" \
  -af "highpass=f=300,lowpass=f=3500,afade=t=in:d=0.32:curve=exp,afade=t=out:st=0.32:d=0.18,volume=0.5" "$TMP/whoosh.wav"
ffmpeg -loglevel error -y -f lavfi -i "sine=f=48:d=1.4:r=48000" \
  -af "afade=t=in:d=0.02,afade=t=out:st=0.1:d=1.3:curve=exp,volume=0.9" "$TMP/boom.wav"
inputs=(-i "$VOICE" -i "$TMP/boom.wav"); mix="[1:a]adelay=0|0[b];"; labels="[0:a][b]"; k=2
for c in "${cuts[@]}"; do
  ms=$(python3 -c "print(int($c/24*1000) - 300)")
  inputs+=(-i "$TMP/whoosh.wav"); mix+="[$k:a]adelay=${ms}|${ms}[w$k];"; labels+="[w$k]"; k=$((k + 1))
done
mix+="${labels}amix=inputs=$((k)):normalize=0:duration=first,alimiter=limit=0.95[a]"
ffmpeg -loglevel error -y "${inputs[@]}" -filter_complex "$mix" -map "[a]" -ac 2 -ar 48000 "$TMP/audio.wav"

ffmpeg -loglevel error -y -framerate 24 -i "$SEQ/%05d.png" -i "$TMP/audio.wav" \
  -vf "scale=1080:1920:flags=lanczos,unsharp=5:5:0.5:5:5:0,fade=t=in:st=0:d=0.15,fade=t=out:st=$(python3 -c "print($DUR-0.7)"):d=0.7" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -r 24 -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
rm -rf "$TMP"
echo "wrote $OUT"; ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
