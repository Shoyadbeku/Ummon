#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + foydalanuvchi ovozi + tovush effektlari (sfx.py)
# Zack D. montaji: yulishlarda (2.54, 20.17, 28.8, 29.8, 30.8 s) oq chaqnash, "yolg'on" (5.6 s), kapillyar uzilishi (22.95 s)
# va yiring (43.3 s) da qizil chaqnash, yengil vinyetka va kino donadorligi, oxirida qorong'ilik.
# Effektlar ovoz eshitilganda pasayadi (sidechain).
# montaj.sh <kadrlar_papkasi> <ovoz.mp3> <chiqish.mp4> [sfx.wav]
FR=${1:-/tmp/claude-0/frames}; VO=${2:-zack_test/oqsoch/ovoz.mp3}; OUT=${3:-zack_test/oqsoch/oq_soch.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_oqsoch.wav}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$(dirname "$0")/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 1063 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.7+70)':enable='between(t,2.54,2.59)+between(t,20.17,20.22)+between(t,28.80,28.84)+between(t,29.80,29.84)+between(t,30.80,30.84)',
      lutrgb=r='min(255,val*1.3+60)':g='val*0.6':b='val*0.6':enable='between(t,5.58,5.70)+between(t,22.95,23.05)+between(t,43.30,43.40)',
      vignette=PI/5,noise=alls=5:allf=t,
      fade=t=in:st=0:d=0.1,fade=t=out:st=43.75:d=0.5,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:44.29[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 23 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 44.29 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
