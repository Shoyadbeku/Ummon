#!/bin/bash
# Text file -> natural Uzbek speech in the user's voice:
#   1) Navoiy TTS (CosyVoice2 Uzbek) reads the text fluently, zero-shot cloned from a reference clip
#   2) RVC (trained 30 epochs on the user's recordings) converts the timbre to the user's voice
# usage: speak.sh <text_file> <out.wav>   (paths below point at this session's scratchpad setup)
set -e
S=${S:-/tmp/claude-0/-home-user-Ummon/f0acb166-f246-510b-9b0b-793bb35cd6b5/scratchpad}
HERE=$(cd "$(dirname "$0")" && pwd)
TXT=$(realpath "$1"); OUT=$(realpath -m "$2"); TMP="${OUT%.*}.navoiy.wav"
REF_TEXT="Maktab yillarida oilasi bilan Buyuk Britaniyaga ko'chib o'tgan. Otasining e'tirozlariga qaramay, Angliyada o'qish davomida o'z mustaqil qarori bilan Londondagi Temz Velli universitetida musiqa yo'nalishida tahsil olgan."
"$S/venv2/bin/python" "$HERE/navoiy_tts.py" --cosyvoice "$S/ext/CosyVoice" --cv2 "$S/models/navoiy/cv2" \
  --navoiy "$S/models/navoiy/code" --ref "$S/cb_ref/ref_seg4.wav" --ref_text "$REF_TEXT" --text_file "$TXT" --out "$TMP"
INDEX_RATE=0 "$HERE/rvc_convert.sh" "$S/ext/Applio" "$S/venv4/bin/python" "$HERE/trained/rvc_myvoice_30e.pth" \
  "$S/ext/Applio/logs/myvoice/myvoice.index" "$TMP" "$OUT" 1
rm -f "$TMP"
echo "saved $OUT"
