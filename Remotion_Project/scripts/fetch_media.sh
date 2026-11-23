#!/usr/bin/env bash
# Re-downloads every licensed source file into public/media and rebuilds public/audio.
# Usage: bash scripts/fetch_media.sh /path/to/original_voice.wav
set -euo pipefail
cd "$(dirname "$0")/.."
M=public/media; A=public/audio; mkdir -p "$M" "$A" public/blur public/fx
k(){ curl -s -A "Mozilla/5.0" "http://kremlin.ru/events/president/news/$1/videos" | grep -oE 'http://static\.kremlin\.ru/media/events/video/ru/video_high/[A-Za-z0-9]+\.mp4' | head -1; }
clip(){ ffmpeg -nostdin -v error -y -ss "$3" -i "$2" -t "$4" -an -vf "scale=1920:1080,fps=30" -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p "$M/$1.mp4"; }
U78815=$(k 78815); U78856=$(k 78856); U79718=$(k 79718); U81114=$(k 81114)
clip v_presser_walk "$U78815" 22 12;  clip v_presser_close "$U78815" 192 14
clip v_presser_close2 "$U78815" 1192 14; clip v_presser_hall "$U78815" 492 10
clip v_awards_hall "$U78856" 2 12;    clip v_awards_podium "$U78856" 26 14
clip v_awards_wide "$U78856" 86 12;   clip v_awards_putin2 "$U78856" 2392 12
clip v_may9_podium "$U79718" 2 12;    clip v_may9_podium2 "$U79718" 492 14
clip v_may9_podium3 "$U79718" 1192 12
clip v_africa_wide "$U81114" 86 12;   clip v_africa_wide2 "$U81114" 492 12
# Kremlin photos (CC BY 4.0)
curl -s -A "Mozilla/5.0" http://static.kremlin.ru/media/events/photos/big2x/Kb9enb6B9FmwKuwBVNCdtvzmXaAFTAGS.jpeg -o $M/kabaeva_2005.jpg
curl -s -A "Mozilla/5.0" http://static.kremlin.ru/media/events/photos/big2x/1wCiS48DJ5hi77SA2ixkqUjOkl45zkoW.jpeg -o $M/putin_lyudmila_2012.jpg
curl -s -A "Mozilla/5.0" http://static.kremlin.ru/media/events/photos/big2x/neJAOZsq6dBOb7T7o9RAAbh5pKwnndWx.jpg -o /tmp/peskov_group.jpg
python3 -c "from PIL import Image;im=Image.open('/tmp/peskov_group.jpg').crop((540,170,1000,760));im.resize((im.width*2,im.height*2)).save('$M/peskov_2023.jpg',quality=92)"
# Wikimedia Commons originals (Kremlin.ru CC BY 4.0 / CC BY 3.0 / CC BY-SA)
c(){ curl -sL -A "DocumentaryResearch/1.0" "https://commons.wikimedia.org/wiki/Special:FilePath/$2?width=2400" -o "$M/$1"; sleep 5; }
c wedding2.jpg Vladimir_Putin_wedding-2.jpg
c kgb.jpg Vladimir_Putin_in_KGB_uniform.jpg
c lyudmila_1988.jpg Lyudmila_Putin_favourite_photo.jpg
c family2002_1.jpg Vladimir_Putin_with_family_in_Primorsky_Krai_2002-1.jpg
c kabaeva_syd2000.jpg Medalistswaving-syd2000-600pxl.JPG
c spb.jpg Saint_Petersburg_Hermitage_from_Neva_01.jpg
# Tikhonova (edu.gov.ru / Roscongress), cropped to the on-screen video link
curl -sL --compressed -A "Mozilla/5.0" https://photo.roscongress.org/api/structure/photos/fullsize/82c9d27b-eb7e-4a73-b5fd-d4a7ed5389d1.jpg -o /tmp/tik.jpg
python3 -c "from PIL import Image;im=Image.open('/tmp/tik.jpg');s=im.width/1200;c=im.crop((int(885*s),int(158*s),int(1022*s),int(242*s)));c.resize((c.width*2,c.height*2)).save('$M/tikhonova_2024.jpg',quality=92)"
# US Treasury press release paragraph (public domain): screenshot with Playwright (see README)
# Audio
ffmpeg -nostdin -v error -y -i "$1" -af "highpass=f=75,afftdn=nf=-30:tn=1,equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3200:t=q:w=1.0:g=2,deesser=i=0.35,acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,loudnorm=I=-16:TP=-1.5:LRA=9" -ar 48000 -ac 2 $A/voice.wav
echo "Done. Generate music/sfx/blur/grain as described in README.md"
