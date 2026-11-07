#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + ovoz (ovoz.mp3) + tovush effektlari (sfx.py)
# Zack D. montaji: rentgen, yeyilish, "aqldan ozadi" (qizil), tola uzilishi va "Eng qo'rqinchlisi" da qisqa chaqnash;
# vinyetka, kino donadorligi, oxirida qorong'ilik.
# montaj.sh <kadrlar_papkasi> <ovoz.mp3> <chiqish.mp4> [sfx.wav]
D=$(dirname "$0")
FR=${1:-/tmp/claude-0/frames}; VO=${2:-$D/ovoz.mp3}; OUT=${3:-$D/uyqusizlik.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_uy.wav}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$D/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 1044 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.8+80)':enable='between(t,2.71,2.79)+between(t,4.5,4.56)+between(t,27.79,27.87)+between(t,32.17,32.23)',
      lutrgb=r='min(255,val*1.6+60)':g='val*0.6':b='val*0.6':enable='between(t,19.42,19.54)',
      vignette=PI/5,noise=alls=5:allf=t,
      fade=t=in:st=0:d=0.1,fade=t=out:st=42.75:d=0.75,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:43.5[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 22 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 43.5 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
