import json, sys
from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[2], device="cpu", compute_type="int8", cpu_threads=4)
import numpy as np, wave
wf=wave.open(sys.argv[1]); a=np.frombuffer(wf.readframes(wf.getnframes()),dtype=np.int16).astype(np.float32)/32768
segs, info = m.transcribe(a, language="uz", word_timestamps=True, vad_filter=True, beam_size=1)
words = []
for s in segs:
    for w in s.words:
        words.append({"s": w.start, "e": w.end, "w": w.word.strip()})
    print(f"{s.start:.1f} {s.text}", flush=True)
json.dump(words, open(sys.argv[3], "w"), ensure_ascii=False)
