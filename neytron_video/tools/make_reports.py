"""Generate Storyboard.csv, Authentic_Media_Sources.csv, YouTube_Footage_Sources.csv and
YouTube_Description_Sources.txt from the storyboard, so the reports always match the edit."""
import csv, json, re, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "deliverables")
OFF = 0.5  # narration offset in the video

sb = open(os.path.join(ROOT, "src/data/storyboard.ts"), encoding="utf-8").read()
src_ts = open(os.path.join(ROOT, "src/data/sources.ts"), encoding="utf-8").read()
cues = json.loads(re.search(r"export const CUES: Cue\[\] = (.*);\s*$", open(os.path.join(ROOT, "src/data/subtitles.ts"), encoding="utf-8").read(), re.S).group(1))

SRC = {k: (l, lic) for k, l, lic in re.findall(r"  (\w+): \{label: '([^']+)', license: '([^']+)'\}", src_ts)}

# Every media file used, with its verified origin.
MEDIA = {
    "vost_close.jpg": ("Kim Chen In (Kim Jong-un)", "https://en.kremlin.ru/events/president/news/72264", "Kremlin.ru — Visit to Vostochny Cosmodrome, 13.09.2023", "CC BY 4.0", "Photo published by the Russian Presidential Press Office at the event; face visually checked"),
    "vost_car.jpg": ("Kim Chen In (Kim Jong-un)", "https://en.kremlin.ru/events/president/news/72264", "Kremlin.ru — Visit to Vostochny Cosmodrome, 13.09.2023", "CC BY 4.0", "Official event gallery; visually checked"),
    "vost_crowd.jpg": ("Kim Chen In (Kim Jong-un)", "https://en.kremlin.ru/events/president/news/72264", "Kremlin.ru — Visit to Vostochny Cosmodrome, 13.09.2023", "CC BY 4.0", "Official event gallery; visually checked"),
    "vost_greet.jpg": ("Kim Chen In (Kim Jong-un)", "https://en.kremlin.ru/events/president/news/72264", "Kremlin.ru — Visit to Vostochny Cosmodrome, 13.09.2023", "CC BY 4.0", "Official event gallery; visually checked"),
    "kim_jong_un_portrait.jpg": ("Kim Chen In (Kim Jong-un)", "https://en.kremlin.ru/events/president/news/72264", "Kremlin.ru — Visit to Vostochny Cosmodrome, 13.09.2023", "CC BY 4.0", "Used in family tree; visually checked"),
    "kim_putin_2019.jpg": ("Kim Chen In (Kim Jong-un)", "https://commons.wikimedia.org/wiki/File:Kim_Jong-un_and_Vladimir_Putin_(2019-04-25)_01.jpg", "Alexei Nikolsky, Presidential Press and Information Office (Kremlin.ru), Vladivostok 25.04.2019", "CC BY 4.0", "Commons file description + visual check"),
    "kim_il_sung_1950.jpg": ("Kim Ir Sen (Kim Il-sung)", "https://commons.wikimedia.org/wiki/File:Kim_Il-sung_in_1950.jpg", "Unknown author, c. 1950", "Public domain", "Commons file description + visual check"),
    "kim_il_sung.jpg": ("Kim Ir Sen (Kim Il-sung)", "https://commons.wikimedia.org/wiki/File:Kim_Il-sung_in_1950.jpg", "Unknown author, c. 1950 (family tree)", "Public domain", "Same file as above"),
    "kim_il_sung_1946.jpg": ("Kim Ir Sen (Kim Il-sung)", "https://commons.wikimedia.org/wiki/File:Kim-Il-sung_%EA%B9%80%EC%9D%BC%EC%84%B1_19461103election.jpg", "Rally speech for 3 Nov 1946 elections (publ. 1948)", "Public domain", "Commons description: Kim Il-Sung speaks at a rally for the 1946 local elections"),
    "f1948_podium.jpg": ("Kim Ir Sen (Kim Il-sung)", "https://commons.wikimedia.org/wiki/File:South%E2%80%93North_Meeting_(1948)_%E2%80%93_Speech_of_Kim_Il_Sung.webm", "North Korean National Film Studio, 1948 — frame at 0:16", "Public domain", "Archive film of Kim Il-sung's speech, frame extracted via Commons"),
    "kim_jong_il_2011.jpg": ("Kim Chen Ir (Kim Jong-il)", "https://commons.wikimedia.org/wiki/File:Kim_Jong-il_on_August_24,_2011.jpg", "Presidential Press and Information Office (Kremlin.ru), Ulan-Ude 24.08.2011", "CC BY 4.0", "Commons description + visual check"),
    "kim_jong_il.jpg": ("Kim Chen Ir (Kim Jong-il)", "https://commons.wikimedia.org/wiki/File:Kim_Jong-il_on_August_24,_2011.jpg", "Kremlin.ru 2011 (family tree)", "CC BY 4.0", "Same file as above"),
    "kim_yo_jong.jpg": ("Kim Yo Jong", "https://commons.wikimedia.org/wiki/File:Kim_Yo-jong_(2018).png", "Munhwa Broadcasting Corporation (MBC), 2018 — video frame", "CC BY 3.0", "Commons description; source YouTube https://www.youtube.com/watch?v=9Ah94vb39S0"),
    "sgp_handshake.jpg": ("Kim Chen In & Donald Trump — Singapore summit", "https://commons.wikimedia.org/wiki/File:2018_Singapore_Summit.webm", "The White House, 12.06.2018 — frame at 0:07", "Public domain (US Government work)", "Original: https://www.youtube.com/watch?v=-s8pYz_KIdc"),
    "sgp_walk.jpg": ("Kim Chen In & Donald Trump — Singapore summit", "https://commons.wikimedia.org/wiki/File:2018_Singapore_Summit.webm", "The White House, 12.06.2018 — frame at 0:31", "Public domain (US Government work)", "Original: https://www.youtube.com/watch?v=-s8pYz_KIdc"),
    "dmz_handshake.jpg": ("Kim Chen In & Donald Trump — DMZ meeting", "https://commons.wikimedia.org/wiki/File:President_Trump_meets_Chairman_Kim_at_the_DMZ.webm", "The White House, 30.06.2019 — frame at 0:06", "Public domain (US Government work)", "Original: https://www.youtube.com/watch?v=fce_EqxOiyk"),
    "klia2_aerial.jpg": ("KLIA2 terminal (location of the attack)", "https://commons.wikimedia.org/wiki/File:View_Over_KLIA2.jpg", "Jason Thien, 2015", "CC BY 2.0", "Commons description: aerial view of KLIA2"),
    "klia2_terminal.jpg": ("KLIA2 terminal", "https://commons.wikimedia.org/wiki/File:Kuala_Lumpur_International_Airport_Terminal_2_(KLIA2).jpg", "Zhou Guanhuai, 2019", "CC BY-SA 4.0", "klia2 signage visible in frame"),
    "klia2_checkin.jpg": ("KLIA2 self check-in hall", "https://commons.wikimedia.org/wiki/File:KLIA2_self-check-in_terminals_2016_September.jpg", "Morio, Sept 2016", "CC BY-SA 4.0", "Self check-in kiosks of KLIA2 (attack occurred in this departure hall area)"),
    "opcw.jpg": ("OPCW (Chemical Weapons Convention)", "https://commons.wikimedia.org/wiki/File:Organisation_for_the_Prohibition_of_Chemical_Weapons_The_Hague.jpg", "Steven Lek, 2018", "CC BY-SA 4.0", "OPCW headquarters, The Hague"),
    "disneyland.jpg": ("Tokyo Disneyland", "https://commons.wikimedia.org/wiki/File:Tokyo_Disneyland_Main_Entrance.jpg", "ARICA, 2006", "CC BY-SA 3.0", "Main entrance of Tokyo Disneyland"),
    "macau.jpg": ("Makao (Macau)", "https://commons.wikimedia.org/wiki/File:Macau_skyline_2013.JPG", "Mimihitam, 2013", "CC BY-SA 3.0", "Macau skyline from Taipa"),
    "kumsusan.jpg": ("Kumsusan Palace of the Sun, Pyongyang", "https://commons.wikimedia.org/wiki/File:Kumsusan_Memorial_Palace,_Pyongyang.jpg", "Mark Scott Johnson, 2008", "CC BY 2.0", "Mausoleum of Kim Il-sung and Kim Jong-il"),
    "id_letter.jpg": ("Siti Aisyah — release request", "https://commons.wikimedia.org/wiki/File:Indonesian_Government_Letter_to_Malaysian_Government_for_the_Release_of_Siti_Aisyah.jpg", "Government of Indonesia, March 2019", "Public domain", "Letter names Siti Aisyah and Kim Jong Nam"),
}


