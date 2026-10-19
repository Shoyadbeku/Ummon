#!/bin/sh
# Ovoz + sintez qilingan past "drone" fon (hech qanday tashqi musiqa kerak emas)
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 assets/ovoz.mp3)
T=$(echo "$D + 0.6" | bc)
ffmpeg -y -v error -i assets/ovoz.mp3 \
  -f lavfi -i "aevalsrc='0.30*sin(2*PI*55*t)*(0.7+0.3*sin(2*PI*0.11*t))+0.22*sin(2*PI*82.4*t)*(0.6+0.4*sin(2*PI*0.07*t+1))+0.12*sin(2*PI*110.3*t)+0.06*sin(2*PI*164.8*t)*(0.5+0.5*sin(2*PI*0.05*t))':s=44100:d=$T" \
  -f lavfi -i "anoisesrc=c=brown:a=0.08:d=$T:r=44100" \
  -filter_complex "[1]lowpass=f=400,volume=0.22,afade=t=in:d=3,afade=t=out:st=$(echo "$T - 3" | bc):d=3[dr];[2]lowpass=f=600,volume=0.25[n];[0]apad=pad_dur=0.6,loudnorm=I=-16:TP=-1.5[v];[v][dr][n]amix=inputs=3:normalize=0,aformat=channel_layouts=stereo" \
  -t $T -c:a aac -b:a 192k out/audio.m4a
