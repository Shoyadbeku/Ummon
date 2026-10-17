"""Score MMS VITS checkpoints: intelligibility (Uzbek Whisper CER) and write wavs for speaker-similarity scoring."""
import argparse
import difflib
import os
import sys

import numpy as np
import soundfile as sf
import torch
from transformers import VitsModel, VitsTokenizer, WhisperForConditionalGeneration, WhisperProcessor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uzbek_text import normalize_cyr  # noqa: E402

TEXTS = ["assalomu alaykum, bugun havo juda yaxshi.", "men kitob o'qishni yaxshi ko'raman.",
         "kelajakda insonlar marsga uchib boradi.", "bu mening yangi ovozim.",
         "toshkent o'zbekistonning poytaxti.", "ertaga do'stlarim bilan choyxonaga boramiz."]

ap = argparse.ArgumentParser()
ap.add_argument("--whisper", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--noise", type=float, nargs=2, default=[0.667, 0.8])
ap.add_argument("models", nargs="+")
a = ap.parse_args()
torch.set_num_threads(int(os.environ.get("THREADS", "2")))
proc = WhisperProcessor.from_pretrained(a.whisper)
asr = WhisperForConditionalGeneration.from_pretrained(a.whisper).eval()


def transcribe(w):
    f = proc(w, sampling_rate=16000, return_tensors="pt").input_features
    with torch.no_grad():
        ids = asr.generate(f, language="uz", task="transcribe", max_new_tokens=100)
    return proc.batch_decode(ids, skip_special_tokens=True)[0]


for path in a.models:
    m = VitsModel.from_pretrained(path).eval()
    tok = VitsTokenizer.from_pretrained(path)
    m.noise_scale, m.noise_scale_duration = a.noise
    name = os.path.basename(path.rstrip("/"))
    os.makedirs(os.path.join(a.out, name), exist_ok=True)
    errs = []
    for i, t in enumerate(TEXTS):
        torch.manual_seed(0)
        with torch.no_grad():
            w = m(**tok(normalize_cyr(t), return_tensors="pt")).waveform[0].numpy()
        sf.write(os.path.join(a.out, name, f"{i}.wav"), w, 16000)
        ref, hyp = normalize_cyr(t), normalize_cyr(transcribe(w))
        errs.append(1 - difflib.SequenceMatcher(None, ref, hyp).ratio())
    print(f"{name:30s} CER={np.mean(errs):.3f}", flush=True)
