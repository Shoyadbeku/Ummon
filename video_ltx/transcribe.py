import sys, json
from faster_whisper import WhisperModel
m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
import numpy as np, wave
w=wave.open(sys.argv[1]); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
segs, info = m.transcribe(a, language="uz", beam_size=1, vad_filter=True)
out=[]
for s in segs:
    out.append({"start":round(s.start,2),"end":round(s.end,2),"text":s.text.strip()})
    print(f"[{s.start:7.1f}-{s.end:7.1f}] {s.text.strip()}", flush=True)
json.dump(out, open(sys.argv[2],"w"), ensure_ascii=False, indent=1)
