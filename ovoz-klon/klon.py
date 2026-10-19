"""O'zbekcha matnni klonlangan ovozda o'qitadi (OmniVoice, CPU).

Ishlatish: ~/.ovoz-venv/bin/python ovoz-klon/klon.py matn.txt chiqish.mp3
"""
import os
import re
import subprocess
import sys
import time

import numpy as np
import soundfile as sf
import torch
from omnivoice import OmniVoice

HERE = os.path.dirname(os.path.abspath(__file__))
NAMUNA = os.path.join(HERE, "namuna.wav")
# namuna.wav'da aynan shu gap aytilgan; ovoz o'zgarsa, matnni ham yangilang.
NAMUNA_MATNI = (
    "Kuchli yomg'irdan keyin yo'llarni suv bosgani aks etgan video "
    "ijtimoiy tarmoqlarda muhokama uyg'otmoqda."
)
SR = 24000


def tayyorla(matn):
    for belgi in "‘’ʻʼ":
        matn = matn.replace(belgi, "'")
    matn = re.sub(r"\biPhone\b", "Ayfon", matn, flags=re.I)
    matn = re.sub(r"[\"“”«»]", "", matn)
    matn = matn.replace("...", ".").replace("…", ".")
    # Har bir gap alohida yaratiladi: uzun matnda model chalkashmaydi.
    gaplar = re.split(r"(?<=[.!?:])\s+|\n+", matn)
    return [g.strip() for g in gaplar if len(g.strip()) > 1]


def yukla():
    """Modelni va namuna ovozini bir marta yuklaydi (bot uchun ham)."""
    m = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map="cpu", dtype=torch.float32)
    prompt = m.create_voice_clone_prompt(ref_audio=NAMUNA, ref_text=NAMUNA_MATNI)
    return m, prompt


def oqit(m, prompt, matn, log=print):
    """Matnni gaplarga bo'lib o'qitadi va bitta audio massiv qaytaradi."""
    gaplar = tayyorla(matn)
    if not gaplar:
        raise ValueError("matn bo'sh")
    t = time.time()
    qism = []
    for i, gap in enumerate(gaplar):
        a = m.generate(text=gap, language="uz", voice_clone_prompt=prompt)[0]
        qism += [a, np.zeros(int(SR * 0.5), dtype=a.dtype)]
        log(f"{i + 1}/{len(gaplar)} {len(a) / SR:.1f}s audio, {time.time() - t:.0f}s")
    return np.concatenate(qism)


def main():
    matn_fayl, chiqish = sys.argv[1], sys.argv[2]
    m, prompt = yukla()
    audio = oqit(m, prompt, open(matn_fayl, encoding="utf-8").read(),
                 log=lambda s: print(s, flush=True))
    wav = os.path.splitext(chiqish)[0] + ".wav"
    sf.write(wav, audio, SR)
    if not chiqish.endswith(".wav"):
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", wav, "-b:a", "128k", chiqish], check=True)
    print("tayyor:", chiqish)


if __name__ == "__main__":
    main()
