#!/usr/bin/env python3
"""Step 10: download ONLY approved material (licence risk <= max_allowed_risk,
or explicit permission), validate it and build media_index.json.

Features
  * HTTP streaming download with size cap and content-type checks
  * yt-dlp for platform videos that are Creative-Commons or used with permission
  * long archive films: only excerpts are fetched (ffmpeg HTTP seeking) and the
    exact source time range is recorded for the credits report
  * ffprobe validation, resolution filter, broken-file detection
  * perceptual hash (dHash) duplicate detection across all scenes
  * scene-cut detection inside clips (clean shot boundaries for the editor)

Usage: python scripts/download_media.py --project <slug> [--per-scene-video 4] [--per-scene-image 3]
"""
from __future__ import annotations

import argparse
import math
import mimetypes
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (Http, load_config, log, media_info, project_dir, read_json, run, setup_logging,  # noqa: E402
                    sha1_file, write_json)

MAX_BYTES = 1_500_000_000
EXCERPT_SEC = 18.0
LONG_VIDEO_SEC = 150.0


# --------------------------------------------------------------------------
# perceptual hash
# --------------------------------------------------------------------------
def dhash_image(path: str | Path, size: int = 8) -> str:
    from PIL import Image

    with Image.open(path) as im:
        im = im.convert("L").resize((size + 1, size), Image.LANCZOS)
        px = list(im.get_flattened_data()) if hasattr(im, "get_flattened_data") else list(im.getdata())
    bits = 0
    for r in range(size):
        for c in range(size):
            bits = (bits << 1) | (px[r * (size + 1) + c] > px[r * (size + 1) + c + 1])
    return f"{bits:016x}"


def dhash_video(path: Path, at: float, tmpdir: Path) -> str:
    frame = tmpdir / (path.stem + "_ph.jpg")
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{at:.2f}", "-i", path, "-frames:v", "1", "-vf", "scale=160:-2", frame], check=False)
    if not frame.exists():
        return ""
    h = dhash_image(frame)
    frame.unlink(missing_ok=True)
    return h


def hamming(a: str, b: str) -> int:
    if not a or not b:
        return 64
    return bin(int(a, 16) ^ int(b, 16)).count("1")


# --------------------------------------------------------------------------
# scene cut detection
# --------------------------------------------------------------------------
def detect_cuts(path: Path, threshold: float = 0.32, max_sec: float = 600) -> list[float]:
    p = run(["ffmpeg", "-hide_banner", "-v", "info", "-t", str(max_sec), "-i", path, "-an", "-vf",
             f"scale=320:-2,select='gt(scene,{threshold})',showinfo", "-f", "null", "-"], check=False)
    cuts = []
    for line in p.stderr.splitlines():
        if "showinfo" in line and "pts_time:" in line:
            try:
                cuts.append(round(float(line.split("pts_time:")[1].split()[0]), 2))
            except (ValueError, IndexError):
                pass
    return cuts


def detect_black_or_static(path: Path, duration: float) -> dict:
    """Quick quality probe: share of black frames and frozen frames."""
    p = run(["ffmpeg", "-hide_banner", "-t", str(min(duration, 120)), "-i", path, "-an", "-vf",
             "scale=320:-2,blackdetect=d=0.5:pix_th=0.10,freezedetect=n=-60dB:d=2", "-f", "null", "-"], check=False)
    black = sum(float(l.split("black_duration:")[1].split()[0]) for l in p.stderr.splitlines() if "black_duration:" in l)
    frozen = sum(float(l.split("freeze_duration:")[1].split()[0]) for l in p.stderr.splitlines() if "freeze_duration:" in l)
    span = max(0.1, min(duration, 120))
    return {"black_ratio": round(black / span, 3), "frozen_ratio": round(frozen / span, 3)}


# --------------------------------------------------------------------------
# downloaders
# --------------------------------------------------------------------------
def http_download(http: Http, url: str, dest: Path) -> Path:
    r = http.request("GET", url, stream=True, allow_redirects=True, timeout=120)
    if r.status_code != 200:
        raise ConnectionError(f"HTTP {r.status_code}")
    ctype = r.headers.get("Content-Type", "").split(";")[0]
    if ctype.startswith("text/html"):
        raise ValueError("got HTML page instead of media")
    if not dest.suffix:
        dest = dest.with_suffix(mimetypes.guess_extension(ctype) or ".bin")
    size = 0
    tmp = dest.with_suffix(dest.suffix + ".part")
    with open(tmp, "wb") as f:
        for chunk in r.iter_content(1 << 16):
            size += len(chunk)
            if size > MAX_BYTES:
                raise ValueError("file too large")
            f.write(chunk)
    tmp.replace(dest)
    return dest


