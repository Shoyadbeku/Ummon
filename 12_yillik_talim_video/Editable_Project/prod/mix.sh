#!/bin/bash
# Audio mix: original narration (primary) + original music bed (ducked) + original SFX.
# Usage: mix.sh VOICE.wav OUT.wav
set -e
D=$(cd "$(dirname "$0")" && pwd)
V="$1"; OUT="$2"
TOTAL=336.17

# SFX cue times (seconds): whoosh on section bumpers, impacts on key reveals
WH=(12.0 27.6 29.85 97.0 114.35 164.05 200.9 235.2 290.55)
IM=(2.0 161.35 201.05 266.15)
TK=(51.4 54.06 122.6 128.5 134.9 139.3 141.1 150.6 151.8 220.6)

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
