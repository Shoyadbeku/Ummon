"""LoRA fine-tuning of the YourTTS (VITS) base model on a single speaker's Uzbek recordings (CPU)."""
import argparse
import json
import random
import time

import numpy as np
import soundfile as sf
import torch

from common import load_base, normalize_uz
from lora import inject_lora, lora_state_dict
from TTS.tts.utils.speakers import SpeakerManager

ap = argparse.ArgumentParser()
ap.add_argument("--base", required=True)
ap.add_argument("--data", required=True)
ap.add_argument("--embed_wavs", nargs="+", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--steps", type=int, default=2000)
ap.add_argument("--bs", type=int, default=6)
ap.add_argument("--rank", type=int, default=16)
ap.add_argument("--lr", type=float, default=5e-4)
args = ap.parse_args()
torch.set_num_threads(4)
torch.manual_seed(0)
random.seed(0)

cfg, model, lang_id = load_base(args.base, train=True)

# speaker d-vector of the target voice
sm = SpeakerManager(encoder_model_path=cfg.model_args.speaker_encoder_model_path,
                    encoder_config_path=cfg.model_args.speaker_encoder_config_path, use_cuda=False)
dvec = torch.tensor(sm.compute_embedding_from_clip(args.embed_wavs), dtype=torch.float32)
dvec = dvec / dvec.norm()
torch.save(dvec, f"{args.out}/speaker.pt")

for p in model.parameters():
    p.requires_grad = False
n = inject_lora(model, r=args.rank, alpha=args.rank)
for name, p in model.named_parameters():
    if "lora_" in name or name.startswith("emb_l.") or name.startswith("disc."):
        p.requires_grad = True
gen_params = [p for k, p in model.named_parameters() if p.requires_grad and not k.startswith("disc.")]
disc_params = [p for k, p in model.named_parameters() if k.startswith("disc.")]
print(f"LoRA layers: {n}, trainable generator params: {sum(p.numel() for p in gen_params):,}", flush=True)

items = []
for r in json.load(open(args.data)):
    wav, sr = sf.read(r["wav"], dtype="float32")
    assert sr == cfg.audio.sample_rate
    wav = wav / max(1e-3, np.abs(wav).max()) * 0.95
    ids = model.tokenizer.text_to_ids(normalize_uz(r["text"]))
    items.append((torch.from_numpy(wav), torch.LongTensor(ids)))
print("clips:", len(items), flush=True)


def make_batch(samples):
    samples = sorted(samples, key=lambda s: -len(s[0]))
    wl = max(len(w) for w, _ in samples)
    tl = max(len(t) for _, t in samples)
    wav = torch.zeros(len(samples), 1, wl)
    tok = torch.zeros(len(samples), tl, dtype=torch.long)
    for i, (w, t) in enumerate(samples):
        wav[i, 0, : len(w)] = w
        tok[i, : len(t)] = t
    batch = {
        "waveform": wav,
        "waveform_rel_lens": torch.tensor([len(w) / wl for w, _ in samples]),
        "tokens": tok,
        "token_lens": torch.tensor([len(t) for _, t in samples]),
        "d_vectors": dvec.unsqueeze(0).repeat(len(samples), 1),
        "speaker_ids": None,
        "language_ids": torch.full((len(samples),), lang_id, dtype=torch.long),
    }
    return model.format_batch_on_device(batch)


opt_d = torch.optim.AdamW(disc_params, lr=2e-4, betas=(0.8, 0.99), eps=1e-9)
opt_g = torch.optim.AdamW(gen_params, lr=args.lr, betas=(0.8, 0.99), eps=1e-9, weight_decay=0.0)
sched_g = torch.optim.lr_scheduler.LambdaLR(opt_g, lambda s: min(1.0, (s + 1) / 100))
crit = model.get_criterion()
model.train()
t0 = time.time()
for step in range(1, args.steps + 1):
    batch = make_batch(random.sample(items, args.bs))
    _, ld = model.train_step(batch, crit, 0)
    opt_d.zero_grad()
    ld["loss"].backward()
    torch.nn.utils.clip_grad_norm_(disc_params, 5.0)
    opt_d.step()
    _, lg = model.train_step(batch, crit, 1)
    opt_g.zero_grad()
    lg["loss"].backward()
    torch.nn.utils.clip_grad_norm_(gen_params, 5.0)
    opt_g.step()
    sched_g.step()
    if step % 10 == 0:
        el = time.time() - t0
        print(f"step {step}/{args.steps} gen {lg['loss'].item():.3f} mel {lg['loss_mel'].item():.3f} "
              f"dur {lg['loss_duration'].item():.3f} kl {lg['loss_kl'].item():.3f} disc {ld['loss'].item():.3f} "
              f"| {el / step:.2f}s/step eta {el / step * (args.steps - step) / 60:.0f}min", flush=True)
    if step % 250 == 0 or step == args.steps:
        torch.save({"lora": lora_state_dict(model), "rank": args.rank, "step": step},
                   f"{args.out}/lora_adapter.pt")
print("done", flush=True)
