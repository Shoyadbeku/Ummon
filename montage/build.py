"""Cut the 12 talking clips to the narration's pauses and grade them into one 1080x1920 film.

Usage: python montage/build.py NARRATION.mp3 OUT.mp4
"""
import subprocess, sys

audio, out = sys.argv[1:3]
X = 0.6  # crossfade length
# Scene cuts sit in the middle of the narration's pauses (ffmpeg silencedetect, -35 dB, 0.35 s).
cuts = [3.72, 9.47, 21.74, 28.99, 41.52, 48.95, 59.10, 61.79, 71.86, 85.32, 94.50]
end = 102.03
bounds = [0.0] + cuts + [end]
segs = [bounds[i + 1] - bounds[i] for i in range(12)]

grade = ("scale=1080:1920:flags=lanczos,unsharp=5:5:0.6,"
         "eq=contrast=1.06:saturation=1.08:gamma=0.98,"
         "colorbalance=rs=0.03:bs=-0.03:rh=0.02:bh=-0.02,"
         "vignette=PI/5,noise=alls=5:allf=t,format=yuv420p")
inputs, chains = [], []
for i, s in enumerate(segs):
    d = s + (X if i < 11 else 0) + (X / 2 if i == 0 else 0)
    inputs += ["-i", f"videos/{i + 1:02d}.mp4"]
    # Scenes longer than the 10 s clip are slowed slightly instead of frozen.
    stretch = max(1.0, d / 9.9)
    chains.append(f"[{i}:v]setpts={stretch:.4f}*PTS,fps=24,trim=duration={d:.3f},setpts=PTS-STARTPTS,{grade}[v{i}]")
    segs[i] = d

prev, t = "v0", segs[0] - X
for i in range(1, 12):
    chains.append(f"[{prev}][v{i}]xfade=transition=fade:duration={X}:offset={t:.3f}[x{i}]")
    prev, t = f"x{i}", t + segs[i] - X
total = t + X
chains.append(f"[{prev}]fade=t=in:st=0:d=0.8,fade=t=out:st={end + 0.7:.2f}:d=1.2,"
              f"tpad=stop_mode=clone:stop_duration=3,trim=duration={end + 1.9:.2f}[vout]")
chains.append(f"[12:a]adelay=300|300,loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st={end + 0.6:.2f}:d=1.2,"
              f"apad,atrim=duration={end + 1.9:.2f}[aout]")
subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-i", audio, "-filter_complex", ";".join(chains),
                "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-movflags", "+faststart", out], check=True)
print("visual length", round(total, 2))
