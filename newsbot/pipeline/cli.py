"""NewsBot command line. Run from newsbot/:  python3 -m pipeline.cli <command> ...

  discover [--region uz|world] [--hours 6]      crawl RSS, score, list top candidates (JSON)
  slot                                          which slot is next (Asia/Tashkent)
  new <slot> <region>                           create episodes/<id>/ with an episode.json template
  media <id> "query 1" "query 2" ...            fetch licence-clean images (Wikimedia Commons)
  voice <id>                                    synthesize anchor voice + word timings + SRT
  render <id>                                   build props, render MP4 with Remotion, run QC
  produce <id>                                  voice + render (+ qc) in one go
  publish <id> --confirm                        upload + publish Reels to Instagram
  stage <id>                                    upload + process on Instagram WITHOUT publishing (test)
  status [<id>]                                 episode status from the history DB
  dashboard                                     regenerate dashboard/index.html
  analytics                                     pull insights for published episodes
"""
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from . import db
from .config import EPISODES, PUBLISH_MODE, SLOTS, TZ
from .dedupe import already_covered, topic_key


def ep_dir(ep_id: str) -> Path:
    d = EPISODES / ep_id
    if not d.exists():
        sys.exit(f"episode topilmadi: {d}")
    return d


def next_slot(now: datetime | None = None) -> tuple[str, datetime]:
    now = now or datetime.now(TZ)
    for day in (0, 1):
        for s in SLOTS:
            h, m = map(int, s.split(":"))
            t = (now + timedelta(days=day)).replace(hour=h, minute=m, second=0, microsecond=0)
            if t > now:
                return s, t
    raise RuntimeError


TEMPLATE = {
    "slot": "", "region": "", "breaking": False, "kicker": "",
    "title": "Video sarlavhasi (platforma uchun)",
    "headline": "Ekrandagi qisqa sarlavha",
    "hook": "1-3 soniyalik kuchli hook (birinchi gap bilan bir xil ma'noda)",
    "thumbnail_text": "Muqova matni",
    "event_date": "YYYY-MM-DD",
    "viral_score": {"total": 0, "freshness": 0, "impact": 0, "coverage": 0, "trust": 0, "visual": 0, "local": 0, "note": ""},
    "sentences": [
        {"text": "Birinchi gap — hook, ovozda aytiladi.", "highlight": ["kalit"], "media": None, "graphic": None, "lower_third": None},
    ],
    "caption": "Instagram/YouTube description",
    "hashtags": ["#yangiliklar"],
    "ticker": "Pastki yugurik qator matni",
    "sources": [{"name": "", "url": "", "published": ""}],
    "storyboard_note": "storyboard.md avtomatik yaratiladi",
}


def cmd_new(slot: str, region: str):
    now = datetime.now(TZ)
    ep_id = f"{now:%Y-%m-%d}-{slot.replace(':', '')}-{region}"
    d = EPISODES / ep_id
    d.mkdir(parents=True, exist_ok=True)
    f = d / "episode.json"
    if not f.exists():
        tpl = dict(TEMPLATE, slot=slot, region=region, kicker=SLOTS.get(slot, {}).get("kicker", ""))
        f.write_text(json.dumps(tpl, ensure_ascii=False, indent=2))
    db.upsert_episode(ep_id, slot=slot, region=region, status="draft")
    print(ep_id)


def _register(ep_id: str, ep: dict):
    text = ep["headline"] + " " + " ".join(s["text"] for s in ep["sentences"][:3])
    dup = already_covered(text)
    db.upsert_episode(ep_id, title=ep["headline"], topic_key=topic_key(text), event_date=ep.get("event_date"),
                      viral_score=(ep.get("viral_score") or {}).get("total"), sources=ep.get("sources", []),
                      similarity=(dup or {}).get("similarity"), is_update_of=(dup or {}).get("episode") if dup and dup["episode"] != ep_id else None)
    return dup


def storyboard(d: Path):
    ep = json.loads((d / "episode.json").read_text())
    tm = json.loads((d / "timings.json").read_text()) if (d / "timings.json").exists() else None
    lines = [f"# Storyboard — {ep['headline']}", "", "| Vaqt | Ovoz (gap) | Vizual | Grafika | Lower third |", "|---|---|---|---|---|"]
    for i, s in enumerate(ep["sentences"]):
        t = f"{tm['sentences'][i]['start']:.1f}–{tm['sentences'][i]['end']:.1f}s" if tm else "-"
        g = (s.get("graphic") or {}).get("type", "")
        lines.append(f"| {t} | {s['text']} | media #{s.get('media', 'auto')} | {g} | {s.get('lower_third') or ''} |")
    (d / "storyboard.md").write_text("\n".join(lines) + "\n")


def cmd_voice(ep_id: str):
    from .tts import synthesize, to_srt
    d = ep_dir(ep_id)
    ep = json.loads((d / "episode.json").read_text())
    dup = _register(ep_id, ep)
    if dup and dup["episode"] != ep_id:
        db.log("WARN", f"o'xshash video bor: {dup}", ep_id)
    data = synthesize(d, ep["sentences"], log=lambda m: db.log("INFO", m, ep_id))
    to_srt(data["words"], d / "subtitles.srt")
    storyboard(d)
    db.upsert_episode(ep_id, status="voiced")


def cmd_render(ep_id: str):
    from .build import build_props, render, qc
    d = ep_dir(ep_id)
    try:
        build_props(d)
        for attempt in (1, 2):              # retry once (headless browser hiccups)
            try:
                render(d)
                break
            except Exception as ex:
                db.log("WARN", f"render attempt {attempt} failed: {ex}", ep_id)
                if attempt == 2:
                    raise
        res = qc(d)
        storyboard(d)
        db.upsert_episode(ep_id, status="rendered" if res["ok"] else "qc_failed", rendered_at=db.now_utc(),
                          video_path=str(d / "final.mp4"))
        print(json.dumps(res, indent=1))
    except Exception as ex:
        db.upsert_episode(ep_id, status="error", error=str(ex)[:500])
        raise


