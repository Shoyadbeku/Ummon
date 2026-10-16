"""Cut the training clips at 24 kHz from the original recordings and extract CosyVoice2 flow features
(speech tokens, 80-bin mel, speaker embedding) for fine-tuning Navoiy's flow (timbre) on the user's voice."""
import json
import os
import subprocess
import sys

import numpy as np
import sherpa_onnx as so
import soundfile as sf
import torch

S, cosy, cv2, originals_json, manifest, out = sys.argv[1:7]
for p in (f"{cosy}/third_party/Matcha-TTS", cosy):
    sys.path.insert(0, p)
from cosyvoice.cli.cosyvoice import CosyVoice2  # noqa: E402

originals = json.load(open(originals_json))  # {"full16k": "/path/orig.mp3", ...}


def vad_starts(wav16):
    a, _ = sf.read(wav16, dtype="float32")
    cfg = so.VadModelConfig()
    cfg.silero_vad.model = f"{S}/models/silero_vad.onnx"
    cfg.silero_vad.min_silence_duration, cfg.silero_vad.min_speech_duration = 0.5, 0.8
    cfg.silero_vad.max_speech_duration, cfg.sample_rate = 12, 16000
    vad, w, segs = so.VoiceActivityDetector(cfg, buffer_size_in_seconds=1200), cfg.silero_vad.window_size, []
    for i in range(0, len(a), w):
        vad.accept_waveform(a[i:i + w])
        while not vad.empty():
            segs.append((vad.front.start, len(vad.front.samples)))
            vad.pop()
    vad.flush()
    while not vad.empty():
        segs.append((vad.front.start, len(vad.front.samples)))
        vad.pop()
    return segs


segs = {src: vad_starts(f"{S}/data/{src}.wav") for src in originals}
model = CosyVoice2(cv2, load_jit=False, load_trt=False, fp16=False)
fe = model.frontend
os.makedirs(f"{out}/wav24", exist_ok=True)
data = []
for item in json.load(open(manifest)):
    name = os.path.basename(item["wav"])[:-4]
    src, k = name.rsplit("_", 1)
    st, n = segs[src][int(k)]
    t0, dur = max(0, st - 1600) / 16000, (n + 4000) / 16000
    wav24 = f"{out}/wav24/{name}.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i",
                    originals[src], "-ac", "1", "-ar", "24000", wav24], check=True)
    feat, _ = fe._extract_speech_feat(wav24)
    tok, _ = fe._extract_speech_token(wav24)
    emb = fe._extract_spk_embedding(wav24)
    L = min(feat.shape[1] // 2, tok.shape[1])
    data.append({"name": name, "speech_token": tok[0, :L].cpu(), "speech_feat": feat[0, :2 * L].cpu(),
                 "embedding": emb[0].cpu()})
    print(name, L, flush=True)
torch.save(data, f"{out}/flow_data.pt")
torch.save(torch.stack([d["embedding"] for d in data]).mean(0), f"{out}/speaker_embedding.pt")
print("clips", len(data))
