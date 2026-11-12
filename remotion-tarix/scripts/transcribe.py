import json,sys
from faster_whisper import WhisperModel
m=WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4)
import numpy as np,wave
w=wave.open(sys.argv[1]);a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
segs,info=m.transcribe(a,language="uz",word_timestamps=True,vad_filter=True)
out=[]
for s in segs:
    out.append({"start":s.start,"end":s.end,"text":s.text,"words":[{"w":w.word,"s":w.start,"e":w.end} for w in s.words]})
    print(f"{s.start:7.1f} {s.text}",flush=True)
json.dump(out,open("transcript.json","w"),ensure_ascii=False)
