"""Fine-tune only Navoiy/CosyVoice2's flow-matching decoder (speech tokens -> mel, i.e. the timbre) on the
user's clips. The LLM (text -> speech tokens: pronunciation and prosody) stays as trained by Navoiy."""
import argparse
import random
import sys
import time

import torch

ap = argparse.ArgumentParser()
ap.add_argument("--cosyvoice", required=True)
ap.add_argument("--cv2", required=True)
ap.add_argument("--data", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--steps", type=int, default=1500)
ap.add_argument("--bs", type=int, default=4)
ap.add_argument("--lr", type=float, default=5e-5)
ap.add_argument("--max_tokens", type=int, default=200, help="crop clips to this many 25 Hz tokens (8 s)")
ap.add_argument("--save_every", type=int, default=250)
a = ap.parse_args()
for p in (f"{a.cosyvoice}/third_party/Matcha-TTS", a.cosyvoice):
    sys.path.insert(0, p)
from cosyvoice.cli.cosyvoice import CosyVoice2  # noqa: E402

torch.set_num_threads(4)
random.seed(0)
torch.manual_seed(0)
flow = CosyVoice2(a.cv2, load_jit=False, load_trt=False, fp16=False).model.flow
data = torch.load(a.data)
flow.train()
opt = torch.optim.AdamW([p for p in flow.parameters() if p.requires_grad], lr=a.lr, weight_decay=0.0)
sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / 50))


def batch(items):
    toks, feats = [], []
    for d in items:
        t, f = d["speech_token"], d["speech_feat"]
        if len(t) > a.max_tokens:
            i = random.randint(0, len(t) - a.max_tokens)
            t, f = t[i:i + a.max_tokens], f[2 * i:2 * (i + a.max_tokens)]
        toks.append(t)
        feats.append(f)
    T, F = max(len(t) for t in toks), max(len(f) for f in feats)
    tok = torch.zeros(len(items), T, dtype=torch.long)
    feat = torch.zeros(len(items), F, feats[0].shape[1])
    for i, (t, f) in enumerate(zip(toks, feats)):
        tok[i, :len(t)], feat[i, :len(f)] = t, f
    return {"speech_token": tok, "speech_token_len": torch.tensor([len(t) for t in toks], dtype=torch.int32),
            "speech_feat": feat, "speech_feat_len": torch.tensor([len(f) for f in feats], dtype=torch.int32),
            "embedding": torch.stack([d["embedding"] for d in items])}


t0, avg = time.time(), None
for step in range(1, a.steps + 1):
    loss = flow(batch(random.sample(data, a.bs)), torch.device("cpu"))["loss"]
    opt.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(flow.parameters(), 5.0)
    opt.step()
    sched.step()
    avg = loss.item() if avg is None else 0.95 * avg + 0.05 * loss.item()
    if step % 10 == 0:
        el = time.time() - t0
        print(f"step {step}/{a.steps} loss {avg:.4f} | {el / step:.2f}s/step eta {el / step * (a.steps - step) / 60:.0f}min",
              flush=True)
    if step % a.save_every == 0 or step == a.steps:
        torch.save(flow.state_dict(), f"{a.out}/flow_step{step}.pt")
print("done", flush=True)
