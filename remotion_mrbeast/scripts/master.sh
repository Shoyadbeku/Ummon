#!/usr/bin/env bash
# Remotion render → audio mastering (2-pass loudnorm, -14 LUFS / -1.5 dBTP) → Final_Video.mp4
set -euo pipefail
cd "$(dirname "$0")/.."
IN=out/render_raw.mp4
OUT=out/Final_Video.mp4

# 1-o‘tish: o‘lchash
STATS=$(ffmpeg -hide_banner -i "$IN" -vn -af "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json" -f null - 2>&1 | sed -n '/^{/,/^}/p')
get() { echo "$STATS" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
MI=$(get input_i); MTP=$(get input_tp); MLRA=$(get input_lra); MTH=$(get input_thresh); OFF=$(get target_offset)
echo "Kirish: I=$MI LUFS, TP=$MTP dBTP, LRA=$MLRA"

# 2-o‘tish: chiziqli normalizatsiya + yakuniy limiter
ffmpeg -y -hide_banner -v error -i "$IN" \
	-af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$MI:measured_TP=$MTP:measured_LRA=$MLRA:measured_thresh=$MTH:offset=$OFF:linear=true,aresample=48000" \
	-vf "scale=in_range=full:out_range=tv,format=yuv420p" -c:v libx264 -preset slow -crf 17 -maxrate 18M -bufsize 36M \
	-profile:v high -level 4.2 -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
	-c:a aac -b:a 320k -ar 48000 -movflags +faststart "$OUT"

ffmpeg -hide_banner -i "$OUT" -vn -af ebur128=peak=true -f null - 2>&1 | grep -A12 Summary | grep -E "I:|Peak:"
echo "Tayyor: $OUT"
