#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + ovoz (ovoz.mp3) + tovush effektlari (sfx.py)
# Zack D. montaji: "shart", "ochib", "ochiq teshik", "qonga" da oq chaqnash; "qon tomir", "o'lim", "yallig'lanish", "xo'ppoz" da qizil;
# vinyetka, kino donadorligi, oxirida qorong'ilik.
# montaj.sh <kadrlar_papkasi> <ovoz.mp3> <chiqish.mp4> [sfx.wav]
D=$(dirname "$0")
FR=${1:-/tmp/claude-0/frames}; VO=${2:-$D/ovoz.mp3}; OUT=${3:-$D/burun_tuki.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_burun.wav}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$D/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 1056 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.8+80)':enable='between(t,3.50,3.58)+between(t,7.62,7.70)+between(t,23.88,23.94)+between(t,39.17,39.23)',
      lutrgb=r='min(255,val*1.6+60)':g='val*0.55':b='val*0.55':enable='between(t,24.83,24.91)+between(t,27.67,27.79)+between(t,40.71,40.77)+between(t,42.29,42.41)',
      vignette=PI/5,noise=alls=5:allf=t,
      fade=t=in:st=0:d=0.1,fade=t=out:st=43.55:d=0.4,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:44[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 22 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 44 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
