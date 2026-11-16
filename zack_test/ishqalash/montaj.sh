#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + ovoz (wav) + tovush effektlari (sfx.py)
# Zack D. montaji: rentgenga o'tishda va operatsiya xonasida oq, "dahshatga", "og'riq" va "yorilib" da qizil chaqnash;
# vinyetka, kino donadorligi.
# montaj.sh <kadrlar_papkasi> <ovoz.wav> <chiqish.mp4> [sfx.wav]
D=$(dirname "$0")
FR=${1:-/tmp/claude-0/frames}; VO=${2:-/tmp/claude-0/audio/ovoz.wav}; OUT=${3:-$D/kozni_ishqalash.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_ish.wav}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$D/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 1056 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutrgb=r='min(255,val*1.5+50)':g='val*0.6':b='val*0.6':enable='between(t,8.08,8.20)+between(t,35.29,35.37)+between(t,39.62,39.75)',
      lutyuv=y='min(255,val*1.8+80)':enable='between(t,4.75,4.80)+between(t,40.21,40.26)',
      vignette=PI/5,noise=alls=5:allf=t,
      fade=t=in:st=0:d=0.1,fade=t=out:st=43.7:d=0.3,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:44.0[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 22 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 44.0 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
