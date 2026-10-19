#!/usr/bin/env bash
# OmniVoice'ni CPU uchun alohida venv'ga o'rnatadi (bir marta, ~3-5 daqiqa).
set -euo pipefail
VENV="${OVOZ_VENV:-$HOME/.ovoz-venv}"
if [ -x "$VENV/bin/python" ] && "$VENV/bin/python" -c "import omnivoice" 2>/dev/null; then
  echo "tayyor: $VENV"; exit 0
fi
python3 -m venv "$VENV"
"$VENV/bin/pip" install -q torch torchaudio --index-url https://download.pytorch.org/whl/cpu
"$VENV/bin/pip" install -q omnivoice soundfile
echo "o'rnatildi: $VENV"
