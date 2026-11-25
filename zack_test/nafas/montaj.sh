#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + ovoz (wav) + tovush effektlari (sfx.py)
# Zack D. montaji: rentgenga o'tishda oq, "og'riq", "xavfsizlik", "karbonat", "bo'g'ilish", "qon bosimi" da qizil chaqnash;
# hushdan ketishda ekran chetlari qorayadi (tunnel ko'rish), vinyetka, kino donadorligi.
# montaj.sh <kadrlar_papkasi> <ovoz.wav> <chiqish.mp4> [sfx.wav]
D=$(dirname "$0")
FR=${1:-/tmp/claude-0/frames}; VO=${2:-/tmp/claude-0/audio/ovoz.wav}; OUT=${3:-$D/nafas_ushlash.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_nafas.wav}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$D/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 996 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutrgb=r='min(255,val*1.5+50)':g='val*0.6':b='val*0.6':enable='between(t,9.88,10.0)+between(t,18.13,18.25)+between(t,25.21,25.33)+between(t,28.0,28.1)+between(t,35.38,35.5)',
      lutyuv=y='min(255,val*1.8+80)':enable='between(t,3.0,3.06)+between(t,11.29,11.33)+between(t,31.96,32.0)',
      vignette=angle='PI/5+if(gt(t,37.1),min(1,(t-37.1)/4.2)*PI/4.2,0)':eval=frame,noise=alls=5:allf=t,
      fade=t=in:st=0:d=0.1,fade=t=out:st=41.0:d=0.5,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:41.5[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 22 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 41.5 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
