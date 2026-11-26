"""Shared helpers: config, .env, logging, HTTP with retries/rate limiting,
ffmpeg/ffprobe wrappers, JSON IO and project paths.

Every other script imports from here, so the modules stay independent of
each other but behave consistently.
"""
from __future__ import annotations

import copy
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import unicodedata
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = SKILL_ROOT / "config.yaml"

log = logging.getLogger("hve")


# --------------------------------------------------------------------------
# logging
# --------------------------------------------------------------------------
def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )


# --------------------------------------------------------------------------
# .env + config
# --------------------------------------------------------------------------
def load_env(path: Path | None = None) -> None:
    """Load .env without overriding variables already set in the shell."""
    candidates = [path] if path else [Path.cwd() / ".env", SKILL_ROOT / ".env"]
    for p in candidates:
        if not p or not p.exists():
            continue
        try:
            from dotenv import load_dotenv  # type: ignore

            load_dotenv(p, override=False)
        except ImportError:  # tiny fallback parser
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                v = v.split(" #", 1)[0].strip().strip('"').strip("'")
                os.environ.setdefault(k.strip(), v)


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def deep_merge(base: dict, extra: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load_config(extra: str | Path | None = None) -> dict:
    import yaml

    load_env()
    cfg = yaml.safe_load(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    if extra:
        p = Path(extra)
        if p.exists():
            cfg = deep_merge(cfg, yaml.safe_load(p.read_text(encoding="utf-8")) or {})
    return cfg


# --------------------------------------------------------------------------
# JSON / paths
# --------------------------------------------------------------------------
def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, data: Any) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)
    return p


def slugify(text: str, maxlen: int = 60) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii") or hashlib.md5(text.encode()).hexdigest()[:8]
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:maxlen] or "project"


def project_dir(cfg: dict, slug: str) -> Path:
    base = Path(cfg["paths"]["workdir"])
    if not base.is_absolute():
        base = SKILL_ROOT / base
    d = base / slug
    for sub in ("media/video", "media/image", "media/graphic", "audio", "render/segments", "reports"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    return d


def sha1_file(path: str | Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def domain_of(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def chunked(seq: list, n: int) -> Iterable[list]:
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------
class Http:
    """requests.Session with retries, exponential backoff on 429/5xx and a
    per-host minimum interval so we behave politely with public archives."""

    def __init__(self, cfg: dict):
        import requests

        self.cfg = cfg["http"]
        self.s = requests.Session()
        ua = self.cfg["user_agent"]
        contact = env("WIKIMEDIA_CONTACT")
        if contact:
            ua = f"{ua} contact:{contact}"
        self.s.headers.update({"User-Agent": ua, "Accept-Language": "en,ru;q=0.8,uz;q=0.6"})
        self._last: dict[str, float] = {}
        self._lock = threading.Lock()

    def _wait(self, url: str) -> None:
        host = domain_of(url)
        with self._lock:
            gap = self.cfg.get("min_interval_sec", 1.0)
            last = self._last.get(host, 0.0)
            now = time.time()
            if now - last < gap:
                time.sleep(gap - (now - last))
            self._last[host] = time.time()

    def request(self, method: str, url: str, **kw):
        import requests

        kw.setdefault("timeout", self.cfg.get("timeout_sec", 30))
        retries = int(self.cfg.get("retries", 4))
        backoff = float(self.cfg.get("backoff_sec", 2.0))
        last_exc: Exception | None = None
        for attempt in range(retries + 1):
            self._wait(url)
            try:
                r = self.s.request(method, url, **kw)
                if r.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                    ra = r.headers.get("Retry-After", "")
                    delay = float(ra) if ra.isdigit() and int(ra) < 60 else backoff * (2**attempt)
                    log.debug("HTTP %s on %s, retry in %.1fs", r.status_code, domain_of(url), delay)
                    time.sleep(delay)
                    continue
                return r
            except requests.RequestException as e:  # network error
                last_exc = e
                if attempt < retries:
                    time.sleep(backoff * (2**attempt))
        raise ConnectionError(f"{method} {url} failed: {last_exc}")

    def get_json(self, url: str, **kw) -> Any:
        r = self.request("GET", url, **kw)
        if r.status_code != 200:
            raise ConnectionError(f"HTTP {r.status_code} for {domain_of(url)}: {r.text[:200]}")
        return r.json()

    def head_ok(self, url: str) -> tuple[bool, int, str]:
        """Return (alive, status, final_url). Falls back to ranged GET when HEAD is refused."""
        try:
            r = self.request("HEAD", url, allow_redirects=True)
            if r.status_code in (403, 405, 501):
                r = self.request("GET", url, allow_redirects=True, stream=True, headers={"Range": "bytes=0-1023"})
                r.close()
            return (r.status_code < 400, r.status_code, r.url)
        except ConnectionError:
            return (False, 0, url)


# --------------------------------------------------------------------------
# ffmpeg / ffprobe
# --------------------------------------------------------------------------
def require_binary(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"'{name}' not found in PATH. Install FFmpeg (https://ffmpeg.org/download.html).")
    return path


def run(cmd: list[str], check: bool = True, quiet: bool = True, timeout: int | None = None) -> subprocess.CompletedProcess:
    log.debug("RUN %s", " ".join(map(str, cmd))[:2000])
    p = subprocess.run(list(map(str, cmd)), capture_output=True, text=True, timeout=timeout)
    if check and p.returncode != 0:
        tail = "\n".join(p.stderr.strip().splitlines()[-25:])
        raise RuntimeError(f"command failed ({p.returncode}): {cmd[0]} ...\n{tail}")
    if not quiet and p.stderr:
        log.info(p.stderr[-2000:])
    return p


def ffprobe(path: str | Path) -> dict:
    require_binary("ffprobe")
    p = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)])
    return json.loads(p.stdout or "{}")


