"""Build a Kdenlive project that cuts the 4 talking clips to the narration into one graded, moving film,
then render it with melt.

Usage: python montage/kdenlive4k_build.py SRC_DIR WIDTH HEIGHT OUT.mp4
SRC_DIR holds 01.mp4..04.mp4, already 9:16 (the Real-ESRGAN 4K clips in CI, small test clips locally).
The narration is montage/ovoz.mp3; it is loudness-normalised to montage/ovoz_norm.wav.
Writes montage/montaj_4k.kdenlive (the editable project) plus its assets in montage/assets4k/.
"""
import os, subprocess, sys
import numpy as np

src, W, H, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
FPS, L, X = 24, 240, 20                 # clip length, mix length (frames)
LEAD, TAIL = 0.5, 1.0                   # picture before the narration starts / after it ends (s)
N = 4
# Scene cuts sit in the middle of narration pauses (ffmpeg silencedetect, -35 dB, 0.35 s), chosen by meaning:
# trends and shopping | corporations sell fear | "your every choice of clothes" | "when will you admit it?"
cuts, end = [10.69, 26.31, 36.47], 46.92
frames = lambda sec: round(sec * FPS)
bounds = [0] + [frames(c + LEAD) for c in cuts] + [frames(end + LEAD + TAIL)]
total = bounds[-1]
# Each scene spills half a mix into its neighbours; scenes longer than the clip are slowed (Kdenlive speed).
starts = [bounds[i] - (X // 2 if i else 0) for i in range(N)]
lens = [bounds[i + 1] + (X - X // 2 if i < N - 1 else 0) - starts[i] for i in range(N)]
speeds = [min(1.0, (L - 1) / n) for n in lens]
A = "montage/assets4k"
os.makedirs(A, exist_ok=True)
R = lambda path: os.path.relpath(path, "montage")  # project paths are relative to montage/


def ffmpeg_raw(frames, w, h, fmt, args):
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", fmt, "-s", f"{w}x{h}",
                          "-r", str(FPS), "-i", "-", *args], stdin=subprocess.PIPE)
    for fr in frames:
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    assert p.wait() == 0


# --- Film LUT: soft S-curve, lifted blacks, teal shadows / warm highlights, slightly muted colour.
n = 33
g = np.linspace(0, 1, n)
b_, g_, r_ = np.meshgrid(g, g, g, indexing="ij")          # .cube order: red changes fastest
rgb = np.stack([r_, g_, b_], -1).reshape(-1, 3)
y = rgb @ np.array([0.2126, 0.7152, 0.0722])
rgb = y[:, None] + (rgb - y[:, None]) * 0.92                # mute saturation a touch
s = 0.5 + (rgb - 0.5) * 1.12                                # contrast around mid grey
rgb = np.where(rgb < 0.5, rgb + (s - rgb) * 0.8, rgb + (s - rgb) * 0.6)
rgb = 0.035 + rgb * (0.955 - 0.035)                         # lifted blacks, rolled-off whites
sh, hi = (1 - y) ** 2, y ** 2
rgb += sh[:, None] * np.array([-0.025, 0.004, 0.03]) + hi[:, None] * np.array([0.03, 0.01, -0.03])
rgb = np.clip(rgb, 0, 1)
with open(f"{A}/film_look.cube", "w") as f:
    f.write('TITLE "Ummon film look"\nLUT_3D_SIZE 33\n')
    f.writelines(f"{c[0]:.6f} {c[1]:.6f} {c[2]:.6f}\n" for c in rgb)

# --- Wipe maps for the luma mixes (16-bit PGM, as Kdenlive's own lumas).
lw, lh = 540, 960
yy, xx = np.mgrid[0:lh, 0:lw]
iris = np.hypot((xx - lw / 2) / lw, (yy - lh * 0.45) / lw)
diag = (xx / lw + yy / lh) / 2
for name, m in (("iris", iris), ("diagonal", diag)):
    m = ((m - m.min()) / (m.max() - m.min()) * 65535).astype(">u2")
    with open(f"{A}/{name}.pgm", "wb") as f:
        f.write(f"P5\n{lw} {lh}\n65535\n".encode() + m.tobytes())

# --- Layer 1: warm light leak drifting across (RGBA, low opacity, rendered small and scaled up by MLT).
def leaks():
    for t in range(total):
        p = t / total
        cx, cy = lw * (1.1 - 0.9 * p), lh * (0.15 + 0.25 * np.sin(p * np.pi))
        d = np.hypot(xx - cx, yy - cy) / lw
        d2 = np.hypot(xx - lw * (0.1 + 0.3 * p), yy - lh * 0.85) / lw
        a = 0.20 * np.exp(-(d / 0.45) ** 2) * (0.75 + 0.25 * np.sin(t / 19)) + 0.08 * np.exp(-(d2 / 0.3) ** 2)
        fr = np.empty((lh, lw, 4), np.uint8)
        fr[..., 0], fr[..., 1], fr[..., 2] = 255, 168, 80
        fr[..., 3] = np.clip(a * 255, 0, 255)
        yield fr
ffmpeg_raw(leaks(), lw, lh, "rgba", ["-c:v", "qtrle", f"{A}/light_leak.mov"])

# --- Layer 2: thin cinema bars.
bar = round(H * 0.045)
img = np.zeros((H, W, 4), np.uint8)
img[:bar, :, 3] = img[-bar:, :, 3] = 255
ffmpeg_raw([img], W, H, "rgba", ["-frames:v", "1", f"{A}/cinema_bars.png"])

# --- Per-clip grade (matches the scenes to each other) and camera-like moves.
eq = [  # contrast, brightness, saturation, gamma
    (1.05, 0.00, 1.02, 1.00),   # 01 lamp-lit street: already bright
    (1.06, 0.02, 1.04, 1.04),   # 02 dim smoky office: lift a little
    (1.06, -0.02, 1.00, 0.98),  # 03 glowing shop window: hold the highlights
    (1.06, 0.02, 1.03, 1.03),   # 04 dark close-up under the lamp
]
def rect(z, fx, fy, dx=0.0):
    """Zoom z centred on (fx, fy) of the frame, shifted by dx frame widths."""
    w, h = W * z, H * z
    return f"{(-(w - W) * fx + dx * W):.1f} {(-(h - H) * fy):.1f} {w:.1f} {h:.1f} 1"
moves = [  # (rect at start, rect at end, rotation start, rotation end)
    (rect(1.02, .50, .70), rect(1.15, .50, .70), 0, 0),          # slow push-in on the rabbit and the fox
    (rect(1.16, 0, .45), rect(1.16, 1, .45), -1.2, 0.8),         # pan from the chess table to the fox, slight roll
    (rect(1.03, .65, .40), rect(1.18, .65, .40), 0, 0),          # push-in on the rabbit's longing face
    (rect(1.20, .50, .40), rect(1.03, .50, .40), -1.0, 0),       # pull-out from the fox's eyes, roll settles
]
lumas = [None, R(f"{A}/iris.pgm"), R(f"{A}/diagonal.pgm")]


def tc(fr):
    s = fr / FPS
    return f"{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{s % 60:06.3f}"


def props(d, ind):
    return "".join(f'{ind}<property name="{k}">{v}</property>\n' for k, v in d.items())


def filt(fid, service, d, kid=None, ind="   ", extra=""):
    d = {"mlt_service": service, "kdenlive_id": kid or service, **d}
    return f'{ind}<filter id="{fid}"{extra}>\n{props(d, ind + " ")}{ind}</filter>\n'


x = ['<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<mlt LC_NUMERIC="C" producer="main_bin" version="7.22.0">\n',
     f' <profile description="Vertical 4K UHD 24 fps" width="{W}" height="{H}" progressive="1" '
     'sample_aspect_num="1" sample_aspect_den="1" display_aspect_num="9" display_aspect_den="16" '
     'frame_rate_num="24" frame_rate_den="1" colorspace="709"/>\n']
bin_ids = {}
def producer(pid, kid, res, name, length, extra=None):
    bin_ids[pid] = kid
    d = {"length": length, "eof": "pause", "resource": res, "mlt_service": "avformat-novalidate",
         "kdenlive:clipname": name, "kdenlive:folderid": -1, "kdenlive:id": kid, "audio_index": -1,
         "seekable": 1, **(extra or {})}
    x.append(f' <producer id="{pid}" in="{tc(0)}" out="{tc(length - 1)}">\n{props(d, "  ")} </producer>\n')
for i in range(N):
    producer(f"clip{i + 1}", i + 2, R(f"{src}/{i + 1:02d}.mp4"), f"Sahna {i + 1:02d}", L, {"kdenlive:clip_type": 1})
wav = "montage/ovoz_norm.wav"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", "montage/ovoz.mp3", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                "-ar", "48000", "-ac", "2", wav], check=True)
alen = frames(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav],
                              capture_output=True, text=True, check=True).stdout))
