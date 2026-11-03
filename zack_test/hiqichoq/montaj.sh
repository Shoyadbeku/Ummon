#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + foydalanuvchi ovozi + tovush effektlari (sfx.py)
# Zack D. montaji: har "hik" va zarbada qisqa oq chaqnash (0.38, 2.71, 22.58, 25.0, 30.29, 31.58, 33.13, 38.88 s),
# yengil vinyetka va kino donadorligi, oxirida qorong'ilik. Effektlar ovoz eshitilganda pasayadi (sidechain).
# montaj.sh <kadrlar_papkasi> <ovoz.mp3> <chiqish.mp4> [sfx.wav]
FR=${1:-/tmp/claude-0/frames}; VO=${2:-/tmp/claude-0/work/ovoz.mp3}; OUT=${3:-zack_test/hiqichoq/hiqichoq.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_hiqichoq.wav}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$(dirname "$0")/sfx.py" "$SFX"
FL=""; for t in 0.38 2.71 22.58 25.0 30.29 31.58 33.13 38.88; do FL="$FL+between(t,$t,$(echo "$t+0.07" | bc))"; done
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 960 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.8+80)':enable='${FL#+}',
      vignette=PI/5,noise=alls=5:allf=t,
      fade=t=out:st=39.5:d=0.5,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=3:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:40[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 24 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 40 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
