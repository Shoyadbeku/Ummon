#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + ovoz (ovoz.mp3) + tovush effektlari (sfx.py)
# Zack D. montaji: "to'satdan", "xatolik", "uyg'onib" da oq chaqnash; "vahima", "sharpa" va mavjudot hamlasida qizil chaqnash;
# vinyetka, kino donadorligi, oxirida keskin qorong'ilik.
# montaj.sh <kadrlar_papkasi> <ovoz.mp3> <chiqish.mp4> [sfx.wav]
D=$(dirname "$0")
FR=${1:-/tmp/claude-0/frames}; VO=${2:-$D/ovoz.mp3}; OUT=${3:-$D/uyqu_falaji.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_falaj.wav}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$D/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 1176 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.8+80)':enable='between(t,0.58,0.66)+between(t,15.08,15.13)+between(t,31.58,31.70)',
      lutrgb=r='min(255,val*1.6+60)':g='val*0.55':b='val*0.55':enable='between(t,36.71,36.80)+between(t,43.0,43.08)+between(t,47.38,47.50)',
      vignette=PI/4.5,noise=alls=6:allf=t,
      fade=t=in:st=0:d=0.1,fade=t=out:st=48.40:d=0.08,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:49[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 22 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 49 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
