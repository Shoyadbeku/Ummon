#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + foydalanuvchi ovozi + tovush effektlari (sfx.py)
# Zack D. montaji: chaqmoqda oq chaqnash (1.83 s), mushaklar qisqarishida (14.6 s) va jun hurpayishida (31.3 s) qisqa chaqnash,
# yengil vinyetka va kino donadorligi, oxirida qorong'ilik. Effektlar ovoz eshitilganda pasayadi (sidechain).
# montaj.sh <kadrlar_papkasi> <ovoz.mp3> <chiqish.mp4> [sfx.wav]
FR=${1:-/tmp/claude-0/frames}; VO=${2:-zack_test/goz/ovoz.mp3}; OUT=${3:-zack_test/goz/goz_terisi.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_goz.wav}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$(dirname "$0")/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 1002 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.9+90)':enable='between(t,1.83,1.88)+between(t,2.0,2.04)',
      lutyuv=y='min(255,val*1.4+40)':enable='between(t,14.58,14.63)+between(t,31.33,31.38)',
      vignette=PI/5,noise=alls=5:allf=t,
      fade=t=in:st=0:d=0.12,fade=t=out:st=41.1:d=0.6,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:41.75[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 23 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 41.75 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
