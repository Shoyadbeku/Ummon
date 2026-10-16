"""Build hybrid MMS models: take some submodules from the base (pronunciation) and others from the fine-tune
(voice), optionally interpolating weights: w = base + alpha * (finetuned - base)."""
import argparse
import shutil
import os

from transformers import VitsModel

ap = argparse.ArgumentParser()
ap.add_argument("base")
ap.add_argument("finetuned")
ap.add_argument("out")
ap.add_argument("--alpha", type=float, nargs="*", default=[],
                help="per-module alpha as module=value, e.g. text_encoder=0 duration_predictor=0 flow=1 decoder=1")
ap.add_argument("--set", nargs="*", default=[])
a = ap.parse_args()
alphas = {kv.split("=")[0]: float(kv.split("=")[1]) for kv in a.set}
base, ft = VitsModel.from_pretrained(a.base).state_dict(), VitsModel.from_pretrained(a.finetuned)
sd = ft.state_dict()
for k in sd:
    al = alphas.get(k.split(".")[0], 1.0)
    if sd[k].is_floating_point():
        sd[k] = base[k] + al * (sd[k] - base[k])
ft.load_state_dict(sd)
ft.save_pretrained(a.out)
for f in ("vocab.json", "tokenizer_config.json", "special_tokens_map.json", "added_tokens.json"):
    if os.path.exists(os.path.join(a.finetuned, f)):
        shutil.copy(os.path.join(a.finetuned, f), a.out)
print("saved", a.out, alphas)
