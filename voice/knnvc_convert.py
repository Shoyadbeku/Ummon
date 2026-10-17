"""Convert speech (e.g. Navoiy TTS output) into the user's voice with kNN-VC (bshall/knn-vc, MIT):
every WavLM frame of the source is replaced by the average of its k nearest frames from the user's own
recordings, then vocoded. No training; the user's ~9.5 min of clips are the matching set."""
import argparse
import glob

import torch
import torchaudio

ap = argparse.ArgumentParser()
ap.add_argument("--knnvc", required=True, help="bshall/knn-vc checkout")
ap.add_argument("--target_glob", required=True, help="16 kHz wavs of the user's voice")
ap.add_argument("--src", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--topk", type=int, default=4)
a = ap.parse_args()
torch.set_num_threads(4)
knn = torch.hub.load(a.knnvc, "knn_vc", source="local", prematched=True, trust_repo=True, pretrained=True, device="cpu")
wav, sr = torchaudio.load(a.src)
src16 = f"{a.out}.src16.wav"
torchaudio.save(src16, torchaudio.functional.resample(wav.mean(0, keepdim=True), sr, 16000), 16000)
query = knn.get_features(src16)
matching = knn.get_matching_set(sorted(glob.glob(a.target_glob)))
out = knn.match(query, matching, topk=a.topk)
torchaudio.save(a.out, (out / out.abs().max() * 0.9).unsqueeze(0), 16000)
print("saved", a.out, round(out.shape[-1] / 16000, 1), "s")
