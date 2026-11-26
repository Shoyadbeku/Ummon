
from analyze_script import analyse
from scene_builder import build, snap_to_beats, subtitle_lines
from source_overlay import build_ass

SCRIPT = "# A\nSamarqand shahri. 1370-yilda Amir Temur hukmdor bo'ldi va poytaxt qurdi.\n\n# B\nBuxoro va Xiva orqali karvonlar o'tdi. Cho'lda shamol esardi va karvon yurardi.\n"


def fake_index(sb):
    assets = []
    for i, s in enumerate(sb["scenes"]):
        for k in range(3):
            assets.append({"asset_id": f"v{i}{k}", "scene_id": s["id"], "media_type": "video", "path": f"/x/v{i}{k}.mp4",
                           "width": 1280, "height": 720, "duration": 20.0, "has_audio": True, "src_in": 0.0, "cuts": [6.0, 12.5],
                           "meta": {"title": "clip", "source_label": "Internet Archive", "license": {"risk": 0, "label": "Public Domain", "code": "pd"},
                                    "page_url": "https://archive.org/details/x", "archival": True}})
        assets.append({"asset_id": f"i{i}", "scene_id": s["id"], "media_type": "image", "path": f"/x/i{i}.jpg",
                       "width": 2000, "height": 1500, "duration": 0,
                       "meta": {"title": "painting", "source_label": "Wikimedia Commons", "license": {"risk": 0, "label": "Public Domain", "code": "pd"},
                                "page_url": "https://commons.wikimedia.org/wiki/File:x.jpg"}})
    return {"assets": assets}


def test_build_timeline(cfg):
    sb = analyse(SCRIPT, "Test", cfg, duration=40)
    tl = build(sb, fake_index(sb), cfg, beats=[])
    clips = tl["clips"]
    # contiguous, covers the whole narration
    assert abs(clips[0]["start"]) < 1e-6
    for a, b in zip(clips, clips[1:]):
        assert abs(a["start"] + a["duration"] - b["start"]) < 0.01
    assert abs(clips[-1]["start"] + clips[-1]["duration"] - tl["total_duration"]) < 0.01
    # no overlapping reuse of the same footage
    used = {}
    for c in clips:
        if c.get("kind") == "video":
            for r in used.get(c["asset_id"], []):
                assert c["out_point"] <= r[0] + 1e-6 or c["in_point"] >= r[1] - 1e-6
            used.setdefault(c["asset_id"], []).append((c["in_point"], c["out_point"]))
    # every clip with third-party media has a credit overlay covering it
    credits = [o for o in tl["overlays"] if o["type"] == "credit"]
    for c in clips:
        if c.get("asset_id"):
            assert any(o["start"] <= c["start"] + 0.01 and o["end"] >= c["start"] + c["duration"] - 0.01 for o in credits)
    # chapter change -> fade to black
    assert any(c["transition_in"]["type"] == "fadeblack" for c in clips)
    # lower third for Amir Temur
    assert any(o["type"] == "lower_third" for o in tl["overlays"])


def test_ass_output(cfg):
    sb = analyse(SCRIPT, "Test", cfg, duration=40)
    tl = build(sb, fake_index(sb), cfg, beats=[])
    ass = build_ass(tl, cfg)
    fmt = [l for l in ass.splitlines() if l.startswith("Format: Name")][0]
    nf = len(fmt.split(","))
    for l in ass.splitlines():
        if l.startswith("Style: "):
            assert len(l.split(",")) == nf
    assert "Source: Internet Archive" in ass or "Arxiv kadrlari: Internet Archive" in ass or "Manba:" in ass
    assert "\\fad(" in ass


def test_snap_and_subtitles():
    assert snap_to_beats([1.0, 2.9], [0.0, 0.5, 1.1, 3.5], 0.35) == [1.1, 2.9]
    subs = subtitle_lines("Bir ikki uch to'rt besh olti yetti sakkiz to'qqiz o'n. " * 4, 10.0, 8.0)
    assert subs[0]["start"] == 10.0 and subs[-1]["end"] <= 18.0
