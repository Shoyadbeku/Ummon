#!/bin/bash
# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + ovoz (wav) + tovush effektlari (sfx.py)
# Zack D. montaji: rentgenga o'tish, "miyani", "keskin" da oq chaqnash; "ulgurmasa" da qizil chaqnash;
# POV (28.55–31.15 s): ko'z oldi chetlardan qorayib, xiralashadi; vinyetka, kino donadorligi, oxirida qorong'ilik.
# montaj.sh <kadrlar_papkasi> <ovoz.wav> <chiqish.mp4> [sfx.wav]
D=$(dirname "$0")
FR=${1:-/tmp/claude-0/frames}; VO=${2:-/tmp/claude-0/work/ovoz.wav}; OUT=${3:-$D/keskin_turish.mp4}
SFX=${4:-/tmp/claude-0/audio/sfx_turish.wav}
[ -f "$SFX" ] || /tmp/claude-0/wvenv/bin/python -I "$D/sfx.py" "$SFX"
ffmpeg -y -v error -framerate 24 -i "$FR/%04d.png" -i "$VO" -i "$SFX" -frames:v 821 \
  -filter_complex "[0:v]scale=1080:1920:flags=lanczos,
      lutyuv=y='min(255,val*1.8+80)':enable='between(t,5.0,5.08)+between(t,6.5,6.56)+between(t,14.5,14.56)+between(t,33.79,33.84)',
      lutrgb=r='min(255,val*1.6+60)':g='val*0.55':b='val*0.55':enable='between(t,24.62,24.72)',
      vignette=angle='if(between(t,28.55,31.15),PI/5+(t-28.55)/2.6*(PI/2.02-PI/5),PI/5)':eval=frame,
      eq=brightness='if(between(t,28.55,31.15),-0.28*(t-28.55)/2.6,0)':eval=frame,
      boxblur=luma_radius=6:luma_power=1:chroma_radius=6:enable='between(t,29.9,31.15)',
      vignette=PI/4.5,noise=alls=6:allf=t,
      fade=t=in:st=0:d=0.08,fade=t=out:st=33.95:d=0.25,format=yuv420p[v];
    [1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];
    [2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];
    [fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];
    [vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:34.2[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 21 -maxrate 9M -bufsize 18M -c:a aac -b:a 192k -t 34.2 -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of compact "$OUT"
