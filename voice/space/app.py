"""Mening ovozim: Uzbek text -> fluent speech (Navoiy TTS / CosyVoice2, public demo speaker)
-> the owner's timbre (RVC model trained on their recordings). CPU-friendly; runs on a Hugging Face Space."""
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from huggingface_hub import hf_hub_download, snapshot_download

ROOT = Path(__file__).resolve().parent
EXT, MODELS = ROOT / "ext", ROOT / "models"
RVC_PTH = ROOT / "rvc_myvoice_30e.pth"
# Navoiy reads with its own public demo speaker; the RVC model then turns that into the owner's voice,
# so no raw recording of the owner has to be shipped with the app.
REF_WAV = MODELS / "navoiy" / "demo" / "long_form.wav"
REF_TEXT = ("Alisher Navoiy merosi o'zbek tili va adabiyotining bebaho xazinasidir. "
            "Navoiy TTS zamonaviy sun'iy intellekt yordamida tabiiy o'zbekcha nutq yaratadi.")
PITCH_SHIFT = -9  # demo speaker ~250 Hz -> owner ~145 Hz
COSYVOICE_REPO = "https://github.com/FunAudioLLM/CosyVoice.git"
APPLIO_REPO = "https://github.com/IAHispano/Applio.git"


def setup():
    EXT.mkdir(exist_ok=True)
    if not (EXT / "CosyVoice").exists():
        subprocess.run(["git", "clone", "-q", "--depth", "1", "--recursive", COSYVOICE_REPO, str(EXT / "CosyVoice")],
                       check=True)
    if not (EXT / "Applio").exists():
        subprocess.run(["git", "clone", "-q", "--depth", "1", APPLIO_REPO, str(EXT / "Applio")], check=True)
    cv2 = MODELS / "cv2"
    if not (cv2 / "llm.pt").exists():
        snapshot_download("FunAudioLLM/CosyVoice2-0.5B", local_dir=cv2, allow_patterns=[
            "CosyVoice-BlankEN/*", "campplus.onnx", "cosyvoice2.yaml", "flow.pt", "hift.pt",
            "speech_tokenizer_v2.onnx", "config.json", "configuration.json"])
        ckpt = hf_hub_download("aisha-org/navoiy-tts", "emotion_600h_joint.pt")
        state = torch.load(ckpt, map_location="cpu", weights_only=True)
        torch.save({k: v for k, v in state.items() if torch.is_tensor(v)}, cv2 / "llm.pt")
    snapshot_download("aisha-org/navoiy-tts", local_dir=MODELS / "navoiy", allow_patterns=["uztts/*", "emotions_40h.json", "demo/long_form.wav"])
    res = Path(snapshot_download("IAHispano/Applio", allow_patterns=[
        "Resources/embedders/contentvec/*", "Resources/predictors/rmvpe.pt"])) / "Resources"
    rm = EXT / "Applio" / "rvc" / "models"
    (rm / "embedders" / "contentvec").mkdir(parents=True, exist_ok=True)
    (rm / "predictors").mkdir(parents=True, exist_ok=True)
    for f in (res / "embedders" / "contentvec").iterdir():
        shutil.copy(f, rm / "embedders" / "contentvec" / f.name)
    shutil.copy(res / "predictors" / "rmvpe.pt", rm / "predictors" / "rmvpe.pt")


setup()
for p in (MODELS / "navoiy", EXT / "CosyVoice" / "third_party" / "Matcha-TTS", EXT / "CosyVoice", EXT / "Applio"):
    sys.path.insert(0, str(p))
torch.set_num_threads(os.cpu_count() or 2)

from cosyvoice.cli.cosyvoice import CosyVoice2  # noqa: E402
from uztts.normalize import normalize  # noqa: E402

tts_model = CosyVoice2(str(MODELS / "cv2"), load_jit=False, load_trt=False, fp16=False)
os.chdir(EXT / "Applio")  # Applio resolves its model folders relative to the working directory
from rvc.infer.infer import VoiceConverter  # noqa: E402

vc = VoiceConverter()
lock = threading.Lock()


def synthesize(text: str, speed: float = 1.0) -> str:
    text = (text or "").strip()
    if not text:
        raise ValueError("Matn bo'sh")
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    with lock:
        pieces = []
        for n, para in enumerate(paragraphs):
            random.seed(1986 + n)
            torch.manual_seed(1986 + n)
            with torch.inference_mode():
                for r in tts_model.inference_zero_shot(normalize(" ".join(para.split()), mode="infer"),
                                                       normalize(REF_TEXT, mode="infer"), str(REF_WAV),
                                                       stream=False, speed=speed):
                    pieces.append(r["tts_speech"].squeeze(0).cpu().numpy())
            pieces.append(np.zeros(int(tts_model.sample_rate * 0.45), np.float32))
        wav = np.concatenate(pieces)
        tmp = Path(tempfile.mkdtemp())
        sf.write(tmp / "navoiy.wav", wav / max(1e-3, np.abs(wav).max()) * 0.9, tts_model.sample_rate)
        vc.convert_audio(audio_input_path=str(tmp / "navoiy.wav"), audio_output_path=str(tmp / "ovoz.wav"),
                         model_path=str(RVC_PTH), index_path="", pitch=PITCH_SHIFT, f0_method="rmvpe", index_rate=0.0,
                         volume_envelope=1.0, protect=0.4, embedder_model="contentvec", export_format="WAV")
    return str(tmp / "ovoz.wav")


if __name__ == "__main__":
    import gradio as gr

    def ui(text, speed):
        try:
            return synthesize(text, speed), "Tayyor."
        except Exception as e:  # shown to the user
            return None, f"Xato: {e}"

    with gr.Blocks(title="Mening ovozim") as demo:
        gr.Markdown("# Mening ovozim\nO'zbekcha matn yozing: u ravon o'qiladi va mening ovozimga aylantiriladi. "
                    "Bepul serverda 1 daqiqalik audio bir necha daqiqa oladi.")
        text = gr.Textbox(label="Matn", lines=6, value="Assalomu alaykum! Bu mening ovozimda ravon o'qilgan matn.")
        speed = gr.Slider(0.7, 1.3, value=1.0, step=0.05, label="Tezlik")
        go = gr.Button("Ovozga aylantirish", variant="primary")
        audio = gr.Audio(label="Natija", type="filepath")
        status = gr.Markdown()
        go.click(ui, [text, speed], [audio, status], concurrency_limit=1)
    demo.queue(max_size=20).launch()
