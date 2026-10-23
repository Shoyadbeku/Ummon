#!/bin/bash
set -e
A="$1"; cd /opt/work
ffmpeg -v error -y -i "$A" -i music/bgm.wav -i music/sfx.wav -filter_complex "
[0:a]aresample=44100,pan=stereo|c0=c0|c1=c0,highpass=f=70,acompressor=threshold=0.12:ratio=3:attack=10:release=200,adelay=6500|6500,apad=whole_dur=317,asplit=2[v][key];
[1:a]volume='0.42+0.5*(1-min(1,max(0,(t-5.5)/1.5)))+0.5*min(1,max(0,(t-312.6)/1.2))':eval=frame[m0];
[m0][key]sidechaincompress=threshold=0.04:ratio=5:attack=30:release=600:makeup=1[m];
[2:a]volume=0.55[s];
[v][m][s]amix=inputs=3:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:316.99[out]" -map "[out]" -ar 48000 -c:a pcm_s16le music/mix.wav
