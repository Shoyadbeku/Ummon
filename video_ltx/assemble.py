"""Cut LTX clips to the voice timeline and render the final 1080p video.

Usage: python assemble.py scenes.json clips_dir voice.wav out.mp4
Every scene is retimed so its first frame lands exactly on the sentence it illustrates.
"""
import json, os, subprocess, sys

scenes_path, clips, voice, out = sys.argv[1:5]
FPS = 24
W, H = 1920, 1080
seg_dir = os.path.join(os.path.dirname(out) or ".", "segs")
os.makedirs(seg_dir, exist_ok=True)
FONT_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Chapter cards: start second -> (title, subtitle)
CHAPTERS = {
    0.0:   ("4000 yil oldin ham", "odamlar kredit olganmi?"),
    88.1:  ("MESOPOTAMIYA", "Miloddan avvalgi III ming yillik"),
    219.3: ("BOBIL", "Miloddan avvalgi XVIII asr · Hammurapi"),
    409.3: ("AFINA", "Miloddan avvalgi VI asr · Solon"),
    499.3: ("BUYUK IPAK YO'LI", "O'rta asrlar · Markaziy Osiyo"),
    614.3: ("BUGUN", "Kredit — kelajakka ishonch tarixi"),
    669.3: ("Qarzsiz kelajak bo'ladimi?", "Fikringizni izohlarda yozing"),
}
FADE_IN = {0.0, 88.1, 219.3, 409.3, 499.3}


def esc(t):
    return t.replace("\\", "\\\\").replace("'", "’").replace(":", "\\:").replace(",", "\\,")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-2000:])


def probe_frames(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                        "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", p],
                       capture_output=True, text=True)
    return int(r.stdout.strip())


scenes = json.load(open(scenes_path))
listfile = os.path.join(seg_dir, "list.txt")
with open(listfile, "w") as lf:
    for s in scenes:
        f0, f1 = round(s["start"] * FPS), round(s["end"] * FPS)
        n = f1 - f0
        src = os.path.join(clips, f"{s['id']}.mp4")
        dst = os.path.join(seg_dir, f"{s['id']}.mp4")
        lf.write(f"file '{os.path.abspath(dst)}'\n")
        if os.path.exists(dst) and os.path.getmtime(dst) > os.path.getmtime(src):
            continue
        have = probe_frames(src)
        k = max(n / have, 1.0)  # slow-motion factor; never speed up, just trim
        vf = [f"setpts={k:.5f}*PTS"]
        if k > 1.01:
            vf.append(f"framerate=fps={FPS}:interp_start=0:interp_end=255:scene=100")
        vf += [
            f"tpad=stop_mode=clone:stop=-1",
            f"scale={W}:-2:flags=lanczos", f"crop={W}:{H}",
            "unsharp=5:5:0.6:5:5:0.0",
            "eq=contrast=1.06:saturation=1.08:gamma=0.98",
            "colorbalance=rs=0.03:bs=-0.03:rh=0.02:bh=-0.02",
            "vignette=PI/5",
            "noise=alls=2:allf=t",
        ]
        if s["start"] in FADE_IN:
            vf.append("fade=t=in:st=0:d=0.6")
        if s is scenes[-1]:
            vf.append(f"fade=t=out:st={n / FPS - 1.5:.3f}:d=1.5")
        if s["start"] in CHAPTERS:
            t1, t2 = CHAPTERS[s["start"]]
            a = "if(lt(t,0.4),0,if(lt(t,1.2),(t-0.4)/0.8,if(lt(t,{e}-1.0),1,if(lt(t,{e}),({e}-t)/1.0,0))))".format(
                e=min(n / FPS, 5.5))
            big = s["start"] in (0.0, 669.3)
            y1 = "(h/2)-90" if big else "h-250"
            y2 = "(h/2)+10" if big else "h-165"
            sz1, sz2 = (84, 46) if big else (64, 34)
            by, bh = ("ih/2-130", 230) if big else ("ih-275", 165)
            e = min(n / FPS, 5.5)
            vf.append(f"drawbox=x=0:y={by}:w=iw:h={bh}:color=black@0.42:t=fill:enable='between(t,0.4,{e:.2f})'")
            vf.append(f"drawtext=fontfile={FONT_SERIF}:text='{esc(t1)}':fontsize={sz1}:fontcolor=white:"
                      f"alpha='{a}':x=(w-text_w)/2:y={y1}:shadowcolor=black@0.7:shadowx=2:shadowy=2")
            vf.append(f"drawtext=fontfile={FONT_SANS}:text='{esc(t2)}':fontsize={sz2}:fontcolor=0xE8C878:"
                      f"alpha='{a}':x=(w-text_w)/2:y={y2}:shadowcolor=black@0.7:shadowx=2:shadowy=2")
        run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-vf", ",".join(vf), "-frames:v", str(n),
             "-r", str(FPS), "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
             "-pix_fmt", "yuv420p", dst])
        print("seg", s["id"], n, "frames", f"x{k:.2f}", flush=True)

run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", listfile, "-i", voice,
     "-map", "0:v", "-map", "1:a", "-c:v", "copy",
     "-af", "highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=10:release=200,loudnorm=I=-14:TP=-1.5:LRA=9",
     "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out])
print("wrote", out)
