#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920 ga kattalashtirib) + foydalanuvchi ovozi + tovush effektlari (sfx.py)
# Effektlar ovoz eshitilganda avtomatik pasayadi (sidechain); portlashda (14.3 s) qisqa oq chaqnash.
# montaj.sh <kadrlar_papkasi> <ovoz.wav> <chiqish.mp4> [sfx.wav] [kadrlar_soni]
FR=${1:-/tmp/claude-0/frames}; VO=${2:-/tmp/claude-0/audio/voice.wav}; OUT=${3:-zack_test/gage/phineas_gage.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx.wav}; NF=${5:-1325}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$(dirname "$0")/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v "$NF" \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.7+70)':enable='between(t,14.29,14.40)',format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=5:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 19 -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