producer("voice", 8, R(wav), "Ovoz", alen, {"audio_index": 0, "video_index": -1})
producer("leak", 6, R(f"{A}/light_leak.mov"), "Light leak", total, {"kdenlive:clip_type": 1})
producer("bars", 7, R(f"{A}/cinema_bars.png"), "Cinema bars", total,
         {"mlt_service": "qimage", "ttl": 25, "kdenlive:clip_type": 5, "eof": "pause"})

doc = {"activeTrack": 2, "audioChannels": 2, "audioTarget": -1, "compositing": 1, "documentid": 1760889600000,
       "enableTimelineZone": 0, "enableproxy": 0, "generateproxy": 0, "kdenliveversion": "26.08.0",
       "position": 0, "version": "1.04", "videoTarget": 2, "zonein": 0, "zoneout": total, "zoom": 8}
x.append(' <playlist id="main_bin">\n' + props({f"kdenlive:docproperties.{k}": v for k, v in doc.items()}, "  ")
         + '  <property name="xml_retain">1</property>\n'
         + "".join(f'  <entry producer="{p}" in="{tc(0)}" out="{tc({"voice": alen}.get(p, L if p.startswith("clip") else total) - 1)}"/>\n'
                   for p in bin_ids) + " </playlist>\n")
# Slowed scenes play through timewarp producers, as Kdenlive writes its clip speed changes.
for i in range(N):
    if speeds[i] < 1:
        res = R(f"{src}/{i + 1:02d}.mp4")
        d = {"length": lens[i], "eof": "pause", "resource": f"{speeds[i]:.6f}:{res}", "mlt_service": "timewarp",
             "warp_speed": f"{speeds[i]:.6f}", "warp_resource": res, "warp_pitch": 0, "audio_index": -1,
             "seekable": 1, "kdenlive:id": i + 2, "kdenlive:clipname": f"Sahna {i + 1:02d}"}
        x.append(f' <producer id="clip{i + 1}_tw" in="{tc(0)}" out="{tc(lens[i] - 1)}">\n{props(d, "  ")} </producer>\n')
