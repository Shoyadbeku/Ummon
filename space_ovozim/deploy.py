"""Ummon Ovozim Space'ini Hugging Face'ga joylash.

    HF_TOKEN=hf_... python deploy.py Baxtbek97/ummon-ovozim [--parol MAXFIY]

1. Klon ovoz yopiq model repozitoriyga (<egasi>/<space>-voice) yuklanadi.
2. Space (Gradio, CPU basic) yaratiladi va kod yuklanadi.
3. Space'ga VOICE_REPO o'zgaruvchisi, berilsa PAROL secret qo'shiladi.

So'ng Space Settings → Variables and secrets'ga HF_TOKEN (read token) qo'shing:
Space yopiq repozitoriydan ovozni shu token bilan oladi.
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
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("space", help="egasi/space-nomi")
    p.add_argument("--parol", help="Space'ni parol bilan himoyalash")
    p.add_argument("--ovoz", default=OVOZ, help="VoiceClonePrompt .pt fayli")
    a = p.parse_args()

    api = HfApi(token=os.environ.get("HF_TOKEN"))
    ovoz_repo = a.space + "-voice"
    api.create_repo(ovoz_repo, repo_type="model", private=True, exist_ok=True)
    api.upload_file(path_or_fileobj=a.ovoz, path_in_repo="mening_ovozim_tez.pt", repo_id=ovoz_repo)
    print("Ovoz yuklandi (yopiq):", ovoz_repo)

    api.create_repo(a.space, repo_type="space", space_sdk="gradio", exist_ok=True)
    api.add_space_variable(a.space, "VOICE_REPO", ovoz_repo)
    if a.parol:
        api.add_space_secret(a.space, "PAROL", a.parol)
    for nom, yol in FAYLLAR.items():
        api.upload_file(path_or_fileobj=yol, path_in_repo=nom, repo_id=a.space, repo_type="space")
    print("Space:", f"https://huggingface.co/spaces/{a.space}")
    print("Endi Settings → Variables and secrets'ga HF_TOKEN (read) secret qo'shing.")


if __name__ == "__main__":
    main()
