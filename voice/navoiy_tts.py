"""Natural Uzbek speech in the user's own voice with Lison Navoiy TTS (aisha-org/navoiy-tts, Apache-2.0).

Navoiy is CosyVoice2-0.5B fine-tuned on ~600 h of Uzbek; it clones the voice of a short reference clip
(zero-shot) and supports emotion presets. Runs on CPU here (slow, ~RTF 3-10). Model files are mirrored by
.github/workflows/hf-mirror.yml; put the Navoiy checkpoint at <cv2>/llm.pt."""
import argparse
import json
import random
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ap = argparse.ArgumentParser()
ap.add_argument("--cosyvoice", required=True, help="FunAudioLLM/CosyVoice checkout (with third_party/Matcha-TTS)")
ap.add_argument("--cv2", required=True, help="CosyVoice2-0.5B assets dir, llm.pt = Navoiy checkpoint")
ap.add_argument("--navoiy", required=True, help="navoiy-tts repo dir (uztts/normalize.py, emotions_40h.json)")
ap.add_argument("--ref", required=True, help="clean 5-15 s clip of the voice to clone")
ap.add_argument("--text_file", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--ref_text", help="exact transcript of --ref; enables zero-shot cloning (much closer to the reference voice)")
ap.add_argument("--emotion", default="xotirjam", help="used only without --ref_text (instruct mode)")
ap.add_argument("--flow", help="fine-tuned flow state dict from navoiy_train_flow.py (user's timbre)")
ap.add_argument("--speed", type=float, default=1.0)
ap.add_argument("--seed", type=int, default=1986)
a = ap.parse_args()
for p in (a.navoiy, f"{a.cosyvoice}/third_party/Matcha-TTS", a.cosyvoice):
    sys.path.insert(0, p)

import torch  # noqa: E402
from cosyvoice.cli.cosyvoice import CosyVoice2  # noqa: E402
from uztts.normalize import normalize  # noqa: E402

torch.set_num_threads(4)
emotions = {e["uz"]: e for e in json.loads(Path(a.navoiy, "emotions_40h.json").read_text())}
instruction = emotions[a.emotion]["instruct"].strip() + "<|endofprompt|>"
model = CosyVoice2(a.cv2, load_jit=False, load_trt=False, fp16=False)
if a.flow:
    model.model.flow.load_state_dict(torch.load(a.flow, map_location="cpu", weights_only=True), strict=True)
    model.model.flow.eval()

pieces = []
paragraphs = [p for p in re.split(r"\n\s*\n", open(a.text_file).read()) if p.strip()]
for n, para in enumerate(paragraphs):
    random.seed(a.seed + n)
    torch.manual_seed(a.seed + n)
    text = normalize(" ".join(para.split()), mode="infer")
    with torch.inference_mode():
        gen = (model.inference_zero_shot(text, normalize(a.ref_text, mode="infer"), a.ref, stream=False, speed=a.speed)
               if a.ref_text else model.inference_instruct2(text, instruction, a.ref, stream=False, speed=a.speed))
        for r in gen:
            pieces.append(r["tts_speech"].squeeze(0).cpu().numpy())
    pieces.append(np.zeros(int(model.sample_rate * 0.45), np.float32))
    print("done paragraph", n + 1, "/", len(paragraphs), flush=True)
wav = np.concatenate(pieces)
sf.write(a.out, wav / max(1e-3, np.abs(wav).max()) * 0.9, model.sample_rate)
print("saved", a.out, round(len(wav) / model.sample_rate, 1), "s")
