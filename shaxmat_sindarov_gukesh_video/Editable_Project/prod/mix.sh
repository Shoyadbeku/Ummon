#!/bin/bash
# Audio mix: original narration (primary) + original music bed (ducked) + original SFX.
# Usage: mix.sh VOICE.wav OUT.wav
set -e
D=$(cd "$(dirname "$0")" && pwd)
V="$1"; OUT="$2"
TOTAL=353.40

# SFX cue times (seconds): whoosh on section bumpers, impacts on key reveals
WH=(7.0 12.0 30.0 66.7 93.2 115.6 176.4 266.4 298.1)
IM=(0.9 20.6 88.2 108.1 132.5 258.6)
TK=(49.6 52.0 60.1 101.0 124.9 144.4 160.8 180.9 185.5 201.6 202.4 203.7 219.1)

args=(-i "$V" -i "$D/music_bed.wav")
fc="[0:a]aresample=48000,highpass=f=70,deesser=i=0.35,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=1.5,apad=whole_dur=${TOTAL},asplit=2[voice][sc];"
fc+="[1:a]atrim=0:${TOTAL},volume=0.32[mus];"
fc+="[mus][sc]sidechaincompress=threshold=0.02:ratio=6:attack=40:release=450:makeup=1[musd];"
n=2; sfx=""
for t in "${WH[@]}"; do args+=(-i "$D/sfx_whoosh.wav"); ms=$(python3 -c "print(int(max(0,$t-0.35)*1000))"); fc+="[$n:a]adelay=${ms}|${ms},volume=0.45[s$n];"; sfx+="[s$n]"; n=$((n+1)); done
for t in "${IM[@]}"; do args+=(-i "$D/sfx_impact.wav"); ms=$(python3 -c "print(int($t*1000))"); fc+="[$n:a]adelay=${ms}|${ms},volume=0.55[s$n];"; sfx+="[s$n]"; n=$((n+1)); done
for t in "${TK[@]}"; do args+=(-i "$D/sfx_tick.wav"); ms=$(python3 -c "print(int($t*1000))"); fc+="[$n:a]adelay=${ms}|${ms},volume=0.35[s$n];"; sfx+="[s$n]"; n=$((n+1)); done
ns=$((n-2))
fc+="${sfx}amix=inputs=${ns}:normalize=0[sfx];"
fc+="[voice][musd][sfx]amix=inputs=3:normalize=0:duration=first,atrim=0:${TOTAL},loudnorm=I=-14:TP=-2.5:LRA=9[out]"

ffmpeg -v error -y "${args[@]}" -filter_complex "$fc" -map "[out]" -ar 48000 -ac 2 "$OUT"
ffmpeg -hide_banner -i "$OUT" -af loudnorm=print_format=summary -f null - 2>&1 | grep -E "Input Integrated|Input True Peak"
