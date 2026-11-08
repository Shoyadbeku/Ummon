#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + foydalanuvchi ovozi + tovush effektlari (sfx.py)
# Zack D. montaji: zarbalarda qisqa oq chaqnash (17.8 s "Bu chuvalchang edi", 19.5 s "qo'rqib ketdi"),
# yengil vinyetka va kino donadorligi, oxirida ko'z yumilgach keskin qorong'ilik.
# Effektlar ovoz eshitilganda avtomatik pasayadi (sidechain).
# montaj.sh <kadrlar_papkasi> <ovoz.wav> <chiqish.mp4> [sfx.wav]
# Donadorlik bitreytni oshiradi: crf 27 + maxrate bilan fayl ~10 MB (GitHub 100 MB chegarasidan ancha past).
FR=${1:-/tmp/claude-0/frames}; VO=${2:-/tmp/claude-0/audio/voice.wav}; OUT=${3:-zack_test/ebbi/ebbi_chuvalchang.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_ebbi.wav}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$(dirname "$0")/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 1320 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.8+80)':enable='between(t,17.79,17.88)+between(t,19.50,19.58)+between(t,24.50,24.56)',
      vignette=PI/5,noise=alls=5:allf=t,
      fade=t=out:st=54.55:d=0.25,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 27 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
