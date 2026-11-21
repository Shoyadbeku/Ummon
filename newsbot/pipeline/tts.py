"""STEP 8 + 10: Uzbek AI voice-over (OmniVoice, fixed female anchor) and word-level subtitle timing.

Licence note: OmniVoice weights are CC-BY-NC. For a monetised channel switch TTS_ENGINE to a
commercially licensed engine (see README). The interface (synthesize -> audio.wav + timings.json)
stays the same.
"""
import json
import subprocess
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from .config import VOICE_REF, VOICE_REF_TEXT
from .uz_text import normalize

SR = 24000
GAP = 0.22          # pause between sentences (s)
LEAD_IN = 0.35      # silence before first sentence (s)
_model = None
_prompt = None


def _load():
    global _model, _prompt
    if _model is None:
        import torch
        from omnivoice import OmniVoice
        torch.set_num_threads(4)
        _model = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map="cpu", dtype=torch.float32)
        _prompt = _model.create_voice_clone_prompt(str(VOICE_REF), ref_text=VOICE_REF_TEXT.read_text().strip())
    return _model, _prompt


def _trim(a: np.ndarray, thr_db: float = -42) -> np.ndarray:
    """Remove leading/trailing silence so sentence timing is tight."""
    if len(a) == 0:
        return a
    frame = int(0.02 * SR)
    n = len(a) // frame
    if n == 0:
        return a
    e = 20 * np.log10(np.sqrt((a[: n * frame].reshape(n, frame) ** 2).mean(1)) + 1e-9)
    idx = np.where(e > thr_db)[0]
    if len(idx) == 0:
        return a
    s, t = max(0, idx[0] - 2) * frame, min(len(a), (idx[-1] + 3) * frame)
    return a[s:t]


def word_timings(display: str, start: float, end: float) -> list[dict]:
    """Distribute a sentence's span over its display words, weighted by spoken length."""
    words = display.split()
    weights = [max(2, len(normalize(w))) + 1 for w in words]
    total = sum(weights)
    out, t = [], start
    for w, wt in zip(words, weights):
        d = (end - start) * wt / total
        out.append({"text": w, "start": round(t, 3), "end": round(t + d, 3)})
        t += d
    return out


def synthesize(ep_dir: Path, sentences: list[dict], log=print) -> dict:
    """sentences: [{"text": display text, "say": optional override for TTS}] -> writes voice.wav + timings.json"""
    model, prompt = _load()
    chunks = [np.zeros(int(LEAD_IN * SR), dtype=np.float32)]
    t = LEAD_IN
    timings = []
    for i, s in enumerate(sentences):
        say = normalize(s.get("say") or s["text"])
        t0 = time.time()
        a = model.generate(text=say, language="uz", voice_clone_prompt=prompt)[0].astype(np.float32)
        a = _trim(a)
        dur = len(a) / SR
        timings.append({"i": i, "text": s["text"], "say": say, "start": round(t, 3), "end": round(t + dur, 3)})
        chunks += [a, np.zeros(int(GAP * SR), dtype=np.float32)]
        t += dur + GAP
        log(f"tts {i + 1}/{len(sentences)} {dur:.1f}s audio in {time.time() - t0:.0f}s")
    raw = ep_dir / "voice_raw.wav"
    sf.write(raw, np.concatenate(chunks), SR)
    # broadcast-style polish: highpass, gentle compression, loudness -16 LUFS (social standard)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af",
                    "highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-16:TP=-1.5:LRA=9",
                    "-ar", "48000", str(ep_dir / "voice.wav")], check=True)
    words = []
    for s, tm in zip(sentences, timings):
        ws = word_timings(s["text"], tm["start"], tm["end"])
        hl = {h.lower() for h in s.get("highlight", [])}
        for w in ws:
            core = w["text"].strip(".,!?:;«»\"“”").lower()
            w["highlight"] = core in hl
        words += ws
    data = {"duration": round(t, 3), "sentences": timings, "words": words}
    (ep_dir / "timings.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    return data


def to_srt(words: list[dict], path: Path, max_words: int = 6):
    def ts(x):
        h, r = divmod(x, 3600); m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    lines, i, n = [], 0, 1
    while i < len(words):
        grp = words[i:i + max_words]
        cut = next((k + 1 for k, w in enumerate(grp) if w["text"][-1:] in ".!?"), len(grp))
        grp = grp[:cut]
        lines.append(f"{n}\n{ts(grp[0]['start'])} --> {ts(grp[-1]['end'])}\n{' '.join(w['text'] for w in grp)}\n")
        i += len(grp); n += 1
    path.write_text("\n".join(lines))
