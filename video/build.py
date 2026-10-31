#!/usr/bin/env python3
"""Kun dayjesti 31.10.2026 — montaj skripti.

Ovoz tartibi: HOOK (anons 12.64-26.16) -> salomlashish (0-11.24) -> asosiy qism (26.16-oxir).
Har bir bo'lim uchun kadrlar ro'yxati; davomiyliklar bo'lim uzunligiga proporsional moslanadi.
"""
import os, subprocess, json, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "build")
VOICE = os.path.join(ROOT, "audio", "voice.wav")
FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
W, H, FPS = 1280, 720, 30

LABELS = {
    "AlJazeera": "Al Jazeera English", "PressTV": "Press TV", "IRNA": "IRNA",
    "AWANI": "Astro Awani", "Euronews": "Euronews", "CNNTurk": "CNN Türk / TV Republika",
    "Sozcu": "Sözcü / Flightradar24", "CGTN": "CGTN Europe", "BBC": "BBC News",
    "ElMundo": "El Mundo", "Pagina12": "Página/12", "QN": "Quotidiano Nazionale / askanews",
    "teleSUR": "teleSUR", "NYPost": "New York Post", "TheStar": "Reuters / The Star",
    "Hurriyet": "Hürriyet / Anadolu", "BangShowbiz": "Bang Showbiz",
}

def find(prefix):
    d, p = prefix.split("/")
    for f in sorted(os.listdir(os.path.join(SRC, d))):
        if f.startswith(p) and f.endswith(".mp4"):
            return os.path.join(SRC, d, f)
    raise FileNotFoundError(prefix)

# mode: fill (16:9 kesib to'ldirish), eustrip (Euronews vertikal videoning yuqori 16:9 qismi),
# vert (vertikal video, xira fon bilan), crop=(x,y,w,h) piksel
CROPS = {
    "presstv": (115, 0, 1050, 590),
    "awani":   (93, 0, 662, 372),
    "telesur": (119, 0, 610, 343),
    "cgtn":    (282, 48, 566, 318),
    "qn":      (110, 0, 628, 353),
}

