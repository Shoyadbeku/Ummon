"""Ummon Ovozim Space'ini Hugging Face'ga joylash.

    HF_TOKEN=hf_... python deploy.py Baxtbek97/ummon-ovozim --parol MAXFIY

1. Space (Gradio, CPU basic) yaratiladi, PAROL secret qo'shiladi.
2. Klon ovoz shu parol bilan shifrlanib, ovoz.enc bo'lib yuklanadi.
3. Kod fayllari yuklanadi. Boshqa qo'lda sozlash kerak emas.
"""

import argparse
import os

from huggingface_hub import HfApi

BU = os.path.dirname(os.path.abspath(__file__))
OVOZ = os.path.join(BU, "..", "voice_design", "ovozlar", "mening_ovozim_tez.pt")
FAYLLAR = {
    "app.py": os.path.join(BU, "app.py"),
    "requirements.txt": os.path.join(BU, "requirements.txt"),
    "packages.txt": os.path.join(BU, "packages.txt"),
    "README.md": os.path.join(BU, "README.md"),
    "uz_matn.py": os.path.join(BU, "..", "voice_design", "uz_matn.py"),
    "ovoz_shifr.py": os.path.join(BU, "ovoz_shifr.py"),
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("space", help="egasi/space-nomi")
    p.add_argument("--parol", required=True, help="ovoz shu parol bilan shifrlanadi va Space'ga PAROL secret bo'lib qo'yiladi")
    p.add_argument("--ovoz", default=OVOZ, help="VoiceClonePrompt .pt fayli")
    a = p.parse_args()

    from ovoz_shifr import shifrla

    api = HfApi(token=os.environ.get("HF_TOKEN"))
    api.create_repo(a.space, repo_type="space", space_sdk="gradio", exist_ok=True)
    api.add_space_secret(a.space, "PAROL", a.parol)
    with open(a.ovoz, "rb") as f:
        api.upload_file(path_or_fileobj=shifrla(f.read(), a.parol), path_in_repo="ovoz.enc",
                        repo_id=a.space, repo_type="space")
    for nom, yol in FAYLLAR.items():
        api.upload_file(path_or_fileobj=yol, path_in_repo=nom, repo_id=a.space, repo_type="space")
    print("Space:", f"https://huggingface.co/spaces/{a.space}")


if __name__ == "__main__":
    main()
