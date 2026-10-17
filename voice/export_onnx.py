"""Export base YourTTS + merged LoRA adapter + baked speaker embedding to a single ONNX graph for browser use."""
import argparse

import torch

from synth import VoiceSynth

ap = argparse.ArgumentParser()
ap.add_argument("--base", required=True)
ap.add_argument("--adapter", required=True)
ap.add_argument("--speaker", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()

s = VoiceSynth(a.base, a.adapter, a.speaker)
m = s.model


class Export(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.m = m
        self.register_buffer("dvec", s.dvec.clone())
        self.register_buffer("lang", torch.LongTensor([s.lang_id]))

    def forward(self, text, scales):
        m.noise_scale, m.length_scale, m.noise_scale_dp = scales[0], scales[1], scales[2]
        lengths = torch.full((1,), text.shape[1], dtype=torch.long)
        return m.inference(text, aux_input={"x_lengths": lengths, "d_vectors": self.dvec,
                                             "language_ids": self.lang, "durations": None})["model_outputs"]


e = Export().eval()
x = torch.randint(1, 50, (1, 60), dtype=torch.long)
sc = torch.FloatTensor([0.667, 1.0, 0.8])
with torch.no_grad():
    torch.onnx.export(e, (x, sc), a.out, opset_version=17, input_names=["input", "scales"],
                      output_names=["output"], dynamic_axes={"input": {1: "len"}, "output": {2: "samples"}},
                      dynamo=False)
print("vocab", s.model.tokenizer.characters.vocab)
