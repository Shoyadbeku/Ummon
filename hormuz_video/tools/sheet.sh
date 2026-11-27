#!/bin/bash
# usage: sheet.sh video out.jpg [interval_seconds]
f="$1"; out="$2"; iv="${3:-0}"
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
[ "$iv" = "0" ] && iv=$(python3 -c "print(max(2,round($d/40,1)))")
ffmpeg -loglevel error -y -i "$f" -vf "fps=1/$iv,scale=256:144:force_original_aspect_ratio=decrease,pad=256:144:(ow-iw)/2:(oh-ih)/2,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='%{eif\:n*$iv\:d}s':x=4:y=4:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=6x7" -frames:v 1 "$out"
