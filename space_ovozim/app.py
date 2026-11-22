"""Ummon Ovozim: o'zbekcha matnni egasining OmniVoice klon ovozida o'qiydi.

Ishlash tartibi:
  1. Matn normallashtiriladi (uz_matn.py): raqam, foiz, birliklar so'z bilan yoziladi.
  2. Matn gaplarga bo'linadi, har bir gap OmniVoice bilan klon ovozda yaratiladi.
  3. Ixtiyoriy: har bir gap o'zbekcha ASR bilan tekshiriladi, xato bo'lsa qayta yaratiladi.
  4. Radio ishlovi (EQ, kompressor, -16 LUFS) beriladi.

Ovoz fayli (OmniVoice VoiceClonePrompt, .pt) repozitoriyga qo'yilmaydi. U quyidagilardan biridan olinadi:
  - VOICE_PATH (standart: mening_ovozim.pt): Space'ga yuklangan fayl;
  - VOICE_REPO + VOICE_FILE: yopiq Hugging Face model repozitoriysi (HF_TOKEN secret bilan).

PAROL secret o'rnatilsa, so'rovlar faqat shu parol bilan qabul qilinadi.
"""

import os
import re
import subprocess
import tempfile
import threading
import time
import uuid

import gradio as gr
import numpy as np
import soundfile as sf
import torch

from uz_matn import normallash

MAX_CHARS = int(os.environ.get("MAX_CHARS", "1500"))
VOICE_PATH = os.environ.get("VOICE_PATH", "mening_ovozim_tez.pt")
VOICE_REPO = os.environ.get("VOICE_REPO", "")
VOICE_FILE = os.environ.get("VOICE_FILE", "mening_ovozim_tez.pt")
PAROL = os.environ.get("PAROL", "")
ASR_MODEL = "navai-uz/whisper-small-uzbek"
# 16 qadam 32 dan ikki baravar tez, sinovlarda xato oshmadi. GPU bo'lsa NUM_STEP=32 qo'yish mumkin.
GEN = dict(num_step=int(os.environ.get("NUM_STEP", "16")), guidance_scale=2.0, class_temperature=0.0)

OUT_DIR = os.path.join(tempfile.gettempdir(), "ummon-ovozim")
os.makedirs(OUT_DIR, exist_ok=True)
torch.set_num_threads(os.cpu_count() or 2)


def voice_path() -> str:
    if os.path.exists(VOICE_PATH):
        return VOICE_PATH
    if VOICE_REPO:
        from huggingface_hub import hf_hub_download

        return hf_hub_download(VOICE_REPO, VOICE_FILE, token=os.environ.get("HF_TOKEN"))
    raise FileNotFoundError(f"Ovoz fayli topilmadi: {VOICE_PATH}. Faylni yuklang yoki VOICE_REPO ni sozlang.")


from omnivoice import OmniVoice  # noqa: E402
from omnivoice.models.omnivoice import VoiceClonePrompt  # noqa: E402

CUDA = torch.cuda.is_available()
model = OmniVoice.from_pretrained(
    "k2-fsa/OmniVoice",
    device_map="cuda:0" if CUDA else "cpu",
    dtype=torch.float16 if CUDA else torch.float32,
)
SR = model.sampling_rate
prompt = VoiceClonePrompt.load(voice_path())
lock = threading.Lock()  # bitta model, so'rovlar navbat bilan
_asr = None


def asr():
    global _asr
    if _asr is None:
        from transformers import pipeline

        _asr = pipeline("automatic-speech-recognition", model=ASR_MODEL, device=0 if CUDA else -1)
    return _asr


def sodda(t: str) -> str:
    t = re.sub(r"[‘’ʻʼ`']", "", t.lower())
    t = re.sub(r"[^a-zЀ-ӿ ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def cer(a: str, b: str) -> float:
    a, b = sodda(a), sodda(b)
    if not a:
        return 0.0 if not b else 1.0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1] / len(a)


def gaplar(matn: str, max_belgi=220) -> list[str]:
    bolaklar = []
    for gap in re.split(r"(?<=[.!?])\s+", matn.strip()):
        while len(gap) > max_belgi:
            k = gap.rfind(", ", 0, max_belgi)
            if k < 40:
                k = gap.rfind(" ", 0, max_belgi)
            bolaklar.append(gap[: k + 1].strip())
            gap = gap[k + 1 :].strip()
        if gap:
            bolaklar.append(gap)
    return bolaklar


