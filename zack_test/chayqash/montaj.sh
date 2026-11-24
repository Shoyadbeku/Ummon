#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + foydalanuvchi ovozi + tovush effektlari (sfx.py)
# Zack D. montaji: har bir kesimda qisqa oq chaqnash, yengil vinyetka va kino donadorligi, oxirida qorong'ilik.
# Effektlar ovoz eshitilganda pasayadi (sidechain).
# montaj.sh <kadrlar_papkasi> <ovoz.wav> <chiqish.mp4> [sfx.wav]
FR=${1:-/tmp/claude-0/frames_full}; VO=${2:-/tmp/claude-0/work/ovoz.wav}; OUT=${3:-zack_test/chayqash/ogiz_chayqash.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_chayqash.wav}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$(dirname "$0")/sfx.py" "$SFX"
# kesimlar (kadr -> soniya): 37 88 141 190 284 347 418 463 514 588 681
FL=""; for f in 37 88 141 190 284 347 418 463 514 588 681; do
  t=$(python3 -c "print(round(($f-1)/24,3))"); FL="$FL+between(t,$t,$(python3 -c "print(round(($f-1)/24+0.07,3))"))"; done
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 760 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.6+70)':enable='${FL#+}',
      vignette=PI/5,noise=alls=5:allf=t,
      fade=t=out:st=31.2:d=0.45,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad=whole_dur=31.667,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 25 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