# (manba, boshlanish soniyasi, nominal davomiylik, rejim)
HOOK = [
    ("hormuz/PressTV", 58.3, 1.5, "presstv"), ("hormuz/AlJazeera", 22, 1.3, "vert"),
    ("polsha/CNNTurk", 143, 1.8, "fill"), ("polsha/CNNTurk", 1, 1.7, "fill"),
    ("isroil/CGTN", 218, 1.6, "cgtn"), ("isroil/CGTN", 220, 1.6, "cgtn"),
    ("braziliya/ElMundo", 1.0, 2.2, "fill"), ("braziliya/BBC_p0pk2756", 1.5, 2.3, "fill"),
]
GREET = [
    ("italiya/TheStar", 9.6, 2.4, "fill"), ("korea/Euronews", 37.0, 2.3, "eustrip"),
    ("nvidia/Euronews", 15.0, 2.2, "fill"), ("kanada/Euronews", 0.5, 2.2, "fill"),
    ("hormuz/AWANI", 36, 2.3, "awani"),
]
SECTIONS = [
    # (asl ovozdagi boshlanish, tugash, kadrlar)
    (26.16, 85.40, [
        ("hormuz/AlJazeera", 8, 5.5, "vert"), ("hormuz/PressTV", 13, 6, "presstv"),
        ("hormuz/IRNA", 6, 7, "fill"), ("hormuz/PressTV", 29, 6, "presstv"),
        ("hormuz/AWANI", 19.5, 5, "awani"), ("hormuz/Euronews", 16, 6, "eustrip"),
        ("hormuz/Euronews", 33.5, 6, "eustrip"), ("hormuz/Euronews", 49.5, 6, "eustrip"),
        ("braziliya/BBC_p0pk5yct", 50.8, 4, "fill"), ("hormuz/PressTV", 57, 4, "presstv"),
        ("hormuz/AWANI", 50, 7, "awani"),
    ]),
    (85.40, 127.76, [
        ("polsha/CNNTurk", 2, 5, "fill"), ("polsha/CNNTurk", 24, 5, "fill"),
        ("polsha/CNNTurk", 84, 4, "fill"), ("polsha/CNNTurk", 142, 6, "fill"),
        ("polsha/CNNTurk", 168, 5, "fill"), ("polsha/Sozcu", 2, 8, "fill"),
        ("polsha/CNNTurk", 222, 5, "fill"), ("polsha/CNNTurk", 121, 4.4, "fill"),
    ]),
    (127.76, 163.24, [
        ("isroil/CGTN", 41, 5, "cgtn"), ("isroil/CGTN", 110, 4, "cgtn"),
        ("isroil/CGTN", 136, 5, "cgtn"), ("isroil/CGTN", 216, 4, "cgtn"),
        ("isroil/CGTN", 172, 4, "cgtn"), ("isroil/CGTN", 197, 4, "cgtn"),
        ("isroil/CGTN", 218, 6, "cgtn"), ("isroil/CGTN", 244, 4, "cgtn"),
    ]),
    (163.24, 200.44, [
        ("braziliya/BBC_p0pk5yct", 69.5, 4.5, "fill"), ("braziliya/BBC_p0pk5yct", 12, 3.5, "fill"),
        ("braziliya/BBC_p0pk5yct", 15.8, 3, "fill"), ("braziliya/BBC_p0pk5yct", 36, 4, "fill"),
        ("braziliya/BBC_p0pk5yct", 0, 3, "fill"), ("braziliya/ElMundo", 0, 6, "fill"),
        ("braziliya/Pagina12", 0, 4, "fill"), ("braziliya/BBC_p0pk2756", 0, 8, "fill"),
        ("braziliya/BBC_p0pk5yct", 46.8, 3, "fill"),
    ]),
    (200.44, 225.90, [
        ("ukraina/Euronews", 49, 5, "eustrip"), ("ukraina/Euronews", 59.5, 5, "eustrip"),
        ("ukraina/QN", 8, 4, "qn"), ("ukraina/Euronews", 0, 4, "eustrip"),
        ("ukraina/Euronews", 28, 4, "eustrip"), ("ukraina/Euronews", 52, 4, "eustrip"),
    ]),
    (225.90, 238.70, [
        ("aqsh/teleSUR", 12, 3, "telesur"), ("aqsh/teleSUR", 33, 3, "telesur"),
        ("aqsh/NYPost", 17, 4, "vert"), ("aqsh/NYPost", 30.6, 2.8, "vert"),
    ]),
    (238.70, 248.30, [
        ("kanada/Euronews", 0.5, 3, "fill"), ("kanada/Euronews", 7, 3, "fill"),
        ("kanada/Euronews", 30, 3.6, "fill"),
    ]),
    (248.30, 256.30, [
        ("italiya/TheStar", 0.5, 2.5, "fill"), ("italiya/Euronews", 33, 3, "eustrip"),
        ("italiya/TheStar", 38.5, 2.5, "fill"),
    ]),
    (256.30, 263.50, [
        ("dizel/Euronews", 18, 2.5, "fill"), ("dizel/Euronews", 22, 2.5, "fill"),
        ("dizel/Euronews", 36, 2.2, "fill"),
    ]),
    (263.50, 272.20, [
        ("korea/Euronews", 34.5, 3.4, "eustrip"), ("korea/Euronews", 40.5, 2.6, "eustrip"),
        ("korea/Euronews", 48, 2.7, "eustrip"),
    ]),
    (272.20, 282.80, [
        ("nvidia/Euronews", 8, 3, "fill"), ("nvidia/Euronews", 24, 3, "fill"),
        ("nvidia/Euronews", 60, 2, "fill"), ("nvidia/Euronews", 134, 2.6, "fill"),
    ]),
    (282.80, 293.70, [
        ("uzbekiston/Hurriyet", 25, 4, "fill"), ("uzbekiston/Hurriyet", 52, 3, "fill"),
        ("uzbekiston/Hurriyet", 131, 3.9, "fill"),
    ]),
    (293.70, 304.70, [
        ("stewart/BangShowbiz", 36, 4, "fill"), ("stewart/BangShowbiz", 61, 3.5, "fill"),
        ("stewart/BangShowbiz", 68.5, 3.5, "fill"),
    ]),
    (304.70, 316.43, [
        ("italiya/TheStar", 62.5, 4, "fill"), ("hormuz/Euronews", 0.5, 3.8, "eustrip"),
        ("kanada/Euronews", 48, 3.93, "fill"),
    ]),
]

