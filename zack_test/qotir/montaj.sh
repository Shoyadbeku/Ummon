#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + foydalanuvchi ovozi + tovush effektlari (sfx.py)
# Zack D. montaji: yiqilish (0.96 s), taqiq belgisi (10.88 s), hujayralar ulanishi (22.83 s), miya (37.29 s) da oq chaqnash;
# qichish (6.08 s) va qashish (8.46 s) da qizil chaqnash; yengil vinyetka va kino donadorligi; oxirida qorong'ilik.
# Effektlar ovoz eshitilganda pasayadi (sidechain).
# montaj.sh <kadrlar_papkasi> <ovoz.wav> <chiqish.mp4> [sfx.wav]
H=$(dirname "$0")
FR=${1:-/tmp/claude-0/frames}; VO=${2:-$H/ovoz.wav}; OUT=${3:-$H/qotir_qichishi.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_qotir.wav}
mkdir -p "$(dirname "$SFX")"
[ -f "$SFX" ] || python3 -I "$H/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 954 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.7+70)':enable='between(t,0.96,1.02)+between(t,10.88,10.94)+between(t,22.83,22.9)+between(t,37.29,37.36)',
      lutrgb=r='min(255,val*1.3+60)':g='val*0.6':b='val*0.6':enable='between(t,6.08,6.17)+between(t,8.46,8.53)',
      vignette=PI/5,noise=alls=5:allf=t,
      fade=t=in:st=0:d=0.08,fade=t=out:st=39.3:d=0.45,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:39.75[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 22 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 39.75 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
