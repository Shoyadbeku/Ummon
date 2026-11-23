#!/bin/bash
# qc.sh <media_dir> <qc_dir>: middle frame of every shot tiled into sheets
M=$1; Q=$2; mkdir -p $Q
for f in $M/s*.mp4; do i=$(basename $f .mp4); d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $f); ffmpeg -v error -y -ss $(python3 -c "print(float('$d')/2)") -i $f -frames:v 1 -vf "scale=320:180,drawtext=text='$i':x=4:y=4:fontsize=22:fontcolor=yellow:box=1:boxcolor=black@0.7" $Q/$i.jpg; done
cd $Q; ls s*.jpg > all; split -l 60 -d all part
for p in part*; do while read x; do echo "file '$PWD/$x'"; done < $p > $p.txt; ffmpeg -v error -y -f concat -safe 0 -i $p.txt -vf "tile=10x6:padding=2" -frames:v 1 sheet_$p.jpg; done
ls $Q/sheet_*
