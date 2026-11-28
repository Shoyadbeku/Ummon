set -e
python3 -I gfx.py | ffmpeg -y -loglevel error -stats -i build/base.mp4 -f rawvideo -pix_fmt rgba -s 1920x1080 -r 25 -i pipe:0 -i build/mix.wav \
 -filter_complex "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]" -map "[v]" -map 2:a \
 -c:v libx264 -preset medium -crf 17 -profile:v high -level 4.2 -r 25 -g 50 -bf 2 -c:a aac -b:a 320k -ar 48000 \
 -movflags +faststart -shortest build/final.mp4
echo FINAL_OK
