"""Load base YourTTS + LoRA adapter and synthesize Uzbek text in the trained voice."""
import io
import re

import numpy as np
import soundfile as sf
import torch

from common import load_base, normalize_uz
from lora import inject_lora


class VoiceSynth:
    # Only the waveform-decoder adapter is applied by default: it carries the speaker timbre, while the
    # text-encoder/duration adapters learned from noisy transcripts and hurt pronunciation (ASR CER 0.32 vs 0.51).
    def __init__(self, base_dir: str, adapter: str | None, speaker: str, targets=("waveform_decoder",),
                 noise_scale: float = 0.4, noise_scale_dp: float = 0.4):
        torch.set_num_threads(4)
        self.cfg, self.model, self.lang_id = load_base(base_dir)
        if adapter:
            ck = torch.load(adapter, map_location="cpu")
            inject_lora(self.model, r=ck["rank"], alpha=ck["rank"], targets=targets)
            sd = {k: v for k, v in ck["lora"].items() if k.split(".")[0] in targets}
            missing = self.model.load_state_dict(sd, strict=False)
            assert not missing.unexpected_keys, missing.unexpected_keys
        self.model.eval()
        self.model.inference_noise_scale = noise_scale
        self.model.inference_noise_scale_dp = noise_scale_dp
        self.dvec = torch.load(speaker, map_location="cpu").view(1, -1)
        self.sr = self.cfg.audio.sample_rate

    @torch.inference_mode()
    def _sentence(self, text: str, speed: float) -> np.ndarray:
        ids = torch.LongTensor(self.model.tokenizer.text_to_ids(text)).unsqueeze(0)
        self.model.length_scale = 1.0 / speed
        out = self.model.inference(ids, aux_input={"d_vectors": self.dvec,
                                                   "language_ids": torch.LongTensor([self.lang_id])})
        return out["model_outputs"].squeeze().numpy()

    def synthesize(self, text: str, speed: float = 1.0) -> np.ndarray:
        text = normalize_uz(text)
        parts = [p.strip() for p in re.split(r"(?<=[.!?;])\s+", text) if p.strip()]
        pause = np.zeros(int(self.sr * 0.25), dtype=np.float32)
        audio = []
        for p in parts:
            audio += [self._sentence(p, speed), pause]
        wav = np.concatenate(audio) if audio else pause
        return (wav / max(1e-3, np.abs(wav).max()) * 0.9).astype(np.float32)

    def to_wav_bytes(self, wav: np.ndarray) -> bytes:
        buf = io.BytesIO()
        sf.write(buf, wav, self.sr, format="WAV")
        return buf.getvalue()


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--adapter")
    ap.add_argument("--speaker", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    s = VoiceSynth(a.base, a.adapter, a.speaker)
    sf.write(a.out, s.synthesize(a.text), s.sr)
