#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + foydalanuvchi ovozi + tovush effektlari (sfx.py)
# Zack D. montaji: 0–5.6 s "kino" — 2.39:1 qora polosalar va iliq-moviy (teal/orange) rang; sug'urish (4.83 s), tolalar uzilishi
# (25.46, 26.63, 27.79 s), tiqin (29.17 s) da oq chaqnash; yiqilish (8.2 s) va qon favvorasi (30.04 s) da qizil chaqnash;
# yengil vinyetka, kino donadorligi, oxirida qorong'ilik. Effektlar ovoz eshitilganda pasayadi (sidechain).
# montaj.sh <kadrlar_papkasi> <ovoz.mp3> <chiqish.mp4> [sfx.wav]
FR=${1:-/tmp/claude-0/frames}; VO=${2:-zack_test/pichoq/ovoz.mp3}; OUT=${3:-zack_test/pichoq/pichoqni_sugurma.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_pichoq.wav}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$(dirname "$0")/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 949 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      colorbalance=rs=0.06:bs=-0.08:rh=0.08:bh=-0.06:enable='lt(t,5.58)',
      eq=saturation=0.85:enable='between(t,5.58,9.8)',
      lutyuv=y='min(255,val*1.7+70)':enable='between(t,4.83,4.89)+between(t,25.46,25.50)+between(t,26.63,26.67)+between(t,27.79,27.83)+between(t,29.17,29.21)',
      lutrgb=r='min(255,val*1.3+60)':g='val*0.6':b='val*0.6':enable='between(t,8.20,8.30)+between(t,30.04,30.16)',
      drawbox=x=0:y=0:w=iw:h=355:color=black:t=fill:enable='lt(t,5.58)',
      drawbox=x=0:y=ih-355:w=iw:h=355:color=black:t=fill:enable='lt(t,5.58)',
      vignette=PI/5,noise=alls=5:allf=t,
      fade=t=in:st=0:d=0.1,fade=t=out:st=38.9:d=0.6,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:39.54[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 23 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 39.54 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
