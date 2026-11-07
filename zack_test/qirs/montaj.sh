#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + foydalanuvchi ovozi + tovush effektlari (sfx.py)
# Zack D. montaji: "qirs" zarbalarida qisqa oq chaqnash (1.04, 5.08, 7.79, 32.13, 34.08, 34.54 s),
# yengil vinyetka va kino donadorligi, oxirida keskin qorong'ilik. Effektlar ovoz ostida pasayadi (sidechain).
# montaj.sh <kadrlar_papkasi> <ovoz.mp3> <chiqish.mp4> [sfx.wav]
D=$(dirname "$0")
FR=${1:-/tmp/claude-0/frames}; VO=${2:-$D/ovoz.mp3}; OUT=${3:-$D/barmoq_qirsillashi.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_qirs.wav}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$D/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 1140 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.7+70)':enable='between(t,1.04,1.10)+between(t,5.08,5.14)+between(t,7.79,7.85)+between(t,32.13,32.21)+between(t,34.08,34.14)+between(t,34.54,34.58)',
      vignette=PI/5,noise=alls=5:allf=t,
      fade=t=out:st=47.2:d=0.29,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad=whole_dur=47.5,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 24 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
