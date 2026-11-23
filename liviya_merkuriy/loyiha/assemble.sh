#!/bin/bash
# Concatenate rendered scenes and mux the final audio mix.
set -e
cd "$(dirname "$0")"
(cd seg && ls [0-9][0-9][0-9].mp4 | sort) | sed "s#^#file '#; s#\$#'#" > seg/list.txt
ffmpeg -loglevel error -y -f concat -safe 0 -i seg/list.txt -c copy seg/video.mp4
ffmpeg -loglevel error -y -i seg/video.mp4 -i aud/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -ar 48000 -movflags +faststart -shortest out/master.mp4
