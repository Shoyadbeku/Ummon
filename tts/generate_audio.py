#!/usr/bin/env python3
"""
O'zbekcha dublyaj generatori.

tts/script.json dagi ssenariyni o'qiydi va quyidagilarni yaratadi:
  * audio/audio.wav            — butun videoning yagona audio treki
  * src/data/timeline.json     — har bir replika/sfx/pauza vaqti, taglavhalar
                                 va lab-sinxron uchun ovoz amplituda konverti

TTS backendlar (ikkalasi ham bepul va ochiq manbali):
  * mms   — Meta MMS-TTS, `facebook/mms-tts-uzb-script_latin` (VITS).
            O'zbek tili uchun eng tabiiy eshitiladigan ochiq model.
            Talab: pip install torch transformers  (+ HuggingFace'ga internet)
  * espeak — espeak-ng (uz ovozi). Robotroq, lekin to'liq oflayn va yengil.
            Talab: apt install espeak-ng

Ishlatish:
  python3 tts/generate_audio.py                 # avtomatik: mms, bo'lmasa espeak
  python3 tts/generate_audio.py --backend mms
  python3 tts/generate_audio.py --backend espeak
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SR = 22050          # yakuniy audio chastotasi
FPS = 30            # lab-sinxron konverti uchun kadr tezligi

# Har bir qahramon uchun ovoz sozlamalari.
#  pitch_shift — MMS uchun yarim tonlarda (bitta ovozdan 3 xil qahramon)
#  espeak      — espeak-ng parametrlari
VOICES = {
    "er":     {"pitch_shift": -2.0, "tempo": 1.00,
               "espeak": {"voice": "uz+m1", "pitch": 38, "speed": 150}},
    "xotin":  {"pitch_shift": +4.0, "tempo": 1.05,
               "espeak": {"voice": "uz+f3", "pitch": 72, "speed": 160}},
    "kuryer": {"pitch_shift": +0.5, "tempo": 1.12,
               "espeak": {"voice": "uz+m3", "pitch": 50, "speed": 175}},
}


# --------------------------------------------------------------------------- #
#  Yordamchi audio funksiyalar
# --------------------------------------------------------------------------- #
def read_wav(path: Path) -> np.ndarray:
    """Istalgan wav'ni ffmpeg orqali mono float32 SR ga o'tkazib o'qiydi."""
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR),
         "-f", "f32le", "-"],
        check=True, capture_output=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def write_wav(path: Path, data: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(data, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def ffmpeg_filter(data: np.ndarray, af: str) -> np.ndarray:
    """numpy massivga ffmpeg audio filtrini qo'llaydi."""
    with tempfile.TemporaryDirectory() as td:
        src, dst = Path(td) / "a.wav", Path(td) / "b.wav"
        write_wav(src, data)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src),
                        "-af", af, str(dst)], check=True)
        return read_wav(dst)


def trim_silence(x: np.ndarray, thr: float = 0.01) -> np.ndarray:
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(0.03 * SR))
    b = min(len(x), idx[-1] + int(0.08 * SR))
    return x[a:b]


def normalize(x: np.ndarray, peak: float = 0.9) -> np.ndarray:
    m = np.max(np.abs(x)) if len(x) else 0
    return x * (peak / m) if m > 0 else x


def envelope(x: np.ndarray) -> list[float]:
    """Kadrma-kadr RMS (0..1) — og'iz harakati uchun."""
    hop = SR // FPS
    n = int(np.ceil(len(x) / hop))
    env = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-12)
                    for i in range(n)])
    if env.max() > 0:
        env = env / np.percentile(env, 95)
    env = np.clip(env, 0, 1)
    # biroz silliqlash (og'iz titramasligi uchun)
    k = np.array([0.25, 0.5, 0.25])
    env = np.convolve(env, k, mode="same")
    return [round(float(v), 3) for v in env]


# --------------------------------------------------------------------------- #
#  TTS backendlar
# --------------------------------------------------------------------------- #
def clean_text(text: str) -> str:
    # o‘ g‘ ʻ ’ kabi turli apostroflarni bitta ko'rinishga keltiramiz
    return re.sub(r"[‘’ʻʼ`´]", "'", text)