def ts(x):
    x = max(0, x)
    return f"{int(x // 60):02d}:{x % 60:05.2f}"


def spoken(a, b):
    return " ".join(w["t"] for c in cues for w in c["w"] if a <= w["s"] < b)


rows = []
for line in sb.splitlines():
    m = re.match(r"\s*\{start: ([\d.]+), end: ([\d.]+), v: \{kind: '(\w+)'(.*)", line)
    if not m:
        continue
    a, b, kind, rest = float(m.group(1)), float(m.group(2)), m.group(3), m.group(4)
    f = re.search(r"file: 'media/([^']+)'", rest)
    files = re.findall(r"file: 'media/([^']+)'", rest)
    src = re.search(r"source: SRC\.(\w+)", rest)
    srci = re.search(r"source: \{label: '([^']+)', license: '([^']+)'\}", rest)
    label = (SRC[src.group(1)][0] + " · " + SRC[src.group(1)][1]) if src else (srci.group(1) + " · " + srci.group(2) if srci else "")
    lower = re.search(r"lower: \{name: '([^']+)', role: '([^']+)'\}", rest)
    note = re.search(r"note: '((?:[^'\\]|\\.)*)'", rest)
    move = re.search(r"move: \{([^}]*)\}", rest)
    title = re.search(r"title: '([^']+)'", rest)
    rows.append(dict(a=a, b=b, kind=kind, files=files, label=label, lower=lower.groups() if lower else None, note=note.group(1) if note else "", move=move.group(1) if move else "", title=title.group(1) if title else ""))

