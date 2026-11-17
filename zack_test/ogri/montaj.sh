#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + foydalanuvchi ovozi + tovush effektlari (sfx.py)
# Zack D. montaji: zarbalarda (deraza, eshik, g'oya, chiroq yonishi, sumka tushishi, TV joyida) qisqa oq chaqnash, vinyetka,
# kino donadorligi; eslash (flashback) kadri oq-qora-ko'kish; oxirida qorong'ilik. Effektlar ovoz eshitilganda pasayadi (sidechain).
# montaj.sh <kadrlar_papkasi> <ovoz.wav> <chiqish.mp4> [sfx.wav] [events.json]
D=$(cd "$(dirname "$0")" && pwd)
FR=${1:-/tmp/claude-0/frames_o}; VO=${2:-$D/ovoz.wav}; OUT=${3:-$D/ogri_televizor.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_ogri.wav}; EV=${5:-/tmp/claude-0/audio/events_ogri.json}
mkdir -p "$(dirname "$SFX")"; [ -f "$SFX" ] || python3 -I "$D/sfx.py" "$SFX" $( [ -f "$EV" ] && echo "$EV" )
fl() { awk -v f=$1 'BEGIN{t=(f-1)/24; printf "between(t,%.3f,%.3f)", t, t+0.06}'; }
FLASH="$(fl 234)+$(fl 302)+$(fl 355)+$(fl 715)+$(fl 774)+$(fl 858)"
FB="between(t,$(awk 'BEGIN{printf "%.3f,%.3f", 1006/24, 1066/24}'))"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 1112 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.7+70)':enable='$FLASH',
      hue=s=0.25:enable='$FB',colorbalance=bs=0.18:bm=0.08:enable='$FB',
      eq=saturation=1.08:contrast=1.05,vignette=PI/5,noise=alls=5:allf=t,
      fade=t=in:st=0:d=0.08,fade=t=out:st=45.6:d=0.71,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:46.31[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 22 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 46.31 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
