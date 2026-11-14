#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + foydalanuvchi ovozi + tovush effektlari (sfx.py) + so'zma-so'z subtitr (subtitr.py)
# Zack D. montaji: nuqta chizilishi (3.42 s) va crash zoom (8.63 s) da oq chaqnash, salbiy lahzalarda (25.25, 34.13 s) qizil chaqnash,
# yengil vinyetka va kino donadorligi, oxirida qorong'ilik. Effektlar ovoz eshitilganda pasayadi (sidechain).
# montaj.sh <kadrlar_papkasi> <ovoz.wav> <chiqish.mp4>
H=$(dirname "$0")
FR=${1:-/tmp/claude-0/frames}; VO=${2:-$H/ovoz.wav}; OUT=${3:-$H/oq_koylakdagi_nuqta.mp4}
SFX=/tmp/claude-0/audio/sfx_nuqta.wav; ASS=/tmp/claude-0/audio/nuqta.ass
mkdir -p /tmp/claude-0/audio
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$H/sfx.py" "$SFX"
python3 -I "$H/subtitr.py" "$ASS"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 998 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.6+60)':enable='between(t,3.42,3.47)+between(t,8.63,8.69)',
      lutrgb=r='min(255,val*1.25+50)':g='val*0.65':b='val*0.65':enable='between(t,25.25,25.33)+between(t,34.13,34.2)',
      vignette=PI/5,noise=alls=4:allf=t,
      subtitles=$ASS:fontsdir=/usr/share/fonts/opentype/inter,
      fade=t=in:st=0:d=0.1,fade=t=out:st=41.1:d=0.45,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:41.58[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 22 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 41.58 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
