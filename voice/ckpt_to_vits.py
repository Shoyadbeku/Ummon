"""Turn a finetune-hf-vits accelerate checkpoint into a plain VitsModel directory.

The checkpoint stores weight-normed layers as weight_g/weight_v, while VitsModel expects either a plain
`weight` (decoder, flow conv_pre/post) or `parametrizations.weight.original0/1` (wavenet layers)."""
import os
import shutil
import sys

import torch
from safetensors.torch import load_file
from transformers import VitsModel

ckpt_dir, model_dir, out = sys.argv[1:4]
src = load_file(os.path.join(ckpt_dir, "model.safetensors"))
model = VitsModel.from_pretrained(model_dir)
target = model.state_dict()
new, missing = {}, []
for k in target:
    if k in src:
        new[k] = src[k]
    elif k.endswith(".parametrizations.weight.original0") and k.replace(".parametrizations.weight.original0", ".weight_g") in src:
        new[k] = src[k.replace(".parametrizations.weight.original0", ".weight_g")]
    elif k.endswith(".parametrizations.weight.original1") and k.replace(".parametrizations.weight.original1", ".weight_v") in src:
        new[k] = src[k.replace(".parametrizations.weight.original1", ".weight_v")]
    elif k.endswith(".weight") and k[:-7] + ".weight_g" in src:
        g, v = src[k[:-7] + ".weight_g"], src[k[:-7] + ".weight_v"]
        new[k] = g * v / v.norm(dim=tuple(range(1, v.dim())), keepdim=True)
    else:
        missing.append(k)
assert not missing, missing[:10]
model.load_state_dict(new, strict=True)
model.save_pretrained(out)
for f in ("vocab.json", "tokenizer_config.json", "special_tokens_map.json", "added_tokens.json"):
    if os.path.exists(os.path.join(model_dir, f)):
        shutil.copy(os.path.join(model_dir, f), out)
print("converted", out)
