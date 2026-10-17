"""Cut the curated training clips (names like full16k_012) at a chosen sample rate from the original
recordings, using the same VAD segmentation as the transcription step."""
import json
import os
import subprocess
import sys

import sherpa_onnx as so
import soundfile as sf

S, originals_json, manifest, out, sr = sys.argv[1:6]
originals = json.load(open(originals_json))


def vad(wav16):
    a, _ = sf.read(wav16, dtype="float32")
    cfg = so.VadModelConfig()
    cfg.silero_vad.model = f"{S}/models/silero_vad.onnx"
    cfg.silero_vad.min_silence_duration, cfg.silero_vad.min_speech_duration = 0.5, 0.8
    cfg.silero_vad.max_speech_duration, cfg.sample_rate = 12, 16000
    v, w, segs = so.VoiceActivityDetector(cfg, buffer_size_in_seconds=1200), cfg.silero_vad.window_size, []
    for i in range(0, len(a), w):
        v.accept_waveform(a[i:i + w])
        while not v.empty():
            segs.append((v.front.start, len(v.front.samples)))
            v.pop()
    v.flush()
    while not v.empty():
        segs.append((v.front.start, len(v.front.samples)))
        v.pop()
    return segs


segs = {src: vad(f"{S}/data/{src}.wav") for src in originals}
os.makedirs(out, exist_ok=True)
for item in json.load(open(manifest)):
    name = os.path.basename(item["wav"])[:-4]
    src, k = name.rsplit("_", 1)
    st, n = segs[src][int(k)]
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{max(0, st - 1600) / 16000:.3f}", "-t",
                    f"{(n + 4000) / 16000:.3f}", "-i", originals[src], "-ac", "1", "-ar", sr, f"{out}/{name}.wav"],
                   check=True)
print("cut", len(os.listdir(out)))
