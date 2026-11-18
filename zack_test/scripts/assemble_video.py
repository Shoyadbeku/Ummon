"""Assemble renders/final/frame_%06d.png + narration + SFX into output/final_video.mp4.
Frames are rendered at 540x960 (approved 'fast' setting) and Lanczos-upscaled to 1080x1920."""
import os, subprocess, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FR = os.path.join(ROOT, "renders", "final")
OUT = os.path.join(ROOT, "output", "final_video.mp4")
N = 1049

missing = [f for f in range(1, N + 1) if not os.path.exists(os.path.join(FR, f"frame_{f:06d}.png"))]
if missing:
    sys.exit(f"missing {len(missing)} frames, first: {missing[:10]}")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

vf = ("scale=1080:1920:flags=lanczos,"
      "unsharp=5:5:0.6:5:5:0.0,"
      "eq=contrast=1.04:saturation=1.06,"
      "format=yuv420p")
af = ("[1:a]aformat=sample_rates=48000:channel_layouts=stereo,highpass=f=70,"
      "acompressor=threshold=-20dB:ratio=3:attack=5:release=120,loudnorm=I=-15:TP=-2:LRA=9,asplit=2[vo][sc];"
      "[2:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=-9dB[fx];"
      "[fx][sc]sidechaincompress=threshold=0.05:ratio=4:attack=10:release=250[fxd];"
      "[vo][fxd]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89[a]")
cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
       "-framerate", "24", "-i", os.path.join(FR, "frame_%06d.png"),
       "-i", os.path.join(ROOT, "audio", "narration.wav"),
       "-i", os.path.join(ROOT, "audio", "sfx.wav"),
       "-filter_complex", af, "-vf", vf,
       "-map", "0:v", "-map", "[a]",
       "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-r", "24",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
       "-movflags", "+faststart", "-shortest", OUT]
print(" ".join(cmd))
subprocess.run(cmd, check=True)
print("wrote", OUT, os.path.getsize(OUT) // 1024, "KB")
