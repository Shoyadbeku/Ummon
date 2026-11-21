import sys, json
from faster_whisper import WhisperModel
m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4)
import numpy as np
audio=np.fromfile(sys.argv[1],dtype=np.float32)
segs, info = m.transcribe(audio, language="uz", beam_size=5, word_timestamps=True, vad_filter=True)
out=[]
with open(sys.argv[2]+".txt","w") as f:
    for s in segs:
        line=f"[{s.start:7.2f} - {s.end:7.2f}] {s.text.strip()}"
        print(line, flush=True); f.write(line+"\n")
        out.append({"start":s.start,"end":s.end,"text":s.text.strip(),"words":[{"w":w.word,"s":w.start,"e":w.end} for w in s.words]})
json.dump(out, open(sys.argv[2]+".json","w"), ensure_ascii=False, indent=1)
