#!/usr/bin/env bash
# Voice cleanup chain used for public/audio/voice.wav (input: original recording).
# HPF 75 Hz -> light FFT denoise -> mud cut 280 Hz -> presence +2 dB @3.2 kHz -> air shelf
# -> de-esser -> 2.5:1 compressor -> loudness -16 LUFS (final mix is mastered to -14 LUFS).
set -euo pipefail
ffmpeg -y -i "$1" -af "highpass=f=75,afftdn=nf=-50:nr=8,equalizer=f=280:t=q:w=1.2:g=-2.5,equalizer=f=3200:t=q:w=1.0:g=2,equalizer=f=11000:t=h:w=0.7:g=1.5,deesser=i=0.35:m=0.5:f=0.5,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=1.5,loudnorm=I=-16:TP=-1.5:LRA=7" -ar 48000 -ac 1 public/audio/voice.wav
