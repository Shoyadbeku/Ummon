#!/usr/bin/env bash
# Voice cleanup + music ducking + SFX + loudness normalisation (-14 LUFS, -1 dBTP)
set -euo pipefail
VOICE="$1"; OUTDIR="${2:-../public}"
ffmpeg -loglevel error -y -i "$VOICE" -i music.wav -i sfx.wav -filter_complex "
[0:a]aresample=48000,highpass=f=70,afftdn=nf=-55:nr=6,
 equalizer=f=280:t=q:w=1.2:g=-2.5,equalizer=f=3400:t=q:w=1.0:g=2.5,equalizer=f=10500:t=q:w=0.8:g=1.5,
 deesser=i=0.4:m=0.5:f=0.5,
 acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,
 alimiter=limit=0.89,pan=stereo|c0=c0|c1=c0,asplit=3[v][vsc][vsc2];
[1:a]volume=0.42[m];
[m][vsc]sidechaincompress=threshold=0.03:ratio=6:attack=25:release=350:makeup=1[md];
[2:a]volume=0.55[s];
[s][vsc2]sidechaincompress=threshold=0.06:ratio=2.5:attack=10:release=200[sd];
[v][md][sd]amix=inputs=3:normalize=0:duration=first,
 loudnorm=I=-14:TP=-1.0:LRA=9,aresample=48000[out]" -map "[out]" -c:a pcm_s16le -t 35.02 "$OUTDIR/mix.wav"
ffmpeg -hide_banner -i "$OUTDIR/mix.wav" -af ebur128=peak=true -f null - 2>&1 | grep -E "I:|Peak:" | tail -2
