#!/bin/sh
# narration + music with sidechain ducking, then (optionally) mux with the rendered video
set -e
W=/home/user/work
ffmpeg -v error -y -i $W/audio/ovoz.wav -af "aresample=48000,pan=stereo|c0=c0|c1=c0,highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,loudnorm=I=-15:TP=-1.5:LRA=9:linear=true,aresample=48000" $W/audio/voice.wav
ffmpeg -v error -y -i $W/audio/voice.wav -i $W/audio/music.wav -filter_complex \
 "[0:a]asplit=2[v1][vsc];[1:a]aresample=48000,volume=0.55[m];[m][vsc]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=600[md];[v1][md]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:505.5,afade=t=out:st=503.5:d=2" \
 -c:a aac -b:a 192k $W/audio/final_mix.m4a
if [ -n "$1" ]; then ffmpeg -v error -y -i $W/render/video.mp4 -i $W/audio/final_mix.m4a -map 0:v -map 1:a -c:v copy -c:a copy -shortest -movflags +faststart "$1"; fi
