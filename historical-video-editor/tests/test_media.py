"""FFmpeg-based tests (skipped automatically if ffmpeg is missing)."""
import shutil
import subprocess

import pytest

pytestmark = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


def test_beat_detection(tmp_path):
    from audio_editor import detect_beats
    f = tmp_path / "click.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                    "aevalsrc='sin(2*PI*60*t)*exp(-30*mod(t,0.5))':s=22050:d=20", f], check=True)
    r = detect_beats(f)
    assert 110 <= r["bpm"] <= 130 or 55 <= r["bpm"] <= 65


def test_dhash_and_cuts(tmp_path):
    from download_media import detect_cuts, dhash_image, hamming
    from PIL import Image
    a = tmp_path / "a.png"
    Image.new("RGB", (200, 100), (200, 10, 10)).save(a)
    assert hamming(dhash_image(a), dhash_image(a)) == 0
    v = tmp_path / "v.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=red:s=320x180:d=2", "-f", "lavfi", "-i",
                    "color=c=blue:s=320x180:d=2", "-filter_complex", "[0][1]concat=n=2:v=1", "-pix_fmt", "yuv420p", v], check=True)
    cuts = detect_cuts(v)
    assert any(1.8 <= c <= 2.2 for c in cuts)


def test_render_ken_burns_segment(tmp_path, cfg):
    from PIL import Image
    from video_editor import render_clip
    cfg["render"].update(width=320, height=180, fps=25)
    img = tmp_path / "p.jpg"
    Image.new("RGB", (900, 1200), (120, 90, 40)).save(img)
    pdir = tmp_path / "proj"
    (pdir / "render" / "segments").mkdir(parents=True)
    clip = {"id": "c0001", "kind": "image", "path": str(img), "width": 900, "height": 1200, "duration": 2.0,
            "effect": {"type": "parallax"}, "transition_in": {"type": "impact", "duration": 0.12}}
    out = render_clip(clip, None, 0.0, cfg, pdir, preview=True)
    from common import media_info
    info = media_info(out)
    assert info["width"] == 320 and abs(info["duration"] - 2.0) < 0.1
