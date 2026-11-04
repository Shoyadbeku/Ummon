#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + foydalanuvchi ovozi + tovush effektlari (sfx.py)
# Zack D. montaji: zarbalarda qisqa oq chaqnash (bolg'acha 4.04 s, portlash 6.29 s, musht 47.79 s),
# 12-kadrda (hushdan ketish, 26.5–29 s) kadr qorayadi va xiralashadi, yengil vinyetka, kino donadorligi,
# oxirida qorong'ilik. Effektlar ovoz eshitilganda pasayadi (sidechain).
# montaj.sh <kadrlar_papkasi> <ovoz.mp3> <chiqish.mp4> [sfx.wav]
FR=${1:-/tmp/claude-0/frames}; VO=${2:-zack_test/illyuminator/ovoz.mp3}; OUT=${3:-zack_test/illyuminator/illyuminator_sinsa.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_ill.wav}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$(dirname "$0")/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 1308 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.8+80)':enable='between(t,4.04,4.1)+between(t,6.29,6.4)+between(t,47.79,47.84)',
      eq=brightness='if(between(t,26.4,29.0),-0.32*(t-26.4)/2.6,0)':eval=frame,
      boxblur=6:1:enable='between(t,28.0,29.0)',
      vignette=PI/5,noise=alls=5:allf=t,
      fade=t=in:st=0:d=0.12,fade=t=out:st=53.9:d=0.6,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:54.5[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 23 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 54.5 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
