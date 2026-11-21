"""STEP 16: static admin dashboard generated from the history DB (dashboard/index.html)."""
import html
import json
from datetime import datetime

from .config import ROOT, SLOTS, TZ
from .db import conn

CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#14171c;--muted:#5b6370;--line:#e3e6ea;--red:#d92b33;--ok:#1f8a4c;--warn:#b7791f}
@media (prefers-color-scheme: dark){:root{--bg:#0e1116;--card:#161a21;--ink:#e8eaed;--muted:#9aa3ad;--line:#262c35}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 Inter,system-ui,sans-serif}
main{max-width:1100px;margin:0 auto;padding:20px 16px}h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:28px 0 10px}
.muted{color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.big{font-size:26px;font-weight:800}table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden}
td,th{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;font-size:14px}th{color:var(--muted);font-weight:600}
.pill{display:inline-block;padding:1px 8px;border-radius:99px;font-size:12px;font-weight:700;border:1px solid var(--line)}
.published{color:var(--ok)}.error,.qc_failed{color:var(--red)}.rendered,.voiced,.draft{color:var(--warn)}
.score{font-weight:800}.wrap{overflow-x:auto}a{color:inherit}
"""


def _pill(s):
    return f'<span class="pill {html.escape(s or "")}">{html.escape(s or "-")}</span>'


def generate() -> str:
    now = datetime.now(TZ)
    today = now.strftime("%Y-%m-%d")
    with conn() as c:
        eps = c.execute("SELECT * FROM episodes ORDER BY created_at DESC LIMIT 60").fetchall()
        trends = c.execute("SELECT * FROM news_items WHERE score IS NOT NULL AND used_in_episode IS NULL ORDER BY score DESC LIMIT 25").fetchall()
        media = c.execute("SELECT * FROM media_assets ORDER BY id DESC LIMIT 40").fetchall()
        logs = c.execute("SELECT * FROM log WHERE level!='INFO' ORDER BY ts DESC LIMIT 20").fetchall()
        an = {r["episode_id"]: json.loads(r["metrics"]) for r in c.execute("SELECT * FROM analytics ORDER BY fetched_at")}
    today_eps = {e["slot"]: e for e in eps if e["id"].startswith(today)}
    pub = sum(1 for e in eps if e["status"] == "published")
    sched = "".join(
        f'<div class="card"><div class="muted">{s} · {html.escape(v["label"])}</div>'
        f'<div style="margin-top:6px">{_pill(today_eps[s]["status"]) if s in today_eps else _pill("kutilmoqda")}</div>'
        f'<div style="margin-top:6px">{html.escape((today_eps.get(s) or {}).get("title") or "")}</div></div>' for s, v in SLOTS.items())
    rows = "".join(
        f"<tr><td>{html.escape(e['id'])}</td><td>{html.escape(e['title'] or '')}</td><td class='score'>{e['viral_score'] or '-'}</td>"
        f"<td>{_pill(e['status'])}</td><td>{html.escape(str(an.get(e['id'], '')))[:120]}</td><td>{html.escape(e['error'] or '')[:120]}</td></tr>" for e in eps)
    trows = "".join(
        f"<tr><td class='score'>{int(t['score'])}</td><td><a href='{html.escape(t['url'])}' target='_blank' rel='noopener'>{html.escape(t['title'])}</a></td>"
        f"<td>{html.escape(t['source'])}</td><td>{t['region']}</td></tr>" for t in trends)
    mrows = "".join(
        f"<tr><td>{html.escape(m['episode_id'])}</td><td><a href='{html.escape(m['source_url'] or '')}' target='_blank' rel='noopener'>{html.escape((m['title'] or '')[:60])}</a></td>"
        f"<td>{html.escape(m['license'] or '')}</td><td>{html.escape((m['author'] or '')[:40])}</td></tr>" for m in media)
    lrows = "".join(f"<tr><td>{l['ts']}</td><td>{l['level']}</td><td>{html.escape(l['episode_id'] or '')}</td><td>{html.escape(l['msg'])[:200]}</td></tr>" for l in logs)
    page = f"""<!doctype html><html lang="uz"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NewsBot boshqaruv paneli</title><style>{CSS}</style></head><body><main>
<h1>NewsBot boshqaruv paneli</h1><div class="muted">Yangilangan: {now:%Y-%m-%d %H:%M} (Toshkent)</div>
<h2>Bugungi jadval</h2><div class="grid">{sched}</div>
<h2>Ko'rsatkichlar</h2><div class="grid"><div class="card"><div class="muted">Jami epizodlar</div><div class="big">{len(eps)}</div></div>
<div class="card"><div class="muted">E'lon qilingan</div><div class="big">{pub}</div></div>
<div class="card"><div class="muted">Kuzatuvdagi yangiliklar</div><div class="big">{len(trends)}</div></div></div>
<h2>Epizodlar (render, nashr, analitika)</h2><div class="wrap"><table><tr><th>ID</th><th>Sarlavha</th><th>Viral</th><th>Holat</th><th>Analitika</th><th>Xato</th></tr>{rows}</table></div>
<h2>Hozirgi trendlar (Viral Score)</h2><div class="wrap"><table><tr><th>Ball</th><th>Yangilik</th><th>Manba</th><th>Hudud</th></tr>{trows}</table></div>
<h2>Media manbalari va litsenziyalar</h2><div class="wrap"><table><tr><th>Epizod</th><th>Fayl</th><th>Litsenziya</th><th>Muallif</th></tr>{mrows}</table></div>
<h2>Ogohlantirish va xatolar</h2><div class="wrap"><table><tr><th>Vaqt</th><th>Daraja</th><th>Epizod</th><th>Xabar</th></tr>{lrows}</table></div>
</main></body></html>"""
    out = ROOT / "dashboard" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page)
    return str(out)