x.append(f' <producer id="black_track" in="{tc(0)}" out="{tc(total - 1)}">\n'
         + props({"length": 2147483647, "eof": "continue", "resource": "black", "aspect_ratio": 1,
                  "mlt_service": "color", "mlt_image_format": "rgba", "set.test_audio": 0}, "  ") + " </producer>\n")

fid = iter(range(1000))
def track(tid, pls, body="", audio=False, name=""):
    tracks = "".join(f'  <track hide="{"video" if audio else "audio"}" producer="{p}"/>\n' for p in pls)
    meta = {"kdenlive:track_name": name, "kdenlive:trackheight": 67, "kdenlive:timeline_active": 1,
            "kdenlive:collapsed": 0, **({"kdenlive:audio_track": 1} if audio else {})}
    x.append(f' <tractor id="{tid}" in="{tc(0)}" out="{tc(total - 1)}">\n{props(meta, "  ")}{tracks}{body} </tractor>\n')

# A1 carries the narration after the lead-in; A2 stays empty.
for a in range(2):
    for k in range(2):
        body = ""
        if a == 1 and k == 0:
            body = (f'  <blank length="{tc(frames(LEAD))}"/>\n  <entry producer="voice" in="{tc(0)}" out="{tc(alen - 1)}">\n'
                    '   <property name="kdenlive:id">8</property>\n  </entry>\n')
        x.append(f' <playlist id="a{a}p{k}">\n  <property name="kdenlive:audio_track">1</property>\n{body} </playlist>\n')
    track(f"audio{a}", [f"a{a}p0", f"a{a}p1"], audio=True, name=f"A{2 - a}")

# V1: the four scenes, alternating between the track's two playlists so neighbours overlap for the mixes.
def entry(i):
    (r0, r1, a0, a1), e = moves[i], lens[i] - 1
    c, b, s, gm = eq[i]
    f = filt(f"f{next(fid)}", "qtblend", {"rect": f"0~={r0};{e}~={r1}", "rotation": f"0~={a0};{e}~={a1}",
                                          "compositing": 0, "distort": 0, "rotate_center": 1}, ind="   ")
    f += filt(f"f{next(fid)}", "avfilter.eq", {"av.contrast": c, "av.brightness": b, "av.saturation": s,
                                              "av.gamma": gm}, ind="   ")
    if i == 0:
        f += filt(f"f{next(fid)}", "brightness", {"level": "0=0;30=1", "alpha": 1}, "fade_from_black",
                  extra=f' in="{tc(0)}" out="{tc(30)}"')
    if i == N - 1:
        f += filt(f"f{next(fid)}", "brightness", {"level": "0=1;35=0", "alpha": 1}, "fade_to_black",
                  extra=f' in="{tc(e - 35)}" out="{tc(e)}"')
    return (f'  <entry producer="clip{i + 1}{"_tw" if speeds[i] < 1 else ""}" in="{tc(0)}" out="{tc(e)}">\n'
            f'   <property name="kdenlive:id">{i + 2}</property>\n{f}  </entry>\n')
for k in range(2):
    body, pos = "", 0
    for i in range(k, N, 2):
        if starts[i] > pos:
            body += f'  <blank length="{tc(starts[i] - pos)}"/>\n'
        body += entry(i)
        pos = starts[i] + lens[i]
    x.append(f' <playlist id="v1p{k}">\n{body} </playlist>\n')
