"""Cosine similarity between generated wavs and the target speaker's d-vector (YourTTS speaker encoder)."""
import glob
import os
import sys

import numpy as np
import torch
from TTS.tts.utils.speakers import SpeakerManager

base, ref_path, *dirs = sys.argv[1:]
sm = SpeakerManager(encoder_model_path=f"{base}/model_se.pth", encoder_config_path=f"{base}/config_se.json", use_cuda=False)
ref = torch.load(ref_path).view(-1)
for d in dirs:
    sims = [torch.nn.functional.cosine_similarity(torch.tensor(sm.compute_embedding_from_clip(f)).view(-1), ref, 0).item()
            for f in sorted(glob.glob(f"{d}/*.wav"))]
    print(f"{os.path.basename(d):30s} speaker_sim={np.mean(sims):.3f}", flush=True)