class MMSBackend:
    name = "mms"
    MODEL = "facebook/mms-tts-uzb-script_latin"

    def __init__(self) -> None:
        import torch  # noqa: F401
        from transformers import AutoTokenizer, VitsModel
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(self.MODEL)
        self.model = VitsModel.from_pretrained(self.MODEL).eval()
        self.model.config.speaking_rate = 1.0
        self.model.config.noise_scale = 0.667

    def synth(self, text: str, speaker: str) -> np.ndarray:
        v = VOICES[speaker]
        inputs = self.tok(clean_text(text).lower(), return_tensors="pt")
        self.torch.manual_seed(1234)  # takrorlanuvchan natija
        with self.torch.no_grad():
            wav = self.model(**inputs).waveform[0].cpu().numpy()
        sr = self.model.config.sampling_rate
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "mms.wav"
            pcm = (np.clip(wav, -1, 1) * 32767).astype(np.int16)
            with wave.open(str(p), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
                w.writeframes(pcm.tobytes())
            x = read_wav(p)
        # Qahramon ovozini farqlash: pitch shift (+ tempo)
        f = 2 ** (v["pitch_shift"] / 12)
        af = f"asetrate={int(SR * f)},aresample={SR},atempo={v['tempo'] / f:.4f}"
        return ffmpeg_filter(x, af)


class EspeakBackend:
    name = "espeak"

    def __init__(self) -> None:
        self.bin = shutil.which("espeak-ng") or shutil.which("espeak")
        if not self.bin:
            raise RuntimeError("espeak-ng topilmadi (apt install espeak-ng)")

    def synth(self, text: str, speaker: str) -> np.ndarray:
        e = VOICES[speaker]["espeak"]
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "es.wav"
            subprocess.run([self.bin, "-v", e["voice"], "-p", str(e["pitch"]),
                            "-s", str(e["speed"]), "-g", "2", "-w", str(p),
                            clean_text(text)], check=True)
            return read_wav(p)


def make_backend(choice: str):
    order = ["mms", "espeak"] if choice == "auto" else [choice]
    last = None
    for name in order:
        try:
            b = MMSBackend() if name == "mms" else EspeakBackend()
            print(f"[tts] backend: {b.name}")
            return b
        except Exception as ex:  # noqa: BLE001
            last = ex
            print(f"[tts] '{name}' ishlamadi: {ex.__class__.__name__}: "
                  f"{str(ex)[:160]}", file=sys.stderr)
    raise SystemExit(f"Hech qaysi TTS backend ishlamadi: {last}")


# --------------------------------------------------------------------------- #
#  Effektlar va ovoz effektlari (sintez qilingan — tashqi fayl kerak emas)
# --------------------------------------------------------------------------- #
def apply_effect(x: np.ndarray, effect: str | None) -> np.ndarray:
    if effect == "kitchen":   # oshxonadan, uzoqroqdan, muloyim
        return ffmpeg_filter(x, "highpass=f=180,aecho=0.8:0.6:45|90:0.3|0.15,"
                                "volume=0.85")
    if effect == "muffled":   # qutilar tagidan bo'g'iq baqiriq
        return ffmpeg_filter(x, "lowpass=f=1100,aecho=0.8:0.7:60|120:0.4|0.25,"
                                "volume=1.6")
    return x


def sfx(name: str) -> np.ndarray:
    rng = np.random.default_rng(7)
    t = lambda d: np.arange(int(d * SR)) / SR  # noqa: E731
    if name == "knock":
        out = np.zeros(int(1.6 * SR))
        for at in (0.0, 0.28, 0.56, 1.0, 1.22):
            tt = t(0.12)
            k = (np.sin(2 * np.pi * 140 * tt) + 0.5 * np.sin(2 * np.pi * 310 * tt)
                 + 0.4 * rng.standard_normal(len(tt))) * np.exp(-tt * 45)
            i = int(at * SR)
            out[i:i + len(k)] += k
        return normalize(out, 0.8)
    if name == "horn":   # fura signali
        tt = t(1.3)
        s = sum(np.sign(np.sin(2 * np.pi * f * tt)) for f in (220, 277))
        env = np.minimum(1, tt * 20) * np.minimum(1, (1.3 - tt) * 8)
        env[int(0.45 * SR):int(0.6 * SR)] *= 0.05
        return normalize(s * env, 0.45)
    if name == "crash":  # qutilar ko'chkisi
        tt = t(3.4)
        noise = rng.standard_normal(len(tt))
        rumble = np.sin(2 * np.pi * 55 * tt) * 0.8
        body = (noise * 0.6 + rumble) * np.minimum(1, tt * 6) * np.exp(-tt * 0.9)
        for at in np.sort(rng.uniform(0.05, 2.6, 26)):     # alohida "gup" lar
            tk = t(0.18)
            thud = np.sin(2 * np.pi * rng.uniform(70, 160) * tk) * np.exp(-tk * 30)
            i = int(at * SR)
            body[i:i + len(thud)] += thud * rng.uniform(0.6, 1.4)
        return normalize(ffmpeg_filter(normalize(body), "lowpass=f=2500"), 0.85)
    raise ValueError(name)


# --------------------------------------------------------------------------- #
#  Taglavhalarni bo'laklash
# --------------------------------------------------------------------------- #
def split_subtitles(text: str, start: float, end: float, max_chars: int = 46):
    """Matnni gaplar/vergullar bo'yicha bo'lib, vaqtni harf soniga mutanosib
    taqsimlaydi."""
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
    chunks: list[str] = []
    for p in parts:
        while len(p) > max_chars:
            cut = p.rfind(",", 0, max_chars)
            cut = cut + 1 if cut > 10 else (p.rfind(" ", 0, max_chars) or max_chars)
            chunks.append(p[:cut].strip())
            p = p[cut:].strip()
        if p:
            chunks.append(p)
    total = sum(len(c) for c in chunks) or 1
    out, t = [], start
    for c in chunks:
        d = (end - start) * len(c) / total
        out.append({"text": c, "start": round(t, 3), "end": round(t + d, 3)})
        t += d
    return out


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["auto", "mms", "espeak"], default="auto")
    ap.add_argument("--script", default=str(ROOT / "tts" / "script.json"))
    ap.add_argument("--audio-out", default=str(ROOT / "audio" / "audio.wav"))
    ap.add_argument("--timeline-out",
                    default=str(ROOT / "src" / "data" / "timeline.json"))
    args = ap.parse_args()

    script = json.loads(Path(args.script).read_text(encoding="utf-8"))
    backend = None
    track: list[np.ndarray] = []
    cursor = 0.0
    timeline = []

    for seg in script["segments"]:
        kind = seg["type"]
        item = {"id": seg["id"], "type": kind}
        if kind == "pause":
            audio = np.zeros(int(seg["duration"] * SR), dtype=np.float32)
        elif kind == "sfx":
            audio = sfx(seg["sfx"]).astype(np.float32)
        else:
            backend = backend or make_backend(args.backend)
            print(f"[tts] {seg['speaker']:>6}: {seg['text']}")
            audio = trim_silence(backend.synth(seg["text"], seg["speaker"]))
            audio = normalize(apply_effect(normalize(audio), seg.get("effect")))
            item["speaker"] = seg["speaker"]
            item["text"] = seg.get("subtitle", seg["text"])
            item["env"] = envelope(audio)
        dur = len(audio) / SR
        item["start"] = round(cursor, 3)
        item["end"] = round(cursor + dur, 3)
        if kind == "speech":
            item["subs"] = split_subtitles(item["text"], item["start"], item["end"])
        timeline.append(item)
        track.append(audio)
        cursor += dur

    full = np.concatenate(track)
    write_wav(Path(args.audio_out), full)
    out = {
        "title": script["title"],
        "subtitle": script.get("subtitle", ""),
        "fps": FPS,
        "duration": round(cursor, 3),
        "backend": backend.name if backend else None,
        "segments": timeline,
    }
    tl = Path(args.timeline_out)
    tl.parent.mkdir(parents=True, exist_ok=True)
    tl.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[tts] tayyor: {args.audio_out} ({cursor:.2f} s), {tl}")


if __name__ == "__main__":
    main()