mixes = ""
for j in range(1, N):
    a, b = starts[j], starts[j - 1] + lens[j - 1] - 1
    mixes += (f'  <transition id="mix{j}" in="{tc(a)}" out="{tc(b)}">\n'
              + props({"a_track": 0, "b_track": 1, "factory": "loader", "resource": lumas[j - 1] or "",
                       "mlt_service": "luma", "kdenlive_id": "luma", "kdenlive:mixcut": X // 2,
                       "reverse": 0 if j % 2 else 1, "softness": 0.25 if lumas[j - 1] else 0,
                       "alpha_over": 1, "invert": 0}, "   ") + "  </transition>\n")
grade = (filt(f"f{next(fid)}", "lift_gamma_gain", {"lift_r": 0.0, "lift_g": 0.005, "lift_b": 0.02,
                                                    "gamma_r": 1.02, "gamma_g": 1.0, "gamma_b": 0.98,
                                                    "gain_r": 1.03, "gain_g": 1.0, "gain_b": 0.96}, ind="  ")
         + filt(f"f{next(fid)}", "avfilter.lut3d", {"av.file": R(f"{A}/film_look.cube"), "av.interp": "tetrahedral"}, ind="  ")
         + filt(f"f{next(fid)}", "avfilter.unsharp", {"av.lx": 5, "av.ly": 5, "av.la": 0.5,
                                                     "av.cx": 5, "av.cy": 5, "av.ca": 0}, ind="  ")
         + filt(f"f{next(fid)}", "vignette", {"radius": 1.0, "smooth": 0.9, "opacity": 0.55, "mode": 1,
                                             "x": 0.5, "y": 0.5}, ind="  ")
         + filt(f"f{next(fid)}", "grain", {"noise": 12, "contrast": 100, "brightness": 100}, ind="  "))
track("v1", ["v1p0", "v1p1"], mixes + grade, name="V1 Sahnalar")

# V2: light leak layer, V3: cinema bars layer.
fade = lambda e: (filt(f"f{next(fid)}", "brightness", {"level": "0=0;30=1", "alpha": 1}, "fade_from_black",
                       extra=f' in="{tc(0)}" out="{tc(30)}"')
                  + filt(f"f{next(fid)}", "brightness", {"level": "0=1;35=0", "alpha": 1}, "fade_to_black",
                         extra=f' in="{tc(e - 35)}" out="{tc(e)}"'))
x.append(f' <playlist id="v2p0">\n  <entry producer="leak" in="{tc(0)}" out="{tc(total - 1)}">\n'
         f'   <property name="kdenlive:id">6</property>\n{fade(total - 1)}  </entry>\n </playlist>\n'
         ' <playlist id="v2p1"/>\n')
track("v2", ["v2p0", "v2p1"], name="V2 Light leak")
x.append(f' <playlist id="v3p0">\n  <entry producer="bars" in="{tc(0)}" out="{tc(total - 1)}">\n'
         '   <property name="kdenlive:id">7</property>\n  </entry>\n </playlist>\n <playlist id="v3p1"/>\n')
track("v3", ["v3p0", "v3p1"], name="V3 Cinema bars")

tracks = ["black_track", "audio0", "audio1", "v1", "v2", "v3"]
comp = ""
for k in range(1, len(tracks)):
    svc = "mix" if k < 3 else "qtblend"
    d = {"a_track": 0, "b_track": k, "mlt_service": svc, "kdenlive_id": svc, "internal_added": 237,
         "always_active": 1, **({"accepts_blanks": 1, "sum": 1} if svc == "mix" else {"compositing": 0})}
    comp += f'  <transition id="internal{k}">\n{props(d, "   ")}  </transition>\n'
x.append(f' <tractor id="maintractor" in="{tc(0)}" out="{tc(total - 1)}">\n'
         + "".join(f'  <track producer="{t}"/>\n' for t in tracks) + comp + " </tractor>\n</mlt>\n")

proj = "montage/montaj_4k.kdenlive"
open(proj, "w").write("".join(x))
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
# xvfb-run: the MLT Qt module (qtblend, qimage) needs an X server.
if os.environ.get("NORENDER"): sys.exit()
subprocess.run(["xvfb-run", "-a", os.environ.get("MELT", "melt"), R(proj), "-consumer", f"avformat:{os.path.abspath(out)}",
                "vcodec=libx264", "preset=slow", "crf=16", "vprofile=high", "pix_fmt=yuv420p", "acodec=aac", "ab=192k", "ar=48000",
                "movflags=+faststart", "real_time=-4", f"out={total - 1}"], check=True, cwd="montage")  # avfilter/luma paths resolve from here
print("frames", total, "seconds", total / FPS, "scene lengths", lens, "speeds", [round(v, 3) for v in speeds])
