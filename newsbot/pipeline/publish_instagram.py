"""STEP 14: Instagram Reels publishing via the Instagram Graph API (resumable upload, no public hosting needed).

Token: env IG_TOKEN or file IG_TOKEN_FILE (outside the repo, chmod 600). Never commit it.
"""
import json
import os
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

from .config import GRAPH, IG_TOKEN_FILE, IG_USER_ID


def token() -> str:
    t = os.environ.get("IG_TOKEN")
    if not t and Path(IG_TOKEN_FILE).exists():
        t = Path(IG_TOKEN_FILE).read_text().strip()
    if not t:
        raise RuntimeError("Instagram token yo'q: IG_TOKEN yoki IG_TOKEN_FILE sozlang")
    return t


def _req(method: str, url: str, params: dict | None = None, data: bytes | None = None, headers: dict | None = None):
    h = {"Authorization": f"Bearer {token()}"}
    h.update(headers or {})
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Graph API {e.code}: {e.read().decode()[:400]}") from None


def account_info() -> dict:
    return _req("GET", f"{GRAPH}/{IG_USER_ID}", {"fields": "username,followers_count,media_count"})


def quota() -> dict:
    return _req("GET", f"{GRAPH}/{IG_USER_ID}/content_publishing_limit", {"fields": "quota_usage,config"})


def create_container(caption: str, share_to_feed: bool = True, thumb_offset_ms: int | None = None) -> dict:
    params = {"media_type": "REELS", "upload_type": "resumable", "caption": caption, "share_to_feed": str(share_to_feed).lower()}
    if thumb_offset_ms is not None:
        params["thumb_offset"] = str(thumb_offset_ms)   # cover = the designed thumbnail frame
    return _req("POST", f"{GRAPH}/{IG_USER_ID}/media", params)


def _curl(uri: str, headers: list[str], body: Path | None = None, timeout: int = 600) -> dict:
    import subprocess
    cfg = "".join(f'header = "{h}"\n' for h in [f"Authorization: OAuth {token()}", *headers])
    cmd = ["curl", "-s", "-m", str(timeout), uri, "-K", "-"]
    if body is not None:
        cmd[1:1] = ["-X", "POST", "--data-binary", f"@{body}"]
    r = subprocess.run(cmd, input=cfg, capture_output=True, text=True)
    try:
        return json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        return {"raw": r.stdout[:300], "err": r.stderr[:200]}


def upload_copy(video: Path) -> Path:
    """Lighter H.264 copy for upload (same 1080x1920/30fps; ~3.5 Mbps). Big bodies get cut in transit."""
    import subprocess
    out = video.with_name("upload.mp4")
    if not out.exists() or out.stat().st_mtime < video.stat().st_mtime:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-c:v", "libx264", "-preset", "slow", "-crf", "23",
                        "-maxrate", "4M", "-bufsize", "8M", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                        "-c:a", "aac", "-b:a", "160k", str(out)], check=True)
    return out


def upload(container: dict, video: Path, tries: int = 8) -> dict:
    """Resumable upload: on a cut transfer, ask the server how many bytes it has and continue from there.
    (Uses curl: Python's urllib re-capitalises header names, which rupload.facebook.com rejects.)"""
    import tempfile
    uri = f"https://rupload.facebook.com/ig-api-upload/{GRAPH.rsplit('/', 1)[1]}/{container['id']}"
    data = video.read_bytes()
    size = len(data)
    last = {}
    for _ in range(tries):
        off = int(_curl(uri, []).get("offset") or 0)
        with tempfile.NamedTemporaryFile(suffix=".bin") as tmp:
            tmp.write(data[off:]); tmp.flush()
            last = _curl(uri, [f"offset: {off}", f"file_size: {size}"], Path(tmp.name))
        if last.get("success"):
            return last
        time.sleep(3)
    raise RuntimeError(f"upload failed: {last}")


def wait_ready(container_id: str, timeout: int = 600) -> str:
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = _req("GET", f"{GRAPH}/{container_id}", {"fields": "status_code,status"})
        code = st.get("status_code")
        if code in ("FINISHED", "ERROR", "EXPIRED"):
            if code != "FINISHED":
                raise RuntimeError(f"container {code}: {st.get('status')}")
            return code
        time.sleep(8)
    raise TimeoutError("Instagram video processing timed out")


def publish(container_id: str) -> str:
    return _req("POST", f"{GRAPH}/{IG_USER_ID}/media_publish", {"creation_id": container_id})["id"]


def permalink(media_id: str) -> str:
    return _req("GET", f"{GRAPH}/{media_id}", {"fields": "permalink"}).get("permalink", "")


def insights(media_id: str) -> dict:
    """STEP 15: post-publication metrics (needs instagram_manage_insights)."""
    try:
        r = _req("GET", f"{GRAPH}/{media_id}/insights", {"metric": "views,reach,likes,comments,shares,saved,ig_reels_avg_watch_time,ig_reels_video_view_total_time"})
        return {m["name"]: (m.get("values") or [{}])[0].get("value") for m in r.get("data", [])}
    except RuntimeError as e:
        return {"error": str(e)[:200]}
