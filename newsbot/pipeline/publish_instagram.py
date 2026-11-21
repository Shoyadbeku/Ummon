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


def upload(container: dict, video: Path) -> dict:
    data = video.read_bytes()
    uri = container.get("uri") or f"https://rupload.facebook.com/ig-api-upload/v21.0/{container['id']}"
    return _req("POST", uri, data=data, headers={
        "Authorization": f"OAuth {token()}", "offset": "0", "file_size": str(len(data)), "Content-Type": "application/octet-stream"})


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
