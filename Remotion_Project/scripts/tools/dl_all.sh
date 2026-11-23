#!/bin/bash
# runs from scratchpad root; args: list file
dl() { id=$1; dir=$2; out="yt/$dir/$id.mp4"; [ -s "$out" ] && { echo "SKIP $id"; return; }
  for try in 1 2; do r=$(timeout 600 node tools/snapdl.js "https://www.youtube.com/watch?v=$id" "$out" 2>&1 | tail -2 | tr '\n' ' '); [ -s "$out" ] && { echo "OK $id $r"; return; }; done; echo "FAIL $id $r"; }
export -f dl
xargs -P 3 -L 1 bash -c 'dl "$0" "$1"' < "$1"
echo ALLDONE
