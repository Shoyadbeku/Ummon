#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + foydalanuvchi ovozi + tovush effektlari (sfx.py) + subtitr (subtitr.py)
# Zack D. montaji: ayvonga urilish (9.46 s) va quchoqqa tushish (20.21 s) da oq chaqnash; yengil vinyetka va
# kino donadorligi; oxirida qorong'ilik. Effektlar ovoz eshitilganda pasayadi (sidechain).
# montaj.sh <kadrlar_papkasi> <ovoz.wav> <chiqish.mp4> [sfx.wav]      (NOSUB=1 — subtitrsiz)
H=$(cd "$(dirname "$0")" && pwd)
FR=${1:-/tmp/claude-0/frames}; VO=${2:-$H/ovoz.wav}; OUT=${3:-$H/balkondan_yiqilgan_bola.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_balkon.wav}
mkdir -p "$(dirname "$SFX")"
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$H/sfx.py" "$SFX"
ASS=/tmp/claude-0/audio/balkon.ass; python3 -I "$H/subtitr.py" "$ASS"
SUB=",ass=$ASS:fontsdir=/usr/share/fonts/opentype/inter"; [ -n "$NOSUB" ] && SUB=""
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 822 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.7+70)':enable='between(t,9.46,9.52)+between(t,20.21,20.27)',
      vignette=PI/5,noise=alls=5:allf=t$SUB,
      fade=t=in:st=0:d=0.1,fade=t=out:st=33.8:d=0.45,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:34.25[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 23 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 34.25 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
