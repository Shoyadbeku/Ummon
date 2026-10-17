"""Synthesize a text file with the trained MMS voice (same chunking/pauses as the web page)."""
import re
import sys

import numpy as np
import soundfile as sf
import torch
from transformers import VitsModel, VitsTokenizer

from uzbek_text import expand_numbers, latin_to_cyrillic, normalize_cyr

model_dir, text_path, out = sys.argv[1:4]
m = VitsModel.from_pretrained(model_dir).eval()
tok = VitsTokenizer.from_pretrained(model_dir)
sr = m.config.sampling_rate
text = open(text_path).read()
pieces = []
for para in [p for p in re.split(r"\n\s*\n", text) if p.strip()]:
    for sent in re.split(r"(?<=[.!?;])\s+", para.strip()):
        parts = [p for p in re.split(r"(?<=[,:])\s*", sent) if normalize_cyr(p)]
        for i, p in enumerate(parts):
            torch.manual_seed(0)
            with torch.no_grad():
                w = m(**tok(normalize_cyr(p), return_tensors="pt")).waveform[0].numpy()
            pieces += [w, np.zeros(int(sr * (0.35 if i == len(parts) - 1 else 0.15)), np.float32)]
            print(normalize_cyr(p), flush=True)
    pieces.append(np.zeros(int(sr * 0.4), np.float32))
wav = np.concatenate(pieces)
sf.write(out, wav / max(1e-3, np.abs(wav).max()) * 0.9, sr)
print("saved", out, round(len(wav) / sr, 1), "s")
