#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + foydalanuvchi ovozi + tovush effektlari (sfx.py)
# Zack D. montaji: zarbalarda qisqa oq chaqnash ("falaj" 25.17 s, o'pka 32.46 s, oxirgi bo'lak 41.4 s),
# yengil vinyetka va kino donadorligi, oxirida keskin qorong'ilik. Effektlar ovoz eshitilganda pasayadi (sidechain).
# montaj.sh <kadrlar_papkasi> <ovoz.wav> <chiqish.mp4> [sfx.wav]
FR=${1:-/tmp/claude-0/frames}; VO=${2:-/tmp/claude-0/work/ovoz.wav}; OUT=${3:-zack_test/kiprik/nafas_kiprikchalar.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_kiprik.wav}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$(dirname "$0")/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 999 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.8+80)':enable='between(t,25.17,25.25)+between(t,32.46,32.54)+between(t,41.4,41.5)',
      vignette=PI/5,noise=alls=5:allf=t,
      fade=t=out:st=41.35:d=0.25,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad=whole_dur=41.625,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 27 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
