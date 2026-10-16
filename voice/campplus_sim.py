"""Speaker similarity with CAM++ (CosyVoice's campplus.onnx): cosine between each wav's embedding and the
user's mean embedding (navoiy_prep.py output)."""
import sys

import librosa
import numpy as np
import onnxruntime
import torch
import torchaudio.compliance.kaldi as kaldi

onnx_path, ref_emb, *wavs = sys.argv[1:]
sess = onnxruntime.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
ref = torch.load(ref_emb).numpy().ravel()
for w in wavs:
    y, _ = librosa.load(w, sr=16000)
    feat = kaldi.fbank(torch.from_numpy(y).unsqueeze(0), num_mel_bins=80, dither=0, sample_frequency=16000)
    feat = feat - feat.mean(0, keepdim=True)
    e = sess.run(None, {sess.get_inputs()[0].name: feat.unsqueeze(0).numpy()})[0].ravel()
    print(f"{w.split('/')[-1]:45s} sim={np.dot(e, ref) / np.linalg.norm(e) / np.linalg.norm(ref):.3f}")
