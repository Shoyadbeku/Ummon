"""Kliplarni bitta videoga yig'ish (torch talab qilmaydi)."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRAMES_DIR = ROOT / "frames"
OUT_DIR = ROOT / "wan22" / "clips"
FPS = 24


def concat(clips, dest, fade=0.5):
    """Kliplarni ffmpeg xfade bilan bitta 1080x1920 videoga yig'adi."""
    durs = [float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(c)]
    )) for c in clips]
    cmd = ["ffmpeg", "-y"]
    for c in clips:
        cmd += ["-i", str(c)]
    fc = "".join(f"[{i}:v]scale=1080:1920,fps={FPS},setsar=1[v{i}];" for i in range(len(clips)))
    prev, offset = "v0", 0.0
    for i in range(1, len(clips)):
        offset += durs[i - 1] - fade
        fc += f"[{prev}][v{i}]xfade=transition=fade:duration={fade}:offset={offset:.3f}[x{i}];"
        prev = f"x{i}"
    total = offset + durs[-1]
    fc += f"[{prev}]fade=t=in:d=0.5,fade=t=out:st={total - 1:.3f}:d=1[out]"
    cmd += ["-filter_complex", fc, "-map", "[out]", "-c:v", "libx264", "-crf", "18",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(dest)]
    subprocess.run(cmd, check=True)
    print(f"final -> {dest}")
