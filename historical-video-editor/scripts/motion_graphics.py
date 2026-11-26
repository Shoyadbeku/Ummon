"""Procedural motion graphics rendered with Pillow and piped to FFmpeg:

  * schematic historical map: graticule on a parchment/ink background, places from the
    gazetteer (lat/lon), animated route line, pulsing markers, labels, compass, title.
    It is explicitly labelled "Schematic map" — it is NOT a historical map.
  * title / fallback cards: textured background with slowly drifting light and
    centred serif text (kinetic fade + tracking).
"""
from __future__ import annotations

import math
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def ease(p: float) -> float:
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def parchment(w: int, h: int, seed: int = 3, dark: bool = True) -> Image.Image:
    rnd = random.Random(seed)
    base = (24, 26, 30) if dark else (214, 196, 160)
    img = Image.new("RGB", (w // 4, h // 4), base)
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            n = rnd.randint(-9, 9)
            px[x, y] = tuple(max(0, min(255, c + n)) for c in base)
    img = img.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2))
    # radial vignette
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    for i in range(40):
        r = i / 40
        d.ellipse([w * (0.5 - 0.9 + r * 0.9), h * (0.5 - 0.9 + r * 0.9), w * (0.5 + 0.9 - r * 0.9), h * (0.5 + 0.9 - r * 0.9)],
                  fill=int(255 * r))
    mask = mask.filter(ImageFilter.GaussianBlur(60))
    black = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(img, black, mask)


class FramePipe:
    def __init__(self, out: Path, w: int, h: int, fps: int, crf: int = 16, preset: str = "veryfast"):
        self.p = subprocess.Popen(
            ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps),
             "-i", "-", "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
             "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", str(out)],
            stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    def write(self, img: Image.Image):
        self.p.stdin.write(img.tobytes())

    def close(self):
        self.p.stdin.close()
        err = self.p.stderr.read().decode(errors="replace")
        if self.p.wait() != 0:
            raise RuntimeError(f"ffmpeg pipe failed: {err[-400:]}")


