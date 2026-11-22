#!/usr/bin/env bash
# Yangi muhitda Ummon Diktor'ni tayyorlash: venv, CPU torch, OmniVoice va o'zbekcha ASR.
# Ishlatish: bash voice_design/tayyorla.sh [venv papkasi]
set -euo pipefail
VENV="${1:-$HOME/.ummon-venv}"
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install -q torch torchaudio --index-url https://download.pytorch.org/whl/cpu
"$VENV/bin/pip" install -q omnivoice soundfile transformers
command -v ffmpeg >/dev/null || (apt-get install -y -qq ffmpeg >/dev/null 2>&1 || echo "ffmpeg o'rnatilmadi")
# Modellarni oldindan yuklab olish (birinchi so'rov tezroq bo'lishi uchun)
"$VENV/bin/python" -c "from huggingface_hub import snapshot_download as d; d('k2-fsa/OmniVoice'); d('navai-uz/whisper-small-uzbek')"
echo "Tayyor: $VENV/bin/python voice_design/diktor.py ayt --ovoz mening_ovozim_tez ..."