def media_info(path: str | Path) -> dict:
    """Compact summary: duration, width, height, fps, has_audio, vcodec, acodec."""
    info = ffprobe(path)
    out = {"duration": 0.0, "width": 0, "height": 0, "fps": 0.0, "has_audio": False,
           "has_video": False, "vcodec": "", "acodec": "", "size": 0}
    fmt = info.get("format", {})
    try:
        out["duration"] = float(fmt.get("duration", 0) or 0)
        out["size"] = int(fmt.get("size", 0) or 0)
    except ValueError:
        pass
    for s in info.get("streams", []):
        if s.get("codec_type") == "video" and not out["has_video"]:
            if s.get("disposition", {}).get("attached_pic"):
                continue
            out["has_video"] = True
            out["width"], out["height"] = int(s.get("width", 0)), int(s.get("height", 0))
            out["vcodec"] = s.get("codec_name", "")
            fr = s.get("avg_frame_rate") or s.get("r_frame_rate") or "0/1"
            try:
                a, b = fr.split("/")
                out["fps"] = round(float(a) / float(b), 3) if float(b) else 0.0
            except Exception:
                pass
            if not out["duration"]:
                out["duration"] = float(s.get("duration", 0) or 0)
        elif s.get("codec_type") == "audio" and not out["has_audio"]:
            out["has_audio"] = True
            out["acodec"] = s.get("codec_name", "")
    return out


def ffmpeg_has(feature: str) -> bool:
    """Check whether ffmpeg has a given filter or encoder."""
    try:
        p = run(["ffmpeg", "-hide_banner", "-filters"], check=False)
        if re.search(rf"\s{re.escape(feature)}\s", p.stdout):
            return True
        p = run(["ffmpeg", "-hide_banner", "-encoders"], check=False)
        return bool(re.search(rf"\s{re.escape(feature)}\s", p.stdout))
    except Exception:
        return False


def find_font(cfg: dict, family: str | None = None) -> str:
    """Return a font file path for drawtext (prefers assets/fonts, then fontconfig)."""
    fonts_dir = SKILL_ROOT / cfg["paths"]["fonts_dir"]
    for ext in ("*.ttf", "*.otf"):
        for f in sorted(fonts_dir.glob(ext)):
            return str(f)
    fam = family or cfg["overlay"].get("font", "DejaVu Sans")
    if shutil.which("fc-match"):
        p = run(["fc-match", "-f", "%{file}", fam], check=False)
        if p.stdout and Path(p.stdout).exists():
            return p.stdout
    for c in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf",
              "/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf"):
        if Path(c).exists():
            return c
    raise RuntimeError("No font found. Put a .ttf file into assets/fonts/.")


def fmt_ts(sec: float) -> str:
    """Seconds -> HH:MM:SS"""
    sec = max(0, int(round(sec)))
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def fmt_yt(sec: float) -> str:
    """Seconds -> YouTube chapter timestamp (M:SS or H:MM:SS)."""
    sec = max(0, int(sec))
    h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
