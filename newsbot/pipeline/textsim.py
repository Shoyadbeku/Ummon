"""Lightweight multilingual text similarity for clustering and duplicate detection."""
import re

STOP = set("""
va bilan uchun bu u bir ham esa lekin yoki da dan ga ni ning ta deb edi bo'ldi bo'lgan qilindi qildi
haqida bo'yicha yil kuni sababli tomonidan orqali qadar keyin oldin endi yana ular biz siz
the a an of to in on for and or is are was were be by with at from as that this it its after over into
says said new news latest live update updates
""".split())


def norm(s: str) -> str:
    s = s.lower().replace("ʻ", "'").replace("ʼ", "'").replace("‘", "'").replace("’", "'").replace("`", "'")
    return re.sub(r"[^a-z0-9' ğşçöüıа-яёўқғҳ]+", " ", s)


def tokens(s: str) -> set[str]:
    out = set()
    for t in norm(s).split():
        t = t.strip("'")
        if len(t) < 3 or t in STOP:
            continue
        out.add(t[:6])  # crude stemming: Uzbek is agglutinative (Toshkentda -> toshke)
    return out


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
