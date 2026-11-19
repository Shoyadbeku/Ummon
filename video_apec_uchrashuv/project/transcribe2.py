import json,sys
from faster_whisper import WhisperModel
m=WhisperModel("large-v3",device="cpu",compute_type="int8",cpu_threads=4)
import numpy as np
aud=np.fromfile(sys.argv[1],dtype=np.float32)
segs,info=m.transcribe(aud,language="uz",beam_size=5,vad_filter=True,word_timestamps=True,condition_on_previous_text=False)
out=[]
for s in segs:
    out.append({"words":[(w.start,w.end,w.word) for w in s.words],"start":round(s.start,2),"end":round(s.end,2),"text":s.text.strip()})
    print(f"[{s.start:7.2f}-{s.end:7.2f}] {s.text.strip()}",flush=True)
json.dump(out,open(sys.argv[2],"w"),ensure_ascii=False,indent=1)
