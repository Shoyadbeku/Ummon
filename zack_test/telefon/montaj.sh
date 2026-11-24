#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (432x768 -> 1080x1920, lanczos) + foydalanuvchi ovozi + tovush effektlari (sfx.py)
# Chaqnashlar Blender'da (kameraga bog'langan kartochkalar). Bu yerda: rang, vinyetka, kino donadorligi, sidechain miks.
# montaj.sh <kadrlar_papkasi> <ovoz.wav> <chiqish.mp4> [sfx.wav]
D=$(cd "$(dirname "$0")" && pwd)
FR=${1:-/tmp/claude-0/frames_t}; VO=${2:-$D/ovoz.wav}; OUT=${3:-$D/bir_koz_telefon.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_telefon.wav}
mkdir -p "$(dirname "$SFX")"; [ -f "$SFX" ] || python3 -I "$D/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 994 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      eq=saturation=1.08:contrast=1.05,vignette=PI/5,noise=alls=4:allf=t,
      fade=t=in:st=0:d=0.08,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.8[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:41.417[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 20 -maxrate 10M -bufsize 20M -r 24 -c:a aac -b:a 192k -t 41.417 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate -of compact "$OUT"
