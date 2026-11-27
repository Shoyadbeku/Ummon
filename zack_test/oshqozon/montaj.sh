#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + ovoz (wav) + tovush effektlari (sfx.py)
# Zack D. montaji: rentgenga o'tishda, tig' kislotaga tushganda va finalda oq; "zirhli" da ko'k; "to'xtab" va "o'zini" da qizil chaqnash;
# vinyetka, kino donadorligi.
# montaj.sh <kadrlar_papkasi> <ovoz.wav> <chiqish.mp4> [sfx.wav]
D=$(dirname "$0")
FR=${1:-/tmp/claude-0/frames}; VO=${2:-/tmp/claude-0/audio/ovoz.wav}; OUT=${3:-$D/oshqozon_kislotasi.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_osh.wav}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$D/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 792 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutrgb=r='min(255,val*1.5+50)':g='val*0.6':b='val*0.6':enable='between(t,28.54,28.66)+between(t,29.50,29.58)',
      lutrgb=r='val*0.6':g='min(255,val*1.1+20)':b='min(255,val*1.5+60)':enable='between(t,13.88,13.96)',
      lutyuv=y='min(255,val*1.8+80)':enable='between(t,1.29,1.34)+between(t,3.79,3.84)+between(t,32.0,32.06)',
      vignette=PI/5,noise=alls=5:allf=t,
      fade=t=in:st=0:d=0.1,fade=t=out:st=32.7:d=0.3,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:33.0[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 22 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 33.0 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
