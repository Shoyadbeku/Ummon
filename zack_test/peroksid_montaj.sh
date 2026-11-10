#!/bin/bash
# peroksid_montaj.sh <kadrlar_papkasi> <ovoz.wav> <chiqish.mp4>
# PNG kadrlarni 24 fps ga yig'adi, ovozga yengil SFX qo'shadi: kesik "shik" (1.0 s), vishillash (2.9-7.2 s va 18-20 s),
# mikro olamga o'tishda "whoosh" (8.5 s), chandiq zoom'ida zarb (32.6 s).
F="$1"; A="$2"; O="$3"; T=/tmp/claude-0/sfx; mkdir -p $T
ffmpeg -y -loglevel error -f lavfi -i "anoisesrc=c=white:d=0.25:a=0.6" -af "highpass=f=3000,afade=t=in:d=0.02,afade=t=out:st=0.08:d=0.17" $T/cut.wav
ffmpeg -y -loglevel error -f lavfi -i "anoisesrc=c=pink:d=4.3:a=0.25" -af "highpass=f=2500,tremolo=f=11:d=0.6,afade=t=in:d=0.6,afade=t=out:st=3.3:d=1" $T/fizz.wav
ffmpeg -y -loglevel error -f lavfi -i "anoisesrc=c=brown:d=0.9:a=0.7" -af "lowpass=f=900,afade=t=in:d=0.5,afade=t=out:st=0.55:d=0.35" $T/whoosh.wav
ffmpeg -y -loglevel error -f lavfi -i "sine=f=55:d=0.6" -af "volume=2.5,afade=t=out:st=0.05:d=0.55" $T/boom.wav
ffmpeg -y -loglevel error -framerate 24 -pattern_type glob -i "$F/[0-9]*.png" -i "$A" -i $T/cut.wav -i $T/fizz.wav -i $T/fizz.wav -i $T/whoosh.wav -i $T/boom.wav \
  -filter_complex "[2]adelay=1000:all=1,volume=0.5[c];[3]adelay=2900:all=1,volume=0.35[z1];[4]adelay=18000:all=1,volume=0.22[z2];\
[5]adelay=8000:all=1,volume=0.6[w];[6]adelay=32600:all=1,volume=0.5[b];\
[1][c][z1][z2][w][b]amix=inputs=6:duration=first:normalize=0,alimiter=limit=0.95[a]" \
  -map 0:v -map "[a]" -vf "scale=1080:1920:flags=lanczos,unsharp=5:5:0.4,format=yuv420p" \
  -c:v libx264 -preset slow -crf 19 -c:a aac -b:a 192k -movflags +faststart "$O"
ffprobe -v error -show_entries format=duration -of default=nw=1 "$O"
