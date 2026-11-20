#!/usr/bin/env bash
# Stock media'ni qayta yuklash (Mixkit + Wikimedia Commons). Repoga xom fayllar qo'yilmagan.
set -euo pipefail
cd "$(dirname "$0")/../public"
mkdir -p video sfx music img
UA="ShortsMediaFetcher/1.0 (educational video project)"
for id in 46741 34477 23485 9686 39474 8825 13192 8890 18262 18305 45703 4508 41273 46353 22973 23104 23666 47495; do
  [ -s video/$id.mp4 ] || curl -sfL -A "$UA" -o video/$id.mp4 https://assets.mixkit.co/videos/$id/$id-1080.mp4 \
    || curl -sfL -A "$UA" -o video/$id.mp4 https://assets.mixkit.co/videos/$id/$id-720.mp4
done
for id in 2908 2950 1492 1133 1490 788 1486 790 2903 3005 2364 1053 2357 2918 1054 1143 1989 1999 645 1936 2951 498; do
  [ -s sfx/$id.mp3 ] || curl -sfL -A "$UA" -o sfx/$id.mp3 https://assets.mixkit.co/active_storage/sfx/$id/$id-preview.mp3
done
[ -s music/76.mp3 ] || curl -sfL -A "$UA" -o music/76.mp3 https://assets.mixkit.co/music/76/76.mp3
ffmpeg -y -v error -ss 6.833 -t 40 -i music/76.mp3 -ar 48000 -ac 2 audio/music_bed.wav
# Commons rasmlari (standart 1280px thumbnail; 429 bo'lsa kutib qayta urinadi)
python3 - <<'PY'
import json, hashlib, urllib.parse, subprocess, time, os
for e in json.load(open('img/commons_meta.json')):
    if os.path.exists(e['file']) and os.path.getsize(e['file']) > 1000: continue
    t = e['title'][5:].replace(' ', '_'); h = hashlib.md5(t.encode()).hexdigest(); q = urllib.parse.quote(t)
    w = '960' if t.endswith('.svg') else '1280'
    url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{h[0]}/{h[:2]}/{q}/{w}px-{q}" + ('.png' if t.endswith('.svg') else '')
    for i in range(6):
        if subprocess.run(['curl', '-sf', '-A', 'ShortsMediaFetcher/1.0', '-o', e['file'], url]).returncode == 0: break
        time.sleep(10 * (i + 1))
    time.sleep(3)
PY
echo "Media tayyor."
