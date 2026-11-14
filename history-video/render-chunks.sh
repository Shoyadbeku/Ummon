#!/usr/bin/env bash
# Resumable render: video in chunks (skips finished ones), audio separately, then join.
set -euo pipefail
cd "$(dirname "$0")"
TOTAL=21855 # = durationInFrames of HistoryVideo (see src/HistoryVideo.tsx)
CH=2200
mkdir -p out/chunks
i=0
for ((s=0; s<TOTAL; s+=CH)); do
  e=$((s+CH-1)); ((e>=TOTAL)) && e=$((TOTAL-1))
  f=$(printf "out/chunks/c%02d.mp4" $i)
  if [ ! -f "$f" ]; then
    npx remotion render HistoryVideo "$f.part.mp4" --frames=$s-$e --muted --concurrency=4 --crf=20 --log=error
    mv "$f.part.mp4" "$f"
  fi
  echo "chunk $i done ($s-$e)"
  i=$((i+1))
done
ls out/chunks/c*.mp4 | sed "s|^out/|file '|;s|$|'|" > out/list.txt
# Audio mixed with ffmpeg (same curve as HistoryVideo.tsx): voice starts at 1s, music 11% under voice
VOL="if(lt(t,0.833),0.32*t/0.833,if(lt(t,1.5),0.32-0.21*(t-0.833)/0.667,if(lt(t,725.17),0.11,if(lt(t,726.5),0.11+0.21*(t-725.17)/1.33,if(lt(t,726.83),0.32,max(0,0.32*(728.5-t)/1.67))))))"
ffmpeg -y -loglevel error -f concat -safe 0 -i out/list.txt -i public/voice.mp3 -i public/music.mp3 \
  -filter_complex "[1:a]adelay=1000|1000,aresample=48000,aformat=channel_layouts=stereo[v];[2:a]aresample=48000,volume='$VOL':eval=frame[m];[v][m]amix=inputs=2:duration=longest:normalize=0,atrim=0:728.5[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -movflags +faststart out/meri_selest.mp4
# Smaller upload copy (~270 MB)
ffmpeg -y -loglevel error -i out/meri_selest.mp4 -c:v libx264 -preset veryfast -crf 21 -maxrate 4500k -bufsize 9000k -pix_fmt yuv420p -c:a copy -movflags +faststart out/meri_selest_youtube.mp4
echo ALL_DONE
