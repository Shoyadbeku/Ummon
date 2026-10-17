"""Natural-sounding Uzbek TTS with zero-shot cloning of the user's voice.

Uses the Uzbek Chatterbox fine-tune (Abduqayum/uzbek-tts-natural-speech-chatterbox, MIT) on top of the
base ResembleAI/chatterbox vocoder + voice encoder. Needs the chatterbox-finetuning toolkit on sys.path
(--toolkit) for the model code. Files are mirrored by .github/workflows/hf-mirror.yml."""
import argparse
import random
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

ap = argparse.ArgumentParser()
ap.add_argument("--toolkit", required=True)
ap.add_argument("--models", required=True, help="dir with t3 merged weights, s3gen, ve, conds, tokenizer")
ap.add_argument("--ref", required=True, help="reference wav of the voice to clone (5-12 s, clean)")
ap.add_argument("--text_file", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--exaggeration", type=float, default=0.5)
ap.add_argument("--cfg_weight", type=float, default=0.5)
ap.add_argument("--temperature", type=float, default=0.8)
ap.add_argument("--seed", type=int, default=42)
a = ap.parse_args()
sys.path.insert(0, a.toolkit)
torch.set_num_threads(4)

from safetensors.torch import load_file  # noqa: E402
from src.chatterbox_.models.s3gen import S3Gen  # noqa: E402
from src.chatterbox_.models.t3.t3 import T3  # noqa: E402
from src.chatterbox_.models.tokenizers import EnTokenizer  # noqa: E402
from src.chatterbox_.models.voice_encoder import VoiceEncoder  # noqa: E402
from src.chatterbox_.tts import ChatterboxTTS, Conditionals  # noqa: E402

M = Path(a.models)
ve = VoiceEncoder()
ve.load_state_dict(load_file(M / "ve.safetensors"))
t3 = T3()
t3.hp.text_tokens_dict_size = 2454  # Standard-mode multilingual grapheme vocab
t3 = T3(hp=t3.hp)
missing, _ = t3.load_state_dict(load_file(M / "t3_finetuned_merged.safetensors"), strict=False)
assert not missing, missing[:5]
s3gen = S3Gen()
s3gen.load_state_dict(load_file(M / "s3gen.safetensors"), strict=False)
tok = EnTokenizer(str(M / "tokenizer.json"))
conds = Conditionals.load(M / "conds.pt", map_location="cpu")
engine = ChatterboxTTS(t3.eval(), s3gen.eval(), ve.eval(), tok, "cpu", conds=conds)


def chunks(text, max_chars=140):
    out = []
    for sent in re.split(r"(?<=[.!?])\s+", text.strip()):
        cur = ""
        for part in re.split(r"(?<=,)\s+", sent):
            if cur and len(cur) + len(part) + 1 > max_chars:
                out.append(cur)
                cur = part
            else:
                cur = f"{cur} {part}".strip()
        if cur:
            out.append(cur)
    return [c for c in out if c]


text = open(a.text_file).read()
pieces = []
for para in [p for p in re.split(r"\n\s*\n", text) if p.strip()]:
    for i, c in enumerate(chunks(" ".join(para.split()))):
        random.seed(a.seed + i)
        np.random.seed(a.seed + i)
        torch.manual_seed(a.seed + i)
        with torch.no_grad():
            wav = engine.generate(text=c, audio_prompt_path=a.ref, exaggeration=a.exaggeration,
                                  cfg_weight=a.cfg_weight, repetition_penalty=2.0, temperature=a.temperature)
        w = (wav[0] if isinstance(wav, tuple) else wav).squeeze().cpu().numpy().astype(np.float32)
        nz = np.where(np.abs(w) > 0.01)[0]
        if len(nz):
            w = w[max(0, nz[0] - 1200): nz[-1] + 2400]
        pieces += [w, np.zeros(int(engine.sr * 0.2), np.float32)]
        print("done:", c, flush=True)
    pieces.append(np.zeros(int(engine.sr * 0.35), np.float32))
wav = np.concatenate(pieces)
sf.write(a.out, wav / max(1e-3, np.abs(wav).max()) * 0.9, engine.sr)
print("saved", a.out, round(len(wav) / engine.sr, 1), "s")
