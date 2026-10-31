"""Ummon Matn → Ovoz: o'zbekcha matnni egasining klonlangan (RVC v2) ovozida o'qiydi.

Ishlash tartibi:
  1. edge-tts o'zbekcha tayyor ovozda (Sardor yoki Madina) asosiy nutqni yaratadi.
  2. RVC modeli (myvoice.pth) shu nutqni egasining ovoziga aylantiradi.

Ovoz modeli repozitoriyga qo'yilmaydi. U quyidagilardan biridan olinadi:
  - MODEL_PATH (standart: myvoice.pth) — Space'ga yuklangan fayl;
  - MODEL_REPO + MODEL_FILE — yopiq Hugging Face model repozitoriysi
    (HF_TOKEN secret bilan).
"""

import asyncio
import os
import subprocess
import tempfile
import threading
import time
import uuid

import edge_tts
import gradio as gr
from rvc_python.infer import RVCInference

MAX_CHARS = int(os.environ.get("MAX_CHARS", "1500"))
MODEL_PATH = os.environ.get("MODEL_PATH", "myvoice.pth")
MODEL_REPO = os.environ.get("MODEL_REPO", "")
MODEL_FILE = os.environ.get("MODEL_FILE", "rvc_myvoice_30e.pth")

BASE_VOICES = {
    "Sardor (erkak)": "uz-UZ-SardorNeural",
    "Madina (ayol)": "uz-UZ-MadinaNeural",
}

OUT_DIR = os.path.join(tempfile.gettempdir(), "ummon-ovoz")
os.makedirs(OUT_DIR, exist_ok=True)


def resolve_model() -> str:
    if os.path.exists(MODEL_PATH):
        return MODEL_PATH
    if MODEL_REPO:
        from huggingface_hub import hf_hub_download

        return hf_hub_download(MODEL_REPO, MODEL_FILE, token=os.environ.get("HF_TOKEN"))
    raise FileNotFoundError(
        f"Ovoz modeli topilmadi: {MODEL_PATH}. Faylni Space'ga yuklang yoki MODEL_REPO ni sozlang."
    )


rvc = RVCInference(device="cpu:0")
rvc.load_model(resolve_model(), version="v2")
lock = threading.Lock()  # RVC parametrlari umumiy, shuning uchun so'rovlar navbat bilan


def cleanup(max_age=3600):
    now = time.time()
    for name in os.listdir(OUT_DIR):
        path = os.path.join(OUT_DIR, name)
        try:
            if now - os.path.getmtime(path) > max_age:
                os.remove(path)
        except OSError:
            pass


def ovozlashtirish(matn, asosiy_ovoz, tezlik, ohang, protect):
    matn = (matn or "").strip()
    if not matn:
        raise gr.Error("Matn kiriting.")
    if len(matn) > MAX_CHARS:
        raise gr.Error(f"Matn juda uzun: {len(matn)} belgi. Ko'pi bilan {MAX_CHARS} belgi.")
    voice = BASE_VOICES.get(asosiy_ovoz, "uz-UZ-SardorNeural")
    cleanup()

    job = uuid.uuid4().hex
    mp3 = os.path.join(OUT_DIR, f"{job}.mp3")
    wav16 = os.path.join(OUT_DIR, f"{job}-16k.wav")
    out = os.path.join(OUT_DIR, f"ummon-ovoz-{job[:8]}.wav")

    rate = f"{int(tezlik):+d}%"
    try:
        asyncio.run(edge_tts.Communicate(matn, voice, rate=rate).save(mp3))
    except Exception as e:  # tarmoq yoki xizmat xatosi
        raise gr.Error(f"Asosiy nutqni yaratib bo'lmadi (edge-tts): {e}")

    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", mp3, "-ar", "16000", "-ac", "1", wav16],
        check=True,
    )
    with lock:
        rvc.set_params(f0method="rmvpe", f0up_key=int(ohang), index_rate=0, protect=float(protect))
        rvc.infer_file(wav16, out)
    for p in (mp3, wav16):
        try:
            os.remove(p)
        except OSError:
            pass
    return out


with gr.Blocks(title="Ummon Matn → Ovoz") as demo:
    gr.Markdown(
        "# Ummon: Matn → Ovoz\n"
        "O'zbekcha matn yozing, u klonlangan ovozda o'qiladi. "
        "Bepul CPU'da 10 soniyalik nutq taxminan 30–60 soniyada tayyor bo'ladi."
    )
    with gr.Row():
        with gr.Column():
            matn = gr.Textbox(
                label=f"Matn (ko'pi bilan {MAX_CHARS} belgi)",
                lines=6,
                value="Assalomu alaykum! Bu mening sun'iy intellekt yordamida klonlangan ovozim.",
            )
            asosiy = gr.Radio(list(BASE_VOICES), value="Sardor (erkak)", label="Asosiy ovoz")
            tezlik = gr.Slider(-50, 50, value=0, step=5, label="Tezlik (%)")
            ohang = gr.Slider(-12, 12, value=0, step=1, label="Ohang (yarim ton). Madina tanlansa, -12 qo'ying")
            protect = gr.Slider(0, 0.5, value=0.33, step=0.01, label="Undosh himoyasi (protect)")
            btn = gr.Button("Ovozlashtirish", variant="primary")
        with gr.Column():
            natija = gr.Audio(label="Natija", type="filepath")
    btn.click(
        ovozlashtirish,
        [matn, asosiy, tezlik, ohang, protect],
        natija,
        api_name="ovozlashtirish",
    )

demo.queue(default_concurrency_limit=1, max_size=20).launch(theme=gr.themes.Soft())
