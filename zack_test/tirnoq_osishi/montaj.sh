#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + foydalanuvchi ovozi + tovush effektlari (sfx.py)
# Zack D. montaji: qaychi kesishlari (2.46, 3.54 s) va qopqon (6.0 s) da oq chaqnash; teshib chiqish (22.04 s), yiring (28.9 s)
# va "chuqurroq" (33.0 s) da qizil chaqnash; yengil vinyetka va kino donadorligi; oxirida qorong'ilik.
# Effektlar ovoz eshitilganda pasayadi (sidechain).
# montaj.sh <kadrlar_papkasi> <ovoz.wav> <chiqish.mp4> [sfx.wav]
FR=${1:-/tmp/claude-0/frames}; VO=${2:-zack_test/tirnoq_osishi/ovoz.wav}; OUT=${3:-zack_test/tirnoq_osishi/tirnoq_osishi.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_tirnoq_osishi.wav}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$(dirname "$0")/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 938 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.7+70)':enable='between(t,2.46,2.51)+between(t,3.54,3.59)+between(t,6.0,6.06)',
      lutrgb=r='min(255,val*1.3+60)':g='val*0.6':b='val*0.6':enable='between(t,22.04,22.15)+between(t,28.9,29.0)+between(t,33.0,33.08)',
      vignette=PI/5,noise=alls=5:allf=t,
      fade=t=in:st=0:d=0.1,fade=t=out:st=38.6:d=0.48,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:39.08[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 23 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 39.08 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
