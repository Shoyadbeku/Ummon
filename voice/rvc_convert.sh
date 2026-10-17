#!/bin/bash
# Convert speech (e.g. Navoiy TTS output) into the user's voice with the RVC model trained by Applio.
# usage: rvc_convert.sh <applio_dir> <python> <model.pth> <index> <input.wav> <output.wav> [pitch_semitones]
set -e
APPLIO=$1; PY=$2; PTH=$3; INDEX=$4; IN=$5; OUT=$6; PITCH=${7:-1}
cd "$APPLIO"
"$PY" core.py infer --input-path "$IN" --output-path "$OUT" --pth-path "$PTH" --index-path "$INDEX" \
  --pitch "$PITCH" --index-rate "${INDEX_RATE:-0.5}" --protect 0.4 --volume-envelope 1.0 --f0-method rmvpe \
  --embedder-model contentvec --export-format WAV
