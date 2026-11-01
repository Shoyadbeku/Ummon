#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920 ga kattalashtirib) + foydalanuvchi ovozi + portlash (14.3 s) uchun past "gumbur"
# montaj.sh <kadrlar_papkasi> <ovoz.wav> <chiqish.mp4>
FR=${1:-/tmp/claude-0/frames}; VO=${2:-/tmp/claude-0/audio/voice.wav}; OUT=${3:-zack_test/gage/phineas_gage.mp4}
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" \
  -f lavfi -t 2.5 -i "anoisesrc=color=brown:amplitude=0.9:seed=3" \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,format=yuv420p[v];
    [2:a]lowpass=f=140,afade=t=in:d=0.02,afade=t=out:st=0.15:d=2.3,volume=2.2,adelay=14300|14300,aformat=channel_layouts=mono[b];
    [1:a]aformat=channel_layouts=mono[vo];[vo][b]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 19 -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
