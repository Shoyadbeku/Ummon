#!/bin/bash
# Bo'lakli render: har bir bo'lak xato bersa 3 martagacha qayta urinadi
cd "$(dirname "$0")/.."
mkdir -p out/chunks
TOTAL=10189; STEP=1500
for ((a=0; a<TOTAL; a+=STEP)); do
  b=$((a+STEP-1)); [ $b -ge $TOTAL ] && b=$((TOTAL-1))
  out=out/chunks/c_$(printf %05d $a).mp4
  [ -f "$out" ] && continue
  for t in 1 2 3; do
    npx remotion render src/index.ts Hormuz "$out.tmp.mp4" --frames=$a-$b --codec=h264 --crf=16 --concurrency=4 --timeout=120000 --log=error >> out/render_chunks.log 2>&1 && mv "$out.tmp.mp4" "$out" && echo "CHUNK_OK $a-$b" && break
    echo "CHUNK_FAIL $a-$b try $t"
  done
done
echo RENDER_DONE