def guruhlar(gap_list: list[str], qisqa=40, max_belgi=160) -> list[str]:
    """Juda qisqa gaplarni ("Bilasizmi?") qo'shnisiga qo'shadi: har bir model chaqiruvi ~20 s
    qo'shimcha vaqt oladi. Uzun gaplar alohida qoladi, chunki birlashtirilganda xato ko'payadi."""
    out = []
    for g in gap_list:
        if out and (len(out[-1]) < qisqa or len(g) < qisqa) and len(out[-1]) + 1 + len(g) <= max_belgi:
            out[-1] += " " + g
        else:
            out.append(g)
    return out


RADIO = (
    "highpass=f=70,equalizer=f=120:t=q:w=1.0:g=2.5,equalizer=f=350:t=q:w=1.2:g=-2,"
    "equalizer=f=3500:t=q:w=1.0:g=2,acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=2,"
    "loudnorm=I=-16:TP=-1.5:LRA=7"
)


def cleanup(max_age=3600):
    now = time.time()
    for name in os.listdir(OUT_DIR):
        path = os.path.join(OUT_DIR, name)
        try:
            if now - os.path.getmtime(path) > max_age:
                os.remove(path)
        except OSError:
            pass


try:  # ZeroGPU (HF PRO) bo'lsa GPU'da, aks holda CPU'da ishlaydi
    import spaces

    gpu = spaces.GPU(duration=120)
except ImportError:
    def gpu(fn):
        return fn


@gpu
def ovozlashtirish(matn, tezlik=0.92, pauza=0.35, tekshirish=False, parol="", progress=gr.Progress()):
    if PAROL and parol != PAROL:
        raise gr.Error("Parol noto'g'ri.")
    matn = (matn or "").strip()
    if not matn:
        raise gr.Error("Matn bo'sh.")
    if len(matn) > MAX_CHARS:
        raise gr.Error(f"Matn juda uzun: {len(matn)} belgi (eng ko'pi {MAX_CHARS}).")
    cleanup()

    bolaklar = guruhlar(gaplar(normallash(matn)))
    t0 = time.time()
    tezlik = float(tezlik) if tezlik else None
    sukut = np.zeros(int(SR * float(pauza)), dtype=np.float32)
    qismlar = []
    with lock:
        for i, gap in enumerate(bolaklar):
            progress(i / len(bolaklar), desc=f"{i + 1}/{len(bolaklar)}-bo'lak")
            eng = None
            for urinish in range(3 if tekshirish else 1):
                torch.manual_seed(urinish)
                audio = model.generate(text=gap, language="uz", voice_clone_prompt=prompt, speed=tezlik, **GEN)[0]
                if not tekshirish:
                    eng = (0.0, audio)
                    break
                eshitildi = asr()({"raw": audio.astype(np.float32), "sampling_rate": SR},
                                  generate_kwargs={"language": "uzbek", "task": "transcribe"})["text"]
                xato = cer(gap, eshitildi)
                if eng is None or xato < eng[0]:
                    eng = (xato, audio)
                if xato <= 0.05:
                    break
            print(f"{i + 1}/{len(bolaklar)}: {len(gap)} belgi, {time.time() - t0:.1f}s", flush=True)
            qismlar += [eng[1].astype(np.float32), sukut]

    xom = os.path.join(OUT_DIR, f"{uuid.uuid4().hex}_xom.wav")
    chiqish = xom.replace("_xom.wav", ".wav")
    sf.write(xom, np.concatenate(qismlar[:-1]), SR)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", xom, "-af", RADIO, "-ar", "48000", chiqish], check=True)
    os.remove(xom)
    return chiqish


with gr.Blocks(title="Ummon Ovozim") as demo:
    gr.Markdown("## Ummon Ovozim\nO'zbekcha matn egasining klonlangan ovozida o'qiladi (OmniVoice).")
    with gr.Row():
        with gr.Column():
            matn = gr.Textbox(label="Matn", lines=7, max_length=MAX_CHARS,
                              value="Bilasizmi? Samarqand shahri 2 700 yildan ham qadimiyroq.")
            tezlik = gr.Slider(0.7, 1.3, value=0.92, step=0.01, label="Tezlik")
            pauza = gr.Slider(0.0, 1.0, value=0.35, step=0.05, label="Gaplar orasidagi pauza (s)")
            tekshirish = gr.Checkbox(value=False, label="ASR bilan tekshirish (aniqroq, lekin 2 marta sekinroq)")
            parol = gr.Textbox(label="Parol", type="password", visible=bool(PAROL))
            btn = gr.Button("Ovozlashtirish", variant="primary")
        out = gr.Audio(label="Natija", type="filepath")
    btn.click(ovozlashtirish, [matn, tezlik, pauza, tekshirish, parol], out, api_name="ovozlashtirish")

demo.queue(default_concurrency_limit=1).launch()
