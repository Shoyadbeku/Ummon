"""Build a Kdenlive/MLT project that cuts the 5 talking clips to the narration's pauses, then render it with melt.

Usage: python montage/kdenlive_build.py NARRATION.mp3 OUT.mp4
Writes montage/hikoya.mlt (the editable project) next to the render.
"""
import os, re, subprocess, sys

audio, out = sys.argv[1:3]
FPS, X, LEAD, TAIL = 24, 15, 0.5, 1.5        # crossfade frames, narration lead-in, tail after narration (s)
# Scene cuts sit in the middle of narration pauses (ffmpeg silencedetect, -35 dB, 0.35 s).
cuts = [7.56, 16.23, 27.29, 36.76]
end = 45.24
f = lambda s: round(s * FPS)

wav = "montage/ovoz_norm.wav"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", audio, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                "-ar", "48000", "-ac", "2", wav], check=True)

bounds = [0] + [f(c + LEAD) for c in cuts] + [f(end + LEAD + TAIL)]
total = bounds[-1]
args = ["melt", "-profile", "montage/vertical_1080x1920_24.profile"]
for i in range(5):
    # Each clip spills half a crossfade into its neighbours (the first/last keep the outer edge).
    a = bounds[i] - (X // 2 if i else 0)
    b = bounds[i + 1] + (X - X // 2 if i < 4 else 0)
    n = b - a
    speed = min(1.0, 239 / n)  # scenes longer than the 10 s clip are slowed slightly, never frozen
    src = f"videos/{i + 1:02d}.mp4"
    res = src if speed == 1.0 else f"timewarp:{speed:.4f}:{src}"
    args += [res, "in=0", f"out={n - 1}", "audio_index=-1",
             "-attach", "crop", "left=6", "right=6"]  # 480x832 -> 9:16, no letterbox
    if i:
        args += ["-mix", str(X), "-mixer", "luma"]
fade = f"0=0;{f(0.8)}=1;{total - f(1.2)}=1;{total - 1}=0"
args += [
    "-filter", "avfilter.unsharp", "av.luma_msize_x=5", "av.luma_msize_y=5", "av.luma_amount=0.6",
    "-filter", "avfilter.eq", "av.contrast=1.06", "av.saturation=1.08", "av.gamma=0.98",
    "-filter", "avfilter.colorbalance", "av.rs=0.03", "av.bs=-0.03", "av.rh=0.02", "av.bh=-0.02",
    "-filter", "avfilter.vignette", "av.angle=0.628",
    "-filter", "avfilter.noise", "av.alls=5", "av.allf=t",
    "-filter", "brightness", "in=0", f"out={total - 1}", f"level={fade}", "alpha=1",
    "-audio-track", "-blank", str(f(LEAD) - 1), wav,
    "-transition", "mix", "a_track=0", "b_track=1", "always_active=1", "sum=1",
]
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
subprocess.run(args + ["-consumer", "xml:montage/hikoya.mlt"], check=True)
# Make the project portable: drop the absolute root so paths resolve from montage/.
mlt = open("montage/hikoya.mlt").read()
mlt = re.sub(r' root="[^"]*"', "", mlt).replace("videos/", "../videos/").replace("montage/ovoz_norm.wav", "ovoz_norm.wav")
open("montage/hikoya.mlt", "w").write(mlt)
subprocess.run(["melt", "montage/hikoya.mlt", "-consumer", f"avformat:{out}", "vcodec=libx264", "preset=slow",
                "crf=18", "vprofile=high", "pix_fmt=yuv420p", "acodec=aac", "ab=192k", "ar=48000",
                "movflags=+faststart", "real_time=-4", f"out={total - 1}"], check=True)
print("frames", total, "seconds", total / FPS)
