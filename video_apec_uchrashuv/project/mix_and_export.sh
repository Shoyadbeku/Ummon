#!/bin/bash
# Ovoz zanjiri + musiqa ducking + SFX + −14 LUFS, keyin segmentlarni birlashtirish va 4K eksport
set -e
cd "$(dirname "$0")"
ffmpeg -y -i audio/voice.wav -af "highpass=f=80,lowpass=f=15000,afftdn=nf=-28:tn=1,equalizer=f=250:t=q:w=1:g=-2,equalizer=f=3200:t=q:w=1.2:g=2.5,acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=3dB,alimiter=limit=0.95" -ar 48000 -ac 2 audio/voice_proc.wav
ffmpeg -y -i audio/voice_proc.wav -i audio/music.wav -i audio/sfx.wav -filter_complex "[1:a]volume=0.20[m];[0:a]asplit=2[v][vsc];[m][vsc]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=450:makeup=1[md];[2:a]volume=0.55[s];[v][md][s]amix=inputs=3:normalize=0:duration=longest,loudnorm=I=-14:TP=-1.5:LRA=9" -ar 48000 audio/mix.wav
ls segs/seg_*.mp4 | sort | sed "s/^/file '/;s/$/'/" > concat.txt
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy master_video.mp4
ffmpeg -y -i master_video.mp4 -i audio/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest -movflags +faststart master_1080p.mp4
ffmpeg -y -i master_1080p.mp4 -vf "scale=3840:2160:flags=lanczos,unsharp=5:5:0.4" -c:v libx264 -preset medium -crf 18 -profile:v high -level 5.1 -pix_fmt yuv420p -c:a copy -movflags +faststart final_4K.mp4