def ffmpeg_excerpt(url: str, start: float, dur: float, dest: Path, ua: str) -> Path:
    run(["ffmpeg", "-y", "-v", "error", "-user_agent", ua, "-ss", f"{start:.2f}", "-i", url, "-t", f"{dur:.2f}",
         "-map", "0:v:0", "-map", "0:a:0?", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", dest], timeout=900)
    return dest


def ytdlp_download(url: str, dest_stem: Path, max_h: int = 1080, sections: list[tuple[float, float]] | None = None) -> Path:
    exe = shutil.which("yt-dlp")
    if not exe:
        raise RuntimeError("yt-dlp not installed")
    cmd = [exe, "--no-warnings", "--no-playlist", "-f", f"bv*[height<={max_h}]+ba/b[height<={max_h}]/b",
           "--merge-output-format", "mp4", "-o", str(dest_stem) + ".%(ext)s", "--no-part"]
    for s, e in sections or []:
        cmd += ["--download-sections", f"*{s:.1f}-{e:.1f}", "--force-keyframes-at-cuts"]
    cmd.append(url)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip()[-300:])
    files = sorted(dest_stem.parent.glob(dest_stem.name + ".*"), key=lambda f: f.stat().st_size, reverse=True)
    if not files:
        raise RuntimeError("yt-dlp produced no file")
    return files[0]


def normalise_image(path: Path) -> Path:
    from PIL import Image, ImageOps

    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode not in ("RGB", "L"):
            bg = Image.new("RGB", im.size, (0, 0, 0))
            im = im.convert("RGBA")
            bg.paste(im, mask=im.split()[-1])
            im = bg
        im = im.convert("RGB")
        if max(im.size) > 6000:
            im.thumbnail((6000, 6000), Image.LANCZOS)
        out = path.with_suffix(".jpg")
        im.save(out, "JPEG", quality=94)
    if out != path:
        path.unlink(missing_ok=True)
    return out


# --------------------------------------------------------------------------
def excerpt_windows(duration: float, n: int = 3, length: float = EXCERPT_SEC) -> list[tuple[float, float]]:
    """Evenly spread windows avoiding the first/last 5% (titles, end cards)."""
    usable0, usable1 = duration * 0.06, duration * 0.94
    span = usable1 - usable0
    if span <= length:
        return [(usable0, min(duration, usable0 + length))]
    step = span / n
    return [(round(usable0 + step * i + (step - length) / 2, 2), round(usable0 + step * i + (step + length) / 2, 2))
            for i in range(n)]


def process(c: dict, pdir: Path, http: Http, cfg: dict) -> list[dict]:
    kind = c["media_type"]
    folder = pdir / "media" / kind
    stem = folder / c["id"]
    ua = cfg["http"]["user_agent"]
    assets = []
    if kind == "image":
        if c.get("download_method") == "ytdlp":
            raise ValueError("image via yt-dlp not supported")
        ext = Path(c["media_url"].split("?")[0]).suffix.lower()
        dest = http_download(http, c["media_url"], stem.with_suffix(ext if ext in (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".gif") else ""))
        dest = normalise_image(dest)
        from PIL import Image
        with Image.open(dest) as im:
            w, h = im.size
        assets.append({"path": str(dest), "width": w, "height": h, "duration": 0.0, "src_in": None, "src_out": None,
                       "phash": dhash_image(dest)})
        return assets

    # video
    dur = float(c.get("duration") or 0)
    if c.get("download_method") == "ytdlp":
        sections = excerpt_windows(dur) if dur > LONG_VIDEO_SEC else None
        if c.get("max_clip_sec"):
            sections = [(w[0], w[0] + c["max_clip_sec"]) for w in (excerpt_windows(dur, 1) if dur else [(0, 0)])]
        f = ytdlp_download(c["page_url"], stem, sections=sections)
        files = [(f, sections[0] if sections else (0.0, None))]
    else:
        url = c["media_url"]
        if not dur:
            try:
                dur = media_info(url)["duration"]
            except Exception:  # noqa: BLE001
                dur = 0
        if dur > LONG_VIDEO_SEC:
            files = []
            for i, (s, e) in enumerate(excerpt_windows(dur)):
                dest = folder / f"{c['id']}_x{i}.mp4"
                try:
                    files.append((ffmpeg_excerpt(url, s, e - s, dest, ua), (s, e)))
                except Exception as ex:  # noqa: BLE001
                    log.warning("excerpt %s failed: %s", dest.name, str(ex)[:150])
        else:
            ext = Path(url.split("?")[0]).suffix.lower() or ".mp4"
            files = [(http_download(http, url, stem.with_suffix(ext)), (0.0, None))]
    for f, (s, e) in files:
        info = media_info(f)
        if not info["has_video"] or info["duration"] < 1.0:
            f.unlink(missing_ok=True)
            continue
        q = detect_black_or_static(f, info["duration"])
        assets.append({"path": str(f), "width": info["width"], "height": info["height"], "fps": info["fps"],
                       "duration": info["duration"], "has_audio": info["has_audio"],
                       "src_in": s, "src_out": e if e is not None else round(s + info["duration"], 2),
                       "cuts": detect_cuts(f), "quality": q,
                       "phash": dhash_video(f, min(1.0, info["duration"] / 2), folder)})
    return assets


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--per-scene-video", type=int, default=0, help="0 = auto from scene shot count")
    ap.add_argument("--per-scene-image", type=int, default=0)
    ap.add_argument("--include-review", action="store_true", help="also download items with status 'review'")
    ap.add_argument("--config")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    setup_logging(a.verbose)
    cfg = load_config(a.config)
    pdir = project_dir(cfg, a.project)
    sb = read_json(pdir / "storyboard.json")
    verified = read_json(pdir / "verified.json")
    http = Http(cfg)
    index_path = pdir / "media_index.json"
    index = read_json(index_path) if index_path.exists() else {"assets": [], "failed": [], "duplicates": []}
    have = {x["candidate_id"] for x in index["assets"]}
    hashes = [(x["phash"], x["asset_id"]) for x in index["assets"] if x.get("phash")]
    ok_status = {"approved"} | ({"review"} if a.include_review else set()) | (
        {"fair_use_review"} if cfg["licensing"].get("allow_fair_use_clips") else set())
    ratio = cfg["timeline"]["visual_ratio"]

    for sc in sb["scenes"]:
        v = verified.get(sc["id"], {})
        n_vid = a.per_scene_video or max(2, math.ceil(sc.get("shots", 2) * ratio["video"]) + 1)
        n_img = a.per_scene_image or max(1, math.ceil(sc.get("shots", 2) * (ratio["image"] + ratio["graphic"])) + 1)
        for mt, need in (("video", n_vid), ("image", n_img)):
            got = sum(1 for x in index["assets"] if x["scene_id"] == sc["id"] and x["media_type"] == mt)
            for c in v.get(mt, []):
                if got >= need:
                    break
                if c["status"] not in ok_status or c["id"] in have:
                    continue
                try:
                    produced = process(c, pdir, http, cfg)
                except Exception as e:  # noqa: BLE001  -> fall back to next candidate
                    index["failed"].append({"candidate_id": c["id"], "url": c["page_url"], "error": str(e)[:300]})
                    log.warning("download failed %s: %s", c["page_url"], str(e)[:160])
                    continue
                for i, asset in enumerate(produced):
                    dup = next((aid for h, aid in hashes if hamming(h, asset["phash"]) <= 5), None)
                    if dup:
                        index["duplicates"].append({"candidate_id": c["id"], "duplicate_of": dup, "path": asset["path"]})
                        Path(asset["path"]).unlink(missing_ok=True)
                        continue
                    min_h = cfg["search"]["min_video_height"] if mt == "video" else 0
                    if mt == "video" and asset["height"] and asset["height"] < min_h:
                        index["failed"].append({"candidate_id": c["id"], "url": c["page_url"], "error": f"too small {asset['height']}p"})
                        continue
                    if mt == "video" and asset.get("quality", {}).get("black_ratio", 0) > 0.5:
                        index["failed"].append({"candidate_id": c["id"], "url": c["page_url"], "error": "mostly black"})
                        continue
                    aid = f"{c['id']}_{i}"
                    rec = {"asset_id": aid, "candidate_id": c["id"], "scene_id": sc["id"], "media_type": mt,
                           "sha1": sha1_file(asset["path"]), **asset,
                           "meta": {k: c.get(k) for k in ("provider", "title", "page_url", "media_url", "author", "handle",
                                                         "license", "license_raw", "date", "source_label", "credit",
                                                         "archival", "status", "verify_notes", "reconstruction")}}
                    rec["meta"]["present_day"] = c.get("extra", {}).get("present_day", False)
                    index["assets"].append(rec)
                    hashes.append((asset["phash"], aid))
                    got += 1
                have.add(c["id"])
                write_json(index_path, index)
    write_json(index_path, index)
    log.info("media index: %d assets, %d failed, %d duplicates", len(index["assets"]), len(index["failed"]), len(index["duplicates"]))
    print(index_path)


if __name__ == "__main__":
    main()
