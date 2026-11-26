#!/usr/bin/env python3
"""Offline self-test helper: generates SYNTHETIC media so the whole edit/render/
audio/export/QC chain can be tested without network or API keys.

Creates
  assets/music/demo_epic_drone.mp3       generated pad + percussion (90 bpm), CC0
  assets/sfx/{wind,impact,city_ambience,horses,page_turn}.wav   generated, CC0
  <project>/media/...                    synthetic "archive" clips (4:3 B/W, 16:9 colour),
                                         paintings/portrait/map stills
  <project>/media_index.json             registered as provider 'synthetic_test' (CC0)
  <project>/audio/narration.wav          speech-like placeholder (if no narration given)

Every synthetic asset is credited "Synthetic test asset" — never publish this output.

Usage: python scripts/make_demo_assets.py --project <slug> [--clips 10] [--images 8]
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import SKILL_ROOT, load_config, log, media_info, project_dir, read_json, run, setup_logging, sha1_file, write_json  # noqa: E402


def gen_audio(cfg: dict):
    music = SKILL_ROOT / cfg["paths"]["music_dir"]
    sfx = SKILL_ROOT / cfg["paths"]["sfx_dir"]
    music.mkdir(parents=True, exist_ok=True)
    sfx.mkdir(parents=True, exist_ok=True)
    m = music / "demo_epic_drone.mp3"
    if not m.exists():
        # 90 bpm: kick every 0.6667s, low pad chord D minor, slow swell
        expr = ("0.18*sin(2*PI*73.42*t)*(0.6+0.4*sin(2*PI*0.05*t))+0.12*sin(2*PI*110*t)+0.09*sin(2*PI*146.83*t)"
                "+0.06*sin(2*PI*174.61*t)*(0.5+0.5*sin(2*PI*0.11*t))"
                "+0.55*sin(2*PI*(55-25*mod(t,0.6667))*t)*exp(-14*mod(t,0.6667))")
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"aevalsrc='{expr}|{expr}':s=48000:d=90",
             "-af", "aecho=0.6:0.5:120|240:0.25|0.15,lowpass=f=5000,volume=0.8", m])
    specs = {
        "wind": "anoisesrc=color=brown:amplitude=0.5:d=20,lowpass=f=600,tremolo=f=0.15:d=0.6",
        "city_ambience": "anoisesrc=color=pink:amplitude=0.25:d=20,bandpass=f=900:width_type=o:w=2",
        "horses": "anoisesrc=color=brown:amplitude=0.6:d=12,lowpass=f=300,tremolo=f=6:d=0.9",
        "page_turn": "anoisesrc=color=white:amplitude=0.4:d=1.2,highpass=f=1500,afade=t=out:st=0.2:d=0.9",
    }
    for name, f in specs.items():
        out = sfx / f"{name}.mp3"
        if not out.exists():
            run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f, "-ac", "2", "-ar", "48000", out])
    imp = sfx / "impact.mp3"
    if not imp.exists():
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
             "aevalsrc='0.9*sin(2*PI*(70-50*t)*t)*exp(-3*t)+0.3*random(0)*exp(-25*t)':s=48000:d=2.5",
             "-ac", "2", "-af", "lowpass=f=2500,aecho=0.7:0.6:300:0.3", imp])


def gen_video(out: Path, kind: int, dur: float, rnd: random.Random):
    """Different procedural sources so perceptual hashes differ."""
    srcs = [
        ("life=s=640x480:mold=10:r=25:ratio=0.1:death_color=#202020:life_color=#d0d0d0", "4:3 bw"),
        ("mandelbrot=s=1280x720:r=25", "16:9 colour"),
        ("cellauto=s=640x480:rule=110:r=25", "4:3 bw"),
        ("testsrc2=s=1280x720:r=25", "16:9 colour"),
        ("gradients=s=1280x720:r=25:speed=0.02:n=4", "16:9 colour"),
        ("life=s=960x720:mold=25:r=25:ratio=0.3", "4:3 colour"),
    ]
    src, _ = srcs[kind % len(srcs)]
    hue = rnd.randint(0, 360)
    vf = f"hue=h={hue},noise=alls=12:allf=t,eq=contrast=1.1"
    if "bw" in srcs[kind % len(srcs)][1]:
        vf += ",hue=s=0,vignette"
    # cut in the middle to test shot detection
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"{src}", "-f", "lavfi", "-i", f"sine=f={200 + kind * 40}:d={dur}",
         "-t", str(dur), "-vf", vf, "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-shortest", out])


def gen_image(out: Path, kind: str, i: int, rnd: random.Random):
    from PIL import Image, ImageDraw, ImageFilter
    sizes = {"painting": (2400, 1600), "portrait": (1400, 2000), "map": (3000, 2000), "manuscript": (1800, 2400)}
    w, h = sizes[kind]
    base = [(170, 130, 80), (60, 80, 110), (120, 60, 40), (200, 180, 140)][i % 4]
    im = Image.new("RGB", (w, h), base)
    d = ImageDraw.Draw(im)
    for _ in range(60):
        x, y = rnd.randint(0, w), rnd.randint(0, h)
        r = rnd.randint(40, 380)
        c = tuple(max(0, min(255, v + rnd.randint(-70, 70))) for v in base)
        if kind == "map":
            d.line([(x, y), (x + rnd.randint(-600, 600), y + rnd.randint(-300, 300))], fill=(90, 60, 30), width=4)
        else:
            d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    if kind == "portrait":
        d.ellipse([w * 0.3, h * 0.15, w * 0.7, h * 0.48], fill=(225, 190, 160))
        d.rectangle([w * 0.2, h * 0.5, w * 0.8, h], fill=(80, 30, 30))
    if kind == "manuscript":
        for row in range(30):
            d.line([(w * 0.12, h * 0.1 + row * h * 0.026), (w * 0.88, h * 0.1 + row * h * 0.026)], fill=(40, 30, 20), width=6)
    im = im.filter(ImageFilter.GaussianBlur(3))
    im.save(out, "JPEG", quality=92)


def narration_placeholder(out: Path, dur: float):
    # speech-like: band-limited noise gated by a syllable rhythm with sentence pauses
    expr = "0.5*random(0)*(0.5+0.5*sin(2*PI*4.2*t))*gt(sin(2*PI*0.18*t)+0.65,0)"
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d={dur:.2f}",
         "-af", "bandpass=f=700:width_type=o:w=2.5,volume=4", "-ac", "2", out])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--clips", type=int, default=10)
    ap.add_argument("--images", type=int, default=8)
    ap.add_argument("--config")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    setup_logging(a.verbose)
    cfg = load_config(a.config)
    pdir = project_dir(cfg, a.project)
    sb = read_json(pdir / "storyboard.json")
    rnd = random.Random(42)
    gen_audio(cfg)
    scenes = [s["id"] for s in sb["scenes"]]
    assets = []
    lic = {"code": "cc0", "label": "CC0", "url": "https://creativecommons.org/publicdomain/zero/1.0/", "risk": 0,
           "commercial_ok": True, "modify_ok": True, "attribution_required": False, "share_alike": False}
    for i in range(a.clips):
        f = pdir / "media" / "video" / f"synth_v{i:02d}.mp4"
        if not f.exists():
            gen_video(f, i, rnd.choice([8, 12, 16]), rnd)
        info = media_info(f)
        from download_media import detect_cuts, dhash_video
        assets.append({"asset_id": f"synth_v{i:02d}", "candidate_id": f"synth_v{i:02d}", "scene_id": scenes[i % len(scenes)],
                       "media_type": "video", "path": str(f), "width": info["width"], "height": info["height"],
                       "fps": info["fps"], "duration": info["duration"], "has_audio": info["has_audio"], "src_in": 0.0,
                       "src_out": info["duration"], "cuts": detect_cuts(f), "phash": dhash_video(f, 1.0, f.parent),
                       "sha1": sha1_file(f),
                       "meta": {"provider": "synthetic_test", "title": f"Synthetic archive clip {i}", "page_url": f"local://synthetic/{f.name}",
                                "media_url": "", "author": "Historical Video Editor test generator", "license": lic,
                                "license_raw": "CC0", "source_label": "Synthetic test asset", "credit": "Source: Synthetic test asset, CC0",
                                "archival": True, "status": "approved", "verify_notes": [], "present_day": i % 5 == 4}})
    kinds = ["painting", "portrait", "map", "manuscript"]
    from download_media import dhash_image
    for i in range(a.images):
        k = kinds[i % len(kinds)]
        f = pdir / "media" / "image" / f"synth_i{i:02d}_{k}.jpg"
        if not f.exists():
            gen_image(f, k, i, rnd)
        from PIL import Image
        with Image.open(f) as im:
            w, h = im.size
        assets.append({"asset_id": f"synth_i{i:02d}", "candidate_id": f"synth_i{i:02d}", "scene_id": scenes[(i * 2 + 1) % len(scenes)],
                       "media_type": "image", "path": str(f), "width": w, "height": h, "duration": 0.0, "src_in": None,
                       "src_out": None, "phash": dhash_image(f), "sha1": sha1_file(f),
                       "meta": {"provider": "synthetic_test", "title": f"Synthetic {k} {i}" + (" map" if k == "map" else ""),
                                "page_url": f"local://synthetic/{f.name}", "media_url": "", "author": "test generator",
                                "license": lic, "license_raw": "CC0", "source_label": "Synthetic test asset",
                                "credit": "Source: Synthetic test asset, CC0", "archival": True, "status": "approved",
                                "verify_notes": []}})
    write_json(pdir / "media_index.json", {"assets": assets, "failed": [], "duplicates": [], "synthetic": True})
    if not sb.get("narration_audio"):
        nar = pdir / "audio" / "narration.wav"
        narration_placeholder(nar, sb["total_duration"])
        sb["narration_audio"] = str(nar)
        write_json(pdir / "storyboard.json", sb)
    log.info("synthetic assets: %d (project %s)", len(assets), pdir)


if __name__ == "__main__":
    main()