def render_map(out: Path, places: list[dict], title: str, label: str, duration: float, w: int, h: int, fps: int,
               font_path: str, serif_path: str, preset: str = "veryfast") -> Path:
    """places: [{name, lat, lon}] in route order."""
    pts = [p for p in places if p.get("lat") is not None]
    if not pts:
        pts = [{"name": title, "lat": 41.0, "lon": 64.0}]
    lats = [p["lat"] for p in pts]
    lons = [p["lon"] for p in pts]
    pad = max(4.0, (max(lons) - min(lons)) * 0.35, (max(lats) - min(lats)) * 0.35)
    lon0, lon1 = min(lons) - pad * 1.6, max(lons) + pad * 1.6
    lat0, lat1 = min(lats) - pad, max(lats) + pad
    # keep 16:9 aspect in degrees (equirectangular, corrected by cos(lat))
    k = math.cos(math.radians((lat0 + lat1) / 2))
    span_lon = lon1 - lon0
    span_lat = lat1 - lat0
    want = span_lon * k / (w / h)
    if want > span_lat:
        c = (lat0 + lat1) / 2
        lat0, lat1 = c - want / 2, c + want / 2
    else:
        c = (lon0 + lon1) / 2
        need = span_lat * (w / h) / k
        lon0, lon1 = c - need / 2, c + need / 2

    def xy(lat, lon):
        return ((lon - lon0) / (lon1 - lon0) * w, (lat1 - lat) / (lat1 - lat0) * h)

    bg = parchment(w, h)
    d = ImageDraw.Draw(bg)
    grid = (70, 78, 88)
    step = 5 if (lon1 - lon0) < 60 else 10
    for lon in range(int(lon0) // step * step, int(lon1) + step, step):
        x, _ = xy(lat0, lon)
        d.line([(x, 0), (x, h)], fill=grid, width=1)
        d.text((x + 4, h - 26), f"{abs(lon)}°{'E' if lon >= 0 else 'W'}", fill=(100, 108, 118), font=_font(font_path, max(12, h // 70)))
    for lat in range(int(lat0) // step * step, int(lat1) + step, step):
        _, y = xy(lat, lon0)
        d.line([(0, y), (w, y)], fill=grid, width=1)
        d.text((8, y + 3), f"{abs(lat)}°{'N' if lat >= 0 else 'S'}", fill=(100, 108, 118), font=_font(font_path, max(12, h // 70)))
    # compass
    cx, cy, r = w - int(w * 0.07), int(h * 0.14), int(h * 0.045)
    d.polygon([(cx, cy - r), (cx - r * 0.28, cy), (cx + r * 0.28, cy)], fill=(210, 170, 90))
    d.polygon([(cx, cy + r), (cx - r * 0.28, cy), (cx + r * 0.28, cy)], fill=(90, 96, 104))
    d.text((cx - 6, cy - r - 30), "N", fill=(210, 170, 90), font=_font(serif_path, max(14, h // 40)))
    f_lbl = _font(font_path, max(16, h // 34))
    f_title = _font(serif_path, max(22, h // 18))
    f_small = _font(font_path, max(12, h // 60))

    coords = [xy(p["lat"], p["lon"]) for p in pts]
    n_frames = max(1, int(round(duration * fps)))
    pipe = FramePipe(out, w, h, fps, preset=preset)
    accent = (232, 168, 47)
    try:
        for f in range(n_frames):
            t = f / fps
            p = ease(t / max(0.1, duration * 0.75))
            img = bg.copy()
            dr = ImageDraw.Draw(img, "RGBA")
            # slow camera push: we fake by drawing scale-independent; route animates
            total_len = sum(math.dist(coords[i], coords[i + 1]) for i in range(len(coords) - 1)) or 1
            drawn = p * total_len
            acc = 0.0
            for i in range(len(coords) - 1):
                a, b = coords[i], coords[i + 1]
                seg = math.dist(a, b)
                if acc + seg <= drawn:
                    dr.line([a, b], fill=accent + (235,), width=max(3, h // 220))
                elif acc < drawn:
                    q = (drawn - acc) / seg
                    m = (a[0] + (b[0] - a[0]) * q, a[1] + (b[1] - a[1]) * q)
                    dr.line([a, m], fill=accent + (235,), width=max(3, h // 220))
                    dr.ellipse([m[0] - 6, m[1] - 6, m[0] + 6, m[1] + 6], fill=(255, 230, 170, 255))
                acc += seg
            for i, (pt, (x, y)) in enumerate(zip(pts, coords)):
                appear = i / max(1, len(pts) - 1) * duration * 0.7 if len(pts) > 1 else 0.2
                if t < appear:
                    continue
                age = t - appear
                a = int(255 * min(1, age / 0.5))
                pulse = 10 + 8 * (0.5 + 0.5 * math.sin(age * 4))
                dr.ellipse([x - pulse, y - pulse, x + pulse, y + pulse], outline=accent + (int(a * 0.6),), width=2)
                dr.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(250, 244, 230, a))
                dr.text((x + 16, y - 14), pt["name"], fill=(245, 240, 228, a), font=f_lbl,
                        stroke_width=2, stroke_fill=(0, 0, 0, a))
            ta = int(255 * min(1, t / 0.8))
            dr.text((int(w * 0.05), int(h * 0.07)), title, fill=(245, 240, 228, ta), font=f_title)
            dr.text((int(w * 0.05), int(h * 0.07) + f_title.size + 10), label, fill=(160, 168, 178, ta), font=f_small)
            pipe.write(img)
    finally:
        pipe.close()
    return out


def render_card(out: Path, text: str, subtitle: str, duration: float, w: int, h: int, fps: int,
                serif_path: str, font_path: str, preset: str = "veryfast") -> Path:
    bg = parchment(w, h, seed=11)
    f_t = _font(serif_path, max(28, h // 13))
    f_s = _font(font_path, max(16, h // 38))
    n = max(1, int(round(duration * fps)))
    pipe = FramePipe(out, w, h, fps, preset=preset)
    try:
        for i in range(n):
            t = i / fps
            img = bg.copy()
            dr = ImageDraw.Draw(img, "RGBA")
            # drifting light
            lx = int(w * (0.3 + 0.4 * t / max(duration, 0.1)))
            glow = Image.new("L", (w, h), 0)
            ImageDraw.Draw(glow).ellipse([lx - w // 3, -h // 3, lx + w // 3, h], fill=38)
            glow = glow.filter(ImageFilter.GaussianBlur(120))
            img = Image.composite(Image.new("RGB", (w, h), (255, 236, 200)), img, glow)
            dr = ImageDraw.Draw(img, "RGBA")
            a = int(255 * min(1, t / 0.7, max(0, (duration - t) / 0.5)))
            spacing = int(12 * (1 - ease(t / 1.6)))
            tw = sum(dr.textlength(ch, font=f_t) + spacing for ch in text) - spacing
            x = (w - tw) / 2
            y = h * 0.44 - f_t.size / 2
            for ch in text:
                dr.text((x, y), ch, font=f_t, fill=(246, 241, 230, a))
                x += dr.textlength(ch, font=f_t) + spacing
            if subtitle:
                sw = dr.textlength(subtitle, font=f_s)
                dr.text(((w - sw) / 2, h * 0.44 + f_t.size * 0.9), subtitle, font=f_s, fill=(190, 196, 204, a))
            lw = int(w * 0.16 * ease(t / 1.2))
            dr.line([(w / 2 - lw, h * 0.44 + f_t.size * 0.75), (w / 2 + lw, h * 0.44 + f_t.size * 0.75)],
                    fill=(232, 168, 47, a), width=2)
            pipe.write(img)
    finally:
        pipe.close()
    return out
