#!/usr/bin/env bash
# Hamma shotlarni 3 ta parallel navbatda (qolgan joyidan) render qiladi.
# Foydalanish: ZACK_ASSETS=... run_all.sh FRAMES_DIR
FR=${1:?frames}; cd "$(dirname "$0")"
q() { for i in "$@"; do python3 render_shot.py --shot $i --out "$FR/s$(printf %02d $i)" 2>&1 | grep -E "DONE|Error:|Traceback"; done; }
q 3 4 5 14 > "$FR/q1.log" &
q 8 13 12 > "$FR/q2.log" &
q 9 10 11 > "$FR/q3.log" &
wait
echo ALLDONE >> "$FR/q1.log"
