#!/bin/bash
# sheet.sh <video> <interval_sec> <out.jpg> : contact sheet with timestamps, 5 columns
v=$1; iv=$2; out=$3
ffmpeg -v error -y -i "$v" -vf "fps=1/$iv,scale=320:-2,drawtext=text='%{pts\:hms}':x=4:y=4:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=5x8:padding=2" -frames:v 1 -q:v 4 "$out"
