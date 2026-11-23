#!/usr/bin/env python3
"""Write Subtitles.srt, Storyboard.csv, Authentic_Media_Sources.csv, YouTube_Footage_Sources.csv
from src/data/timeline.json + sources.py.  usage: make_deliverables.py <out_dir>"""
import csv, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from sources import SOURCES, REJECTED
from storyboard import S

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
tl = json.load(open(os.path.join(HERE, "..", "src", "data", "timeline.json")))
FPS = tl["fps"]

def ts(t, sep=","):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{int(s):02d}{sep}{int(round((s - int(s)) * 1000)) % 1000:03d}"

with open(os.path.join(OUT, "Subtitles.srt"), "w", encoding="utf-8") as f:
    for i, s in enumerate(tl["subs"], 1):
        f.write(f"{i}\n{ts(s['start'])} --> {ts(s['end'])}\n{s['text']}\n\n")

by_scene = {}
for sh in tl["shots"]:
    by_scene.setdefault(sh["scene"], []).append(sh)

with open(os.path.join(OUT, "Storyboard.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["scene", "audio_start", "audio_end", "original_narration_uz", "shot", "video_in", "video_out",
                "source_id", "source_channel", "source_in_sec", "on_screen_caption", "lower_third", "graphics", "camera_move", "transition"])
    for sc in tl["scenes"]:
        gfx = ", ".join(k for k in sc["extras"].keys())
        for sh in by_scene[sc["i"]]:
            w.writerow([sc["i"], ts(sc["start"], "."), ts(sc["end"], "."), sc["text"], sh["idx"],
                        ts(sh["from"] / FPS, "."), ts((sh["from"] + sh["dur"]) / FPS, "."),
                        sh["src"], SOURCES[sh["src"]]["channel"], sh["t_used"], sh["label"] or "",
                        " / ".join(sh["lt"]) if sh["lt"] else "", gfx,
                        "freeze + Ken Burns" if sh.get("freeze") else ("slow push-in" if sh["idx"] % 2 == 0 else "slow pull-out"),
                        "12-frame cross-dissolve"])

uses = {}
for sh in tl["shots"]:
    uses.setdefault(sh["src"], []).append(sh)

with open(os.path.join(OUT, "Authentic_Media_Sources.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["person_or_event", "source_url", "media_type", "authenticity_check", "rights_basis", "used_in_video_timestamps"])
    for sid, info in SOURCES.items():
        if sid not in uses: continue
        tss = "; ".join(f"{ts(s['from']/FPS,'.')}-{ts((s['from']+s['dur'])/FPS,'.')} (src {s['t_used']}s)" for s in uses[sid])
        w.writerow([info["about"], f"https://www.youtube.com/watch?v={sid}",
                    {"archive": "archival film/photo (via YouTube)", "interview": "interview video", "location": "location video", "event": "film/book/event video"}[info["kind"]],
                    "Frame-by-frame contact-sheet review; person/event/place matched to narration; source title/channel cross-checked",
                    "Not licensed - short excerpts used under user's fair-use instruction (commentary/documentary); owner permission NOT obtained", tss])

with open(os.path.join(OUT, "YouTube_Footage_Sources.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["youtube_url", "video_title", "channel", "related_person_or_event", "authenticity_status", "license_status",
                "download_status", "excerpts_used", "total_seconds_used", "used_in_video_timestamps"])
    for sid, info in SOURCES.items():
        u = uses.get(sid, [])
        secs = round(sum(s["dur"] for s in u) / FPS, 1)
        w.writerow([f"https://www.youtube.com/watch?v={sid}", info["title"], info["channel"], info["about"],
                    "verified (frame review)", "standard YouTube licence - no reuse licence; fair-use excerpts per user instruction",
                    "downloaded via snapyt.app", len(u), secs,
                    "; ".join(f"{ts(s['from']/FPS,'.')}" for s in u)])
    for sid, why in REJECTED.items():
        w.writerow([f"https://www.youtube.com/watch?v={sid}", "", "", "", "REJECTED: " + why, "", "", 0, 0, ""])
print("ok", len(tl["subs"]), "subs;", len(tl["shots"]), "shots;", len(uses), "sources used")