def _caption(ep: dict) -> str:
    src = ", ".join(s["name"] for s in ep.get("sources", []) if s.get("name"))
    cap = ep.get("caption", ep["headline"])
    return f"{cap}\n\nManba: {src}\n\n{' '.join(ep.get('hashtags', []))}".strip()[:2150]


def cmd_publish(ep_id: str, confirm: bool, stage_only: bool = False):
    from . import publish_instagram as ig
    d = ep_dir(ep_id)
    ep = json.loads((d / "episode.json").read_text())
    if not stage_only and PUBLISH_MODE == "approval" and not confirm:
        sys.exit("approval rejimi: admin tasdig'isiz e'lon qilinmaydi (--confirm kerak)")
    qcj = json.loads((d / "qc.json").read_text())
    if not qcj["ok"]:
        sys.exit(f"QC o'tmagan: {qcj['checks']}")
    from .build import cover_offset_ms
    c = None
    for attempt in range(1, 7):         # rupload.facebook.com rejects uploads intermittently -> fresh container + retry
        try:
            c = ig.create_container(_caption(ep), thumb_offset_ms=cover_offset_ms(d))
            time.sleep(10)
            ig.upload(c, ig.upload_copy(d / "final.mp4"))
            ig.wait_ready(c["id"])
            break
        except Exception as ex:
            db.log("WARN", f"upload attempt {attempt}: {str(ex)[:200]}", ep_id)
            c = None
            time.sleep(15 * attempt)
    if c is None:
        db.upsert_episode(ep_id, status="error", error="upload failed after retries")
        sys.exit("upload failed after retries")
    if stage_only:
        db.log("INFO", f"staged container {c['id']} (not published)", ep_id)
        print(json.dumps({"staged": c["id"]}))
        return
    mid = None
    for attempt in range(1, 5):
        try:
            mid = ig.publish(c["id"])
            break
        except Exception as ex:
            db.log("WARN", f"publish attempt {attempt}: {str(ex)[:200]}", ep_id)
            time.sleep(30 * attempt)
            # never double-post: check whether the container got published despite the error
            st = ig._req("GET", f"{ig.GRAPH}/{c['id']}", {"fields": "status_code"})
            if st.get("status_code") == "PUBLISHED":
                break
    if mid is None:
        recent = ig._req("GET", f"{ig.GRAPH}/{ig.IG_USER_ID}/media", {"fields": "id,caption", "limit": "3"}).get("data", [])
        mid = next((m["id"] for m in recent if (m.get("caption") or "").startswith(_caption(ep)[:40])), None)
    if mid is None:
        db.upsert_episode(ep_id, status="error", error="publish failed after retries")
        sys.exit("publish failed after retries")
    link = ig.permalink(mid)
    db.upsert_episode(ep_id, status="published", published_at=db.now_utc(), ig_media_id=mid)
    with db.conn() as cx:
        for s in ep.get("sources", []):
            cx.execute("UPDATE news_items SET used_in_episode=? WHERE url=?", (ep_id, s.get("url")))
    print(json.dumps({"media_id": mid, "permalink": link}))


def cmd_analytics():
    from . import publish_instagram as ig
    with db.conn() as c:
        rows = c.execute("SELECT id, ig_media_id FROM episodes WHERE ig_media_id IS NOT NULL").fetchall()
        for r in rows:
            m = ig.insights(r["ig_media_id"])
            c.execute("INSERT INTO analytics VALUES (?,?,?)", (r["id"], db.now_utc(), json.dumps(m)))
            print(r["id"], m)


def main(argv=None):
    a = argv or sys.argv[1:]
    if not a:
        print(__doc__); return
    cmd = a[0]
    if cmd == "discover":
        from .discover import crawl, score_items, candidates
        region = a[a.index("--region") + 1] if "--region" in a else None
        hours = float(a[a.index("--hours") + 1]) if "--hours" in a else 6
        crawl(); score_items()
        regions = [region] if region else ["uz", "world"]
        out = {r: [{k: c[k] for k in ("score", "title", "source", "url", "published_at", "score_detail", "duplicate_of", "image_url")} for c in candidates(r, hours)] for r in regions}
        print(json.dumps(out, ensure_ascii=False, indent=1))
    elif cmd == "slot":
        s, t = next_slot()
        print(json.dumps({"slot": s, "at": t.isoformat(), **SLOTS[s]}, ensure_ascii=False))
    elif cmd == "new":
        cmd_new(a[1], a[2])
    elif cmd == "media":
        from .media import fetch_media
        got = fetch_media(ep_dir(a[1]), a[1], a[2:])
        print(json.dumps(got, ensure_ascii=False, indent=1))
    elif cmd == "voice":
        cmd_voice(a[1])
    elif cmd == "render":
        cmd_render(a[1])
    elif cmd == "produce":
        cmd_voice(a[1]); cmd_render(a[1])
    elif cmd == "publish":
        cmd_publish(a[1], "--confirm" in a)
    elif cmd == "stage":
        cmd_publish(a[1], False, stage_only=True)
    elif cmd == "status":
        with db.conn() as c:
            q = "SELECT * FROM episodes" + (" WHERE id=?" if len(a) > 1 else " ORDER BY created_at DESC LIMIT 20")
            for r in c.execute(q, (a[1],) if len(a) > 1 else ()):
                print(dict(r))
    elif cmd == "dashboard":
        from .dashboard import generate
        print(generate())
    elif cmd == "analytics":
        cmd_analytics()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
