#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + foydalanuvchi ovozi + tovush effektlari (sfx.py)
# Zack D. montaji: zarbalarda qisqa oq chaqnash (qog'oz tutashi 5.42 s, nur to'r pardaga urilishi 16.21 s,
# hujayralar kuyishi 25.46 s, qora dog' 33.54 s), yorqin joylarda yengil "bloom" (Quyosh porlashi),
# vinyetka va kino donadorligi, oxirida qorong'ilik. Effektlar ovoz eshitilganda pasayadi (sidechain).
# montaj.sh <kadrlar_papkasi> <ovoz.wav> <chiqish.mp4> [sfx.wav]
FR=${1:-/tmp/claude-0/frames}; VO=${2:-/tmp/claude-0/work/ovoz.wav}; OUT=${3:-zack_test/quyosh/quyosh_kozni_kuydiradi.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_quyosh.wav}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$(dirname "$0")/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 1001 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,format=gbrp,split[base][hi];
      [hi]lutrgb=r='max(0,(val-190)*4)':g='max(0,(val-190)*4)':b='max(0,(val-190)*4)',gblur=sigma=28[glow];
      [base][glow]blend=all_mode=screen:all_opacity=0.55,format=yuv420p,
      lutyuv=y='min(255,val*1.8+80)':enable='between(t,5.41,5.50)+between(t,16.20,16.29)+between(t,25.45,25.54)+between(t,33.53,33.62)',
      vignette=PI/5,noise=alls=5:allf=t,
      fade=t=out:st=41.3:d=0.4,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 26 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
