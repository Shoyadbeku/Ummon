#!/usr/bin/env python3
"""Petrov hikoyasi uchun YouTube kliplaridan ovozsiz montaj.

Har bir abzas o'qilish davomiyligiga teng vaqt oladi (so'z soni / soz_tezligi),
shu vaqt abzasdagi kliplar orasida teng bo'linadi. Natija: petrov_montaj.mp4 (1920x1080, 30 fps).

Talablar: python3, ffmpeg, yt-dlp  (pip install -U yt-dlp)
Ishga tushirish:  python3 montaj.py
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
KESH = os.path.join(HERE, "kesh")
QISM = os.path.join(HERE, "qismlar")
W, H, FPS = 1920, 1080, 30


def run(cmd):
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def yukla(vid, s, dur):
    out = os.path.join(KESH, f"{vid}_{s}_{dur:.1f}.mp4")
    if os.path.exists(out):
        return out
    run(["yt-dlp", "-q", "--no-playlist",
         "-f", "bv*[height<=1080][ext=mp4]/bv*[height<=1080]/b",
         "--download-sections", f"*{s}-{s + dur + 1:.1f}",
         "--force-keyframes-at-cuts", "--remux-video", "mp4",
         "-o", out, f"https://www.youtube.com/watch?v={vid}"])
    return out


def main():
    reja = json.load(open(os.path.join(HERE, "reja.json"), encoding="utf-8"))
    matn = [p for p in open(os.path.join(HERE, "matn.txt"), encoding="utf-8").read().split("\n\n") if p.strip()]
    os.makedirs(KESH, exist_ok=True)
    os.makedirs(QISM, exist_ok=True)

    qismlar = []
    for ab in reja["abzaslar"]:
        jami = len(matn[ab["n"] - 1].split()) / reja["soz_tezligi"]
        har = jami / len(ab["kliplar"])
        for i, k in enumerate(ab["kliplar"]):
            try:
                src = yukla(k["id"], k["s"], har)
            except subprocess.CalledProcessError:
                print(f"! {k['id']} yuklanmadi, o'tkazib yuborildi", file=sys.stderr)
                continue
            out = os.path.join(QISM, f"{ab['n']:02d}_{i}.mp4")
            vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                  f"fps={FPS},setsar=1,format=yuv420p,"
                  f"fade=t=in:st=0:d=0.3,fade=t=out:st={har - 0.3:.2f}:d=0.3")
            # Klip kerakli uzunlikdan qisqa bo'lsa, oxirgi kadr ushlab turiladi.
            run(["ffmpeg", "-y", "-loglevel", "error", "-i", src,
                 "-vf", vf + f",tpad=stop_mode=clone:stop_duration={har:.2f}",
                 "-t", f"{har:.2f}", "-an", "-c:v", "libx264", "-preset", "veryfast",
                 "-crf", "20", out])
            qismlar.append(out)

    ro = os.path.join(QISM, "royxat.txt")
    with open(ro, "w") as f:
        f.writelines(f"file '{os.path.abspath(q)}'\n" for q in qismlar)
    natija = os.path.join(HERE, "petrov_montaj.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", ro, "-c", "copy", "-movflags", "+faststart", natija])
    print("Tayyor:", natija)


if __name__ == "__main__":
    main()