HOOK_A = (12.64, 26.16)
GREET_A = (0.0, 11.24)
GAP1, GAP2 = 0.30, 0.20


def vf_for(mode, label):
    if mode == "fill":
        v = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
    elif mode == "eustrip":
        v = f"crop=360:202:0:0,scale={W}:{H}:flags=lanczos,unsharp=5:5:0.6"
    elif mode == "vert":
        return (f"split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                f"boxblur=25:5,eq=brightness=-0.12[bg];[b]scale=-2:{H}[fg];[bg][fg]overlay=(W-w)/2:0,"
                + label_filter(label))
    else:
        x, y, w, h = CROPS[mode]
        v = f"crop={w}:{h}:{x}:{y},scale={W}:{H}:flags=lanczos"
    return v + "," + label_filter(label)


def label_filter(label):
    t = ("Manba\\: " + label).replace("'", "")
    return (f"fps={FPS},setsar=1,drawtext=fontfile={FONT}:text='{t}':fontsize=19:"
            f"fontcolor=white@0.9:shadowcolor=black@0.8:shadowx=1:shadowy=1:"
            f"box=1:boxcolor=black@0.35:boxborderw=6:x=26:y=h-th-28")


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", p]).strip())


def fit(clips, total):
    s = sum(c[2] for c in clips)
    k = total / s
    out, acc = [], 0.0
    for i, c in enumerate(clips):
        d = round(c[2] * k, 3) if i < len(clips) - 1 else round(total - acc, 3)
        acc += d
        out.append((c[0], c[1], d, c[3]))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    plan = []
    hook_len = HOOK_A[1] - HOOK_A[0] + GAP1
    greet_len = GREET_A[1] - GREET_A[0] + GAP2
    plan += fit(HOOK, hook_len)
    plan += fit(GREET, greet_len)
    for a, b, clips in SECTIONS:
        plan += fit(clips, b - a)

    segs = []
    for i, (src, ss, d, mode) in enumerate(plan):
        path = find(src)
        name = os.path.basename(path).split("_")[0]
        label = LABELS[name]
        avail = dur(path) - ss - 0.1
        if d > avail:
            print(f"!! {src} @{ss}: {d:.2f}s kerak, {avail:.2f}s bor — sekinlashtiriladi", file=sys.stderr)
        seg = os.path.join(OUT, f"s{i:03d}.mp4")
        speed = min(1.0, max(avail, 0.5) / d)
        vf = vf_for(mode, label)
        if speed < 1.0:
            vf = f"setpts=PTS/{speed:.4f}," + vf
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-i", path, "-t", f"{d:.3f}",
               "-filter_complex" if mode == "vert" else "-vf", vf, "-an",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", seg]
        subprocess.run(cmd, check=True)
        segs.append(seg)
        print(f"{i:03d} {d:6.2f}s {src} @{ss} [{mode}]")

    with open(os.path.join(OUT, "list.txt"), "w") as f:
        for s in segs:
            f.write(f"file '{s}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i",
                    os.path.join(OUT, "list.txt"), "-c", "copy", os.path.join(OUT, "video_only.mp4")], check=True)

    # ovoz: hook -> pauza -> salom -> pauza -> asosiy
    af = (f"[0]atrim={HOOK_A[0]}:{HOOK_A[1]},asetpts=N/SR/TB,apad=pad_dur={GAP1}[h];"
          f"[0]atrim={GREET_A[0]}:{GREET_A[1]},asetpts=N/SR/TB,apad=pad_dur={GAP2}[g];"
          f"[0]atrim=start=26.16,asetpts=N/SR/TB[m];"
          f"[h][g][m]concat=n=3:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    final = os.path.join(ROOT, "kun_dayjesti_2026-10-31.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VOICE, "-i", os.path.join(OUT, "video_only.mp4"),
                    "-filter_complex", af, "-map", "1:v", "-map", "[a]", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", final],
                   check=True)
    print("TAYYOR:", final)


if __name__ == "__main__":
    main()
