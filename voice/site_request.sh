#!/bin/bash
# Process one high-quality request from the site: text file -> Navoiy+RVC wav -> audio-only webm (opus),
# the format the artifact asset store accepts. The upload and the db update are done by Claude's tools.
# usage: site_request.sh <request_id> <text_file> <out_dir>
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
ID=$1; TXT=$2; OUT=$3
"$HERE/speak.sh" "$TXT" "$OUT/$ID.wav"
ffmpeg -hide_banner -loglevel error -y -i "$OUT/$ID.wav" -c:a libopus -b:a 64k "$OUT/$ID.webm"
echo "ready $OUT/$ID.webm"
