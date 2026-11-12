"""Download Mixamo characters / motions from the HF dataset Linzhan/Mixamo-Animations-Characters.
usage: python3 fetch_mixamo.py OUTDIR char:Brian anim:Drinking anim:Dizzy_Idle ..."""
import sys, os, urllib.request
R = "https://huggingface.co/datasets/Linzhan/Mixamo-Animations-Characters/resolve/main"
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
for item in sys.argv[2:]:
    kind, name = item.split(":", 1)
    sub = {"char": "character_refined", "anim": "animation_motion", "tpose": "character_tpose"}[kind]
    ext = ".png" if kind == "tpose" else ".fbx"
    dst = os.path.join(out, f"{kind}_{name}{ext}")
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        print("have", dst); continue
    urllib.request.urlretrieve(f"{R}/{sub}/{name}{ext}", dst)
    print("got", dst, os.path.getsize(dst))
