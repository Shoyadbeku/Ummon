#!/usr/bin/env bash
# Render video + audio, then two-pass loudness master (-14 LUFS, -1 dBTP) and mux.
set -euo pipefail
cd "$(dirname "$0")"
npx remotion render src/index.ts Main out/render_raw.mp4 --codec=h264 --crf=16 --x264-preset=slow
npx remotion render src/index.ts Main out/mix.wav --codec=wav
J=$(ffmpeg -hide_banner -i out/mix.wav -af loudnorm=I=-14:TP=-1.0:LRA=9:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
MI=$(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(f\"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}\")")
ffmpeg -y -i out/render_raw.mp4 -i out/mix.wav -map 0:v -map 1:a -c:v copy \
  -af "loudnorm=I=-14:TP=-1.0:LRA=9:$MI:linear=true,aresample=48000" -c:a aac -b:a 320k -ar 48000 \
  -movflags +faststart -shortest out/Final_Video.mp4
