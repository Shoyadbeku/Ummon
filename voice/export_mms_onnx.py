"""Export a fine-tuned MMS VitsModel to ONNX (input_ids -> waveform) for in-browser synthesis."""
import argparse
import json

import torch
from transformers import VitsModel, VitsTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("model")
ap.add_argument("--out", required=True)
ap.add_argument("--vocab_out", required=True)
ap.add_argument("--noise", type=float, nargs=2, default=[0.667, 0.8])
a = ap.parse_args()

m = VitsModel.from_pretrained(a.model).eval()
m.noise_scale, m.noise_scale_duration = a.noise
tok = VitsTokenizer.from_pretrained(a.model)


class Export(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.m = m

    def forward(self, input_ids):
        return self.m(input_ids=input_ids).waveform


ids = tok("ассалому алайкум бугун ҳаво жуда яхши", return_tensors="pt").input_ids
with torch.no_grad():
    torch.onnx.export(Export().eval(), (ids,), a.out, opset_version=17, input_names=["input_ids"],
                      output_names=["waveform"], dynamic_axes={"input_ids": {1: "len"}, "waveform": {1: "samples"}},
                      dynamo=False)
json.dump({"vocab": tok.get_vocab(), "pad": tok.pad_token_id, "add_blank": tok.add_blank},
          open(a.vocab_out, "w"), ensure_ascii=False)
print("exported", ids.shape)
