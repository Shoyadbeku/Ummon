#!/bin/bash
# Build public/soundtrack.wav from the ORIGINAL narration (unchanged words/timing):
#  1. voice: high-pass, noise reduction, presence EQ, compression, de-essing, loudness -16 LUFS
#  2. original ambient drone + wind bed (synthesised here -> no third-party music licence needed), ducked under voice
#  3. soft whoosh + low hit at each chapter card
# usage: build_audio.sh <original.wav>
set -e
IN="$1"
cd "$(dirname "$0")/.."
OUT=public/soundtrack.wav
TMP=$(mktemp -d)
DUR=813.4

ffmpeg -v error -y -i "$IN" -af "highpass=f=70,afftdn=nf=-30:tn=1,equalizer=f=200:t=q:w=1:g=-1.5,equalizer=f=3200:t=q:w=1.2:g=2.5,acompressor=threshold=-20dB:ratio=3:attack=8:release=180:makeup=2,deesser=i=0.35,loudnorm=I=-16:TP=-1.5:LRA=9,aformat=sample_rates=48000:channel_layouts=stereo" "$TMP/voice.wav"

ffmpeg -v error -y -f lavfi -i "aevalsrc='0.22*sin(2*PI*55*t)*(0.6+0.4*sin(2*PI*0.05*t))+0.16*sin(2*PI*82.41*t)*(0.6+0.4*sin(2*PI*0.037*t+1))+0.10*sin(2*PI*110*t)*(0.5+0.5*sin(2*PI*0.029*t+2))+0.05*sin(2*PI*164.81*t)*(0.5+0.5*sin(2*PI*0.021*t))|0.22*sin(2*PI*55.2*t)*(0.6+0.4*sin(2*PI*0.047*t))+0.16*sin(2*PI*82.6*t)*(0.6+0.4*sin(2*PI*0.033*t+1))+0.10*sin(2*PI*110.3*t)*(0.5+0.5*sin(2*PI*0.031*t+2))+0.05*sin(2*PI*165.1*t)*(0.5+0.5*sin(2*PI*0.019*t))':s=48000:d=$DUR" \
  -f lavfi -i "anoisesrc=c=pink:r=48000:a=0.25:d=$DUR" \
  -filter_complex "[0]lowpass=f=900,aecho=0.8:0.7:120|240:0.3|0.2,volume=0.55[d];[1]lowpass=f=500,highpass=f=80,volume='0.35+0.25*sin(2*PI*0.03*t)':eval=frame,aformat=channel_layouts=stereo[w];[d][w]amix=inputs=2:normalize=0,afade=t=in:d=4,afade=t=out:st=$(echo "$DUR-6"|bc):d=6" "$TMP/bed.wav"

# chapter transition hits (seconds)
HITS="0.2 76.4 171.8 268.4 319.4 385.3 443.5 528.5 583.4 647.3 724.7 794.3"
ffmpeg -v error -y -f lavfi -i "anoisesrc=c=white:r=48000:a=0.5:d=1.4" -f lavfi -i "aevalsrc='0.9*sin(2*PI*48*t)*exp(-2.5*t)':s=48000:d=2.5" \
  -filter_complex "[0]bandpass=f=1800:w=1600,afade=t=in:d=0.9:curve=exp,afade=t=out:st=0.95:d=0.45,volume=0.35[a];[1]volume=0.8[b];[a]adelay=0|0[a2];[b]adelay=1000|1000[b2];[a2][b2]amix=inputs=2:normalize=0,aformat=channel_layouts=stereo" "$TMP/hit.wav"
INPUTS=""; FILT=""; n=0
for h in $HITS; do INPUTS="$INPUTS -i $TMP/hit.wav"; ms=$(python3 -c "print(int(max(0,$h-1.0)*1000))"); FILT="$FILT[$n]adelay=${ms}|${ms}[h$n];"; n=$((n+1)); done
MIX=""; for i in $(seq 0 $((n-1))); do MIX="$MIX[h$i]"; done
ffmpeg -v error -y $INPUTS -filter_complex "${FILT}${MIX}amix=inputs=$n:normalize=0,apad=whole_dur=$DUR" -t $DUR "$TMP/hits.wav"

# duck bed under voice, mix
ffmpeg -v error -y -i "$TMP/voice.wav" -i "$TMP/bed.wav" -i "$TMP/hits.wav" -filter_complex \
  "[0]asplit[v][key];[1]volume=0.22[bed];[bed][key]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=600[ducked];[2]volume=0.5[fx];[v][ducked][fx]amix=inputs=3:normalize=0,alimiter=limit=0.95,apad=whole_dur=$DUR" \
  -t $DUR -ar 48000 "$OUT"
ffmpeg -v info -i "$OUT" -af ebur128=framelog=quiet -f null - 2>&1 | grep -A3 "Integrated" | head -4
cp "$TMP/voice.wav" public/voice_enhanced.wav
echo done
