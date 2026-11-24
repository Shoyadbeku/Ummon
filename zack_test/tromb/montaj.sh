#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + foydalanuvchi ovozi + tovush effektlari (sfx.py)
# Zack D. montaji: zarbalarda (crash zoom, "tromb", uzilish, o'pkaga tiqilish) qisqa oq chaqnash, vinyetka, kino donadorligi.
# Effektlar ovoz eshitilganda pasayadi (sidechain).
# montaj.sh <kadrlar_papkasi> <ovoz.wav> <chiqish.mp4> [sfx.wav] [events.json]
D=$(cd "$(dirname "$0")" && pwd)
FR=${1:-/tmp/claude-0/frames}; VO=${2:-$D/ovoz.wav}; OUT=${3:-$D/tromb_uzoq_otirish.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx.wav}; EVJ=${5:-/tmp/claude-0/events.json}
mkdir -p "$(dirname "$SFX")"; [ -f "$SFX" ] || python3 -I "$D/sfx.py" "$SFX" "$EVJ"
fl() { awk -v f=$1 'BEGIN{t=(f-1)/24; printf "between(t,%.3f,%.3f)", t, t+0.06}'; }
FLASH="$(fl 41)+$(fl 381)+$(fl 527)+$(fl 700)+$(fl 818)"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 966 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.7+70)':enable='$FLASH',
      eq=saturation=1.08:contrast=1.05,vignette=PI/5,noise=alls=5:allf=t,
      fade=t=in:st=0:d=0.08,fade=t=out:st=39.55:d=0.6,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.85[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:40.25[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 22 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 40.25 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
