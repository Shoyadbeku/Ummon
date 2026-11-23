import sys, json
from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[2], device="cpu", compute_type="int8", cpu_threads=4)
import numpy as np
audio=np.fromfile(sys.argv[1],dtype=np.float32)
segs, info = m.transcribe(audio, language="uz", beam_size=5, word_timestamps=True, vad_filter=True)
out=[]
for s in segs:
    out.append({"start":s.start,"end":s.end,"text":s.text,"words":[[w.start,w.end,w.word] for w in s.words]})
    print(f"[{s.start:7.2f}-{s.end:7.2f}] {s.text}", flush=True)
json.dump(out, open(sys.argv[3],"w"), ensure_ascii=False, indent=1)
