"""Turns an editor-written episode.json + timings into Remotion render props, then renders and QCs."""
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from .config import BRAND, DATA, REMOTION, SLOTS, TZ
from .media import credits_line
from .uz_text import MONTHS

INTRO_SEC = 2.6
OUTRO_SEC = 2.5
COVER_SEC = 0.7     # designed cover held at the end; Instagram cover = this frame (thumb_offset)


def _cover_media(ep: dict, approved: list) -> str | None:
    idx = ep.get("cover_media")
    if idx is None:
        idx = next((s.get("media") for s in ep["sentences"] if s.get("media") is not None), 0)
    return approved[idx]["file"] if approved and idx < len(approved) else None


def cover_offset_ms(ep_dir: Path) -> int:
    props = json.loads((ep_dir / "render_props.json").read_text())
    return int((props["durationSec"] - props.get("coverSec", 0) / 2) * 1000)


def music_bed() -> Path:
    """Original, procedurally generated news bed (no third-party rights involved)."""
    out = DATA / "music_bed.wav"
    if out.exists():
        return out
    expr = ("0.05*sin(2*PI*110*t)*(0.6+0.4*sin(2*PI*0.25*t))"
            "+0.035*sin(2*PI*164.81*t)*(0.6+0.4*sin(2*PI*0.2*t+1))"
            "+0.03*sin(2*PI*220*t)+0.025*sin(2*PI*261.63*t)*(0.5+0.5*sin(2*PI*0.125*t))"
            "+0.22*sin(2*PI*52*t)*exp(-14*mod(t,0.5))"
            "+0.05*sin(2*PI*880*t)*exp(-40*mod(t+0.25,0.5))")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"aevalsrc={expr}:s=48000:d=120",
                    "-af", "lowpass=f=2500,aecho=0.6:0.5:60:0.25,loudnorm=I=-20", "-ac", "2", str(out)], check=True)
    return out


def date_label(dt: datetime) -> str:
    return f"{dt.day}-{MONTHS[dt.month - 1].upper()}, {dt.year}"


def build_props(ep_dir: Path) -> dict:
    ep = json.loads((ep_dir / "episode.json").read_text())
    tm = json.loads((ep_dir / "timings.json").read_text())
    media = json.loads((ep_dir / "media.json").read_text()) if (ep_dir / "media.json").exists() else []
    approved = [m for m in media if m.get("approved", True)]
    sents = tm["sentences"]
    voice_end = tm["duration"]
    body = round(voice_end + 0.6 + OUTRO_SEC, 2)
    total = round(body + COVER_SEC, 2)
    segments = []
    for i, (s, spec) in enumerate(zip(sents, ep["sentences"])):
        start = 0 if i == 0 else s["start"] - 0.1
        end = (sents[i + 1]["start"] - 0.1) if i + 1 < len(sents) else body
        midx = spec.get("media")
        if midx is None and approved:            # never leave a sentence without visuals
            midx = i % len(approved)
        m = approved[midx] if (midx is not None and midx < len(approved)) else None
        segments.append({
            "start": round(start, 3), "end": round(end, 3),
            "media": m["file"] if m else None, "mediaType": (m or {}).get("kind", "image"),
            "graphic": spec.get("graphic"), "lowerThird": spec.get("lower_third"),
        })
    # merge consecutive segments that share the same media & no graphic change -> smoother edit
    slot = SLOTS.get(ep.get("slot", ""), {})
    shutil.copy(music_bed(), ep_dir / "music.wav")
    props = {
        "brand": BRAND,
        "kicker": ep.get("kicker") or slot.get("kicker", "YANGILIKLAR"),
        "region": ep.get("region", slot.get("region", "uz")),
        "breaking": bool(ep.get("breaking")),
        "hook": ep["hook"],
        "headline": ep["headline"],
        "dateLabel": date_label(datetime.now(TZ)),
        "audio": "voice.wav",
        "music": "music.wav",
        "durationSec": total,
        "segments": segments,
        "words": [w for w in tm["words"] if w["start"] >= INTRO_SEC - 0.2],  # intro shows the hook itself
        "ticker": ep.get("ticker") or ep["headline"],
        "credits": credits_line(approved),
        "outroText": ep.get("outro_text", "Har kuni eng muhim yangiliklar"),
        "thumbnailText": ep.get("thumbnail_text") or ep["headline"],
        "coverMedia": _cover_media(ep, approved),
        "coverSec": COVER_SEC,
    }
    (ep_dir / "render_props.json").write_text(json.dumps(props, ensure_ascii=False, indent=1))
    return props


def render(ep_dir: Path) -> Path:
    subprocess.run(["node", str(REMOTION / "render.mjs"), str(ep_dir)], check=True, cwd=REMOTION)
    return ep_dir / "final.mp4"


def qc(ep_dir: Path) -> dict:
    """STEP 11: automatic technical QC. Editorial QC (facts, imagery) is done by the editor/admin."""
    f = ep_dir / "final.mp4"
    probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(f)],
                                      capture_output=True, text=True, check=True).stdout)
    v = next(s for s in probe["streams"] if s["codec_type"] == "video")
    a = next((s for s in probe["streams"] if s["codec_type"] == "audio"), None)
    dur = float(probe["format"]["duration"])
    lufs = subprocess.run(["ffmpeg", "-i", str(f), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    il = [l for l in lufs.splitlines() if l.strip().startswith("I:")]
    loud = float(il[-1].split()[1]) if il else None
    checks = {
        "resolution_1080x1920": (v["width"], v["height"]) == (1080, 1920),
        "fps_30": v["r_frame_rate"] in ("30/1", "30000/1001"),
        "has_audio": a is not None,
        "duration_15_90s": 15 <= dur <= 90,
        "loudness_ok": loud is not None and -20 <= loud <= -11,
        "size_under_100mb": int(probe["format"]["size"]) < 100 * 1024 * 1024,
    }
    res = {"ok": all(checks.values()), "checks": checks, "duration": round(dur, 2), "lufs": loud}
    (ep_dir / "qc.json").write_text(json.dumps(res, indent=1))
    # contact sheet for visual review
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(f), "-vf", f"fps={6/dur:.4f},scale=270:-1,tile=6x1",
                    "-frames:v", "1", str(ep_dir / "contact_sheet.jpg")])
    return res
