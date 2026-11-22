"""Documentary edit decision list (v2): sentences -> shots (2-5 s), overlays, lower thirds,
per-shot source credits, transitions, synthesized SFX and music ducking.

episode.json sentence fields used here:
  shots:  [ <media index> | {"media": i, "speed": 0.7} | {"map": {...MapSpec}} ]   (optional; auto if missing)
  graphic, lower_third, highlight
"""
import json
import subprocess
from pathlib import Path

from .config import DATA
from .media import credit_for

MAX_SHOT = 4.2
MIN_SHOT = 1.6
TRANSITIONS = ["cut", "zoom", "cut", "whip", "cut", "flash"]


def _sfx_lib() -> dict:
    """Original SFX, synthesized once (no third-party rights)."""
    d = DATA / "sfx"
    d.mkdir(parents=True, exist_ok=True)
    spec = {
        "whoosh": ["-f", "lavfi", "-i", "anoisesrc=color=pink:d=0.7:a=0.6",
                   "-af", "highpass=f=500,lowpass=f=6000,afade=t=in:d=0.4:curve=exp,afade=t=out:st=0.4:d=0.3,volume=1.6"],
        "impact": ["-f", "lavfi", "-i", "aevalsrc=0.9*sin(2*PI*(70-40*t)*t)*exp(-3.5*t)+0.25*(random(0)-0.5)*exp(-18*t):d=1.4:s=48000",
                   "-af", "lowpass=f=900,aecho=0.7:0.4:40:0.3,volume=1.4"],
        "tick": ["-f", "lavfi", "-i", "aevalsrc=0.6*sin(2*PI*1800*t)*exp(-60*t):d=0.15:s=48000"],
    }
    out = {}
    for name, args in spec.items():
        f = d / f"{name}.wav"
        if not f.exists():
            args = [a.replace(",", "\\,") if a.startswith("aevalsrc") else a for a in args]
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args, "-ar", "48000", "-ac", "2", str(f)], check=True)
        out[name] = f
    return out


def _norm_shot(x):
    if isinstance(x, int):
        return {"media": x}
    return dict(x)


def build_edit(ep: dict, timings: dict, media: list[dict], body_end: float, intro_sec: float) -> dict:
    sents = timings["sentences"]
    approved = [m for m in media if m.get("approved", True)]
    pool = list(range(len(approved)))
    used_recent: list[int] = []
    shots, overlays, lthirds = [], [], []

    def pick_auto() -> int | None:
        if not pool:
            return None
        # prefer video, avoid the last 3 used
        cands = [i for i in pool if i not in used_recent[-3:]] or pool
        cands.sort(key=lambda i: (approved[i].get("kind") != "video", used_recent.count(i)))
        return cands[0]

    tcount = 0
    for si, (tm, spec) in enumerate(zip(sents, ep["sentences"])):
        start = 0.0 if si == 0 else tm["start"] - 0.08
        end = (sents[si + 1]["start"] - 0.08) if si + 1 < len(sents) else body_end
        span = end - start
        plan = [_norm_shot(x) for x in (spec.get("shots") or [])]
        n_needed = max(1, round(span / 3.2))
        while len(plan) < n_needed and span / (len(plan) + 1) >= MIN_SHOT:
            m = pick_auto()
            if m is None:
                break
            plan.append({"media": m})
            used_recent.append(m)
        if not plan:
            plan = [{"media": None}]
        step = span / len(plan)
        for k, sh in enumerate(plan):
            s0, s1 = start + k * step, start + (k + 1) * step
            m = approved[sh["media"]] if sh.get("media") is not None and sh["media"] < len(approved) else None
            if sh.get("media") is not None:
                used_recent.append(sh["media"])
            tr = "flash" if si == 0 and k == 0 else TRANSITIONS[tcount % len(TRANSITIONS)]
            tcount += 1
            shots.append({
                "start": round(s0, 3), "end": round(s1, 3),
                "media": m["file"] if m else None, "mediaType": (m or {}).get("kind", "image"),
                "credit": credit_for(m) if m else None, "illustrative": bool((m or {}).get("illustrative")),
                "speed": sh.get("speed", 0.85 if (m or {}).get("kind") == "video" and si == 0 else 1.0),
                "transition": "zoom" if sh.get("map") else tr,
                "map": sh.get("map"),
            })
        if spec.get("graphic"):
            overlays.append({"start": round(start + 0.2, 3), "end": round(end - 0.1, 3), "graphic": spec["graphic"]})
        if spec.get("lower_third"):
            lthirds.append({"start": round(start + 0.15, 3), "end": round(end - 0.1, 3), "text": spec["lower_third"]})

    # SFX: impact on the hook, whooshes on whip/zoom/map transitions and graphic entries (kept sparse)
    lib = _sfx_lib()
    sfx = [{"src": "sfx_impact.wav", "at": 0.0, "volume": 0.55}, {"src": "sfx_whoosh.wav", "at": max(0, intro_sec - 0.35), "volume": 0.35}]
    last = -10.0
    for s in shots[1:]:
        if s["transition"] in ("whip", "zoom") and s["start"] - last > 2.5 and s["start"] > intro_sec:
            sfx.append({"src": "sfx_whoosh.wav", "at": round(max(0, s["start"] - 0.3), 3), "volume": 0.22})
            last = s["start"]
    for o in overlays:
        sfx.append({"src": "sfx_tick.wav", "at": o["start"] + 0.1, "volume": 0.25})

    # music ducking: louder in intro/gaps/outro, low under narration
    env = [{"t": 0.0, "v": 0.16}, {"t": max(0.4, sents[0]["start"]), "v": 0.07}]
    for a, b in zip(sents, sents[1:]):
        gap = b["start"] - a["end"]
        if gap > 0.25:
            env += [{"t": a["end"], "v": 0.07}, {"t": a["end"] + gap / 2, "v": 0.1}, {"t": b["start"], "v": 0.07}]
    env += [{"t": sents[-1]["end"], "v": 0.07}, {"t": sents[-1]["end"] + 0.5, "v": 0.18}, {"t": body_end + 5, "v": 0.18}]
    return {"shots": shots, "overlays": overlays, "lowerThirds": lthirds, "sfx": sfx, "musicVolume": env, "sfx_files": lib}
