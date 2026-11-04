#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + foydalanuvchi ovozi + tovush effektlari (sfx.py)
# Zack D. montaji: chaqmoq zarbalarida qisqa oq chaqnash (1.46, 30.58, 47.08, 50.58, 51.63, 52.04, 53.71 s),
# yorqin joylarga "glow" (bloom), yengil vinyetka va kino donadorligi, oxirida qorong'ilik.
# Effektlar ovoz eshitilganda pasayadi (sidechain).
# montaj.sh <kadrlar_papkasi> <ovoz.mp3> <chiqish.mp4> [sfx.wav]
FR=${1:-/tmp/claude-0/frames}; VO=${2:-zack_test/chaqmoq/ovoz.mp3}; OUT=${3:-zack_test/chaqmoq/chaqmoq_urishi.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_chaqmoq.wav}
[ -f "$SFX" ] || /tmp/claude-0/bvenv/bin/python -I "$(dirname "$0")/sfx.py" "$SFX"
FL=""; for f in 36 735 1131 1215 1240 1250 1290; do t=$(echo "scale=3; ($f-1)/24" | bc); FL="$FL+between(t,$t,$(echo "$t+0.08" | bc))"; done
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 1312 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,split[b][g];
      [g]curves=all='0/0 0.6/0 1/1',gblur=sigma=18[gl];
      [b][gl]blend=all_mode=screen:all_opacity=0.55,
      lutyuv=y='min(255,val*1.8+90)':enable='${FL#+}',
      vignette=PI/5,noise=alls=5:allf=t,
      fade=t=out:st=54.15:d=0.5,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=3:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:54.667[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 23 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 54.667 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