os.makedirs(OUT, exist_ok=True)
anim = {"photo": "Ken Burns / 2.5D camera move", "video": "Short clip", "map": "Animated Natural Earth map, pins + arcs", "card": "Kinetic typography title card", "date": "Typewriter date card", "tree": "Animated family tree (real portraits where licensed)", "timeline": "Animated timeline", "question": "Staggered question reveal", "split": "Split-screen comparison", "molecule": "Animated VX molecule (original graphic)", "cctv": "Labelled schematic reconstruction", "stat": "Counter"}
with open(os.path.join(OUT, "Storyboard.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["#", "Video start", "Video end", "Narration start (s)", "Duration (s)", "Original narration (corrected Uzbek)", "Visual type", "Media file(s)", "Subject shown", "On-screen source label", "Lower third", "Animation / camera", "Transition", "Why this visual"])
    for i, r in enumerate(rows, 1):
        subj = "; ".join(MEDIA[f][0] for f in r["files"] if f in MEDIA) or (r["title"] or "graphic")
        w.writerow([i, ts(r["a"] + OFF), ts(r["b"] + OFF), r["a"], round(r["b"] - r["a"], 2), spoken(r["a"], r["b"]), r["kind"], " ".join(r["files"]), subj, r["label"], " — ".join(r["lower"]) if r["lower"] else "", anim.get(r["kind"], "") + (f" ({r['move']})" if r["move"] else ""), "10-frame cross-dissolve" + (" + whoosh" if r["kind"] in ("card", "date", "question", "map", "tree", "timeline") else ""), r["note"]])

used = {}
for r in rows:
    for f in r["files"]:
        used.setdefault(f, []).append(f"{ts(r['a'] + OFF)}–{ts(r['b'] + OFF)}")
# tree portraits
tree_ranges = [f"{ts(r['a'] + OFF)}–{ts(r['b'] + OFF)}" for r in rows if r["kind"] == "tree"]
for f in ("kim_il_sung.jpg", "kim_jong_il.jpg", "kim_jong_un_portrait.jpg", "kim_yo_jong.jpg"):
    used.setdefault(f, []).extend(tree_ranges)
for f in ("kim_il_sung_1950.jpg", "kim_jong_il_2011.jpg"):
    used[f] = used.get(f, []) + [f"{ts(r['a'] + OFF)}–{ts(r['b'] + OFF)} (split)" for r in rows if r["kind"] == "split"]

with open(os.path.join(OUT, "Authentic_Media_Sources.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["Person / event / place", "Original source URL", "Media type", "Author / publisher", "Authenticity evidence", "License / right of use", "Used in video (timestamps)", "Local file"])
    for f, times in sorted(used.items()):
        if f not in MEDIA:
            continue
        subj, url, auth, lic, ev = MEDIA[f]
        typ = "Video frame (still)" if f.startswith(("sgp_", "dmz_", "f1948_")) else "Photograph"
        if f == "id_letter.jpg":
            typ = "Document (scan)"
        w.writerow([subj, url, typ, auth, ev, lic, "; ".join(dict.fromkeys(times)), "public/media/" + f])
    w.writerow(["World map (Malaysia, Korea, Japan, Macau)", "https://www.naturalearthdata.com/", "Map data", "Natural Earth", "Standard reference dataset", "Public domain", "map scenes", "node_modules/world-atlas"])
    w.writerow(["Background music / sound design", "tools/score.py", "Audio", "Synthesized for this video", "Original work", "Original — no third-party rights", "whole video", "public/audio/mix.wav"])

yt = [
    ("https://www.youtube.com/watch?v=-s8pYz_KIdc", "The White House (Trump White House Archived)", "2018 Singapore Summit", "0:07 and 0:31", "sgp_handshake.jpg", "sgp_walk.jpg"),
    ("https://www.youtube.com/watch?v=fce_EqxOiyk", "The White House (Trump White House Archived)", "President Trump meets Chairman Kim at the DMZ", "0:06", "dmz_handshake.jpg", None),
    ("https://www.youtube.com/watch?v=9Ah94vb39S0", "MBC (Munhwa Broadcasting Corporation)", "MBC PD수첩 segment (Kim Yo-jong portrait frame)", "frame as cropped on Commons", "kim_yo_jong.jpg", None),
]
with open(os.path.join(OUT, "YouTube_Footage_Sources.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["Original YouTube URL", "Channel", "Video title", "Original video timestamp", "Final video timestamp", "Segment duration", "Authenticity status", "License / Fair Use assessment", "Download method", "On-screen source label"])
    for url, ch, title, ots, f1, f2 in yt:
        times = used.get(f1, []) + (used.get(f2, []) if f2 else [])
        dur = sum((lambda p: (lambda a, b: b - a)(*[int(x.split(":")[0]) * 60 + float(x.split(":")[1]) for x in p.split(" ")[0].split("–")]))(t) for t in dict.fromkeys(times) if "–" in t)
        lic = "Public domain (US federal government work, 17 U.S.C. §105) — no Fair Use needed" if "White House" in ch else "CC BY 3.0 (as published on Wikimedia Commons) — attribution given; no Fair Use needed"
        w.writerow([url, ch, title, ots, "; ".join(dict.fromkeys(times)), f"{dur:.1f}s on screen as still frame(s)", "Verified: official channel; subject identified visually", lic, "NOT downloaded from YouTube. Single frames obtained from the Wikimedia Commons mirror (commons.wikimedia.org/w/thumb.php). snapyt.app not used (YouTube Terms of Service).", "Manba: The White House (…), video kadri / Wikimedia Commons · Public domain" if "White House" in ch else "Portretlar: … MBC (CC BY 3.0)"])

with open(os.path.join(OUT, "YouTube_Description_Sources.txt"), "w", encoding="utf-8") as fh:
    fh.write("VIDEO MANBALARI / FOOTAGE SOURCES\n\n")
    fh.write("Ushbu hujjatli videoda faqat jamoat mulki (public domain) yoki ochiq litsenziyali (CC BY / CC BY-SA) materiallar ishlatilgan.\n")
    fh.write("Grafik rekonstruksiyalar, xaritalar va oila daraxti — illyustratsiya, arxiv kadri emas.\n\n")
    seen = set()
    for f in sorted(used):
        if f not in MEDIA:
            continue
        subj, url, auth, lic, _ = MEDIA[f]
        if url in seen:
            continue
        seen.add(url)
        fh.write(f"• {subj} — {auth} — {lic}\n  {url}\n")
    fh.write("\nAsl YouTube videolari (kadrlar Wikimedia Commons orqali olingan):\n")
    for url, ch, title, *_ in yt:
        fh.write(f"• {title} — {ch}\n  {url}\n")
    fh.write("\nXarita ma’lumotlari: Natural Earth (public domain) — https://www.naturalearthdata.com/\n")
    fh.write("Musiqa: ushbu video uchun yaratilgan original partitura.\n")
    fh.write("Ovoz: muallifning original ovozi (o‘zgartirilmagan).\n")
print(len(rows), "scenes,", len(used), "media files")
