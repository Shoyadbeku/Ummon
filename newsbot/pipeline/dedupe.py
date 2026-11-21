"""STEP 13: prevent re-publishing the same story under a different headline."""
from .db import conn
from .textsim import tokens, jaccard

THRESHOLD = 0.30   # >= means "same story"; the editor may still publish an explicit UPDATE


def already_covered(text: str, days: int = 4):
    t = tokens(text)
    best = None
    with conn() as c:
        rows = c.execute(
            "SELECT id, title, topic_key FROM episodes WHERE status NOT IN ('skipped','error') "
            "AND created_at >= datetime('now', ?)", (f"-{days} days",)
        ).fetchall()
    for r in rows:
        sim = jaccard(t, set((r["topic_key"] or "").split()))
        if sim >= THRESHOLD and (best is None or sim > best["similarity"]):
            best = {"episode": r["id"], "title": r["title"], "similarity": round(sim, 2)}
    return best


def topic_key(text: str) -> str:
    return " ".join(sorted(tokens(text)))
