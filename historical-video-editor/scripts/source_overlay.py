#!/usr/bin/env python3
"""Step 13: build the on-screen text layer as an ASS subtitle file (rendered by
libass in the final pass):

  * Source credits — small, bottom-right/left, soft fade in/out, shown exactly while
    the asset is on screen ("Source: Internet Archive", "Manba: Wikimedia Commons" ...)
  * Lower thirds — name + dates/role of historical persons, animated slide + fade
  * Date cards — kinetic typography (tracking/scale animation) for key years
  * Chapter titles — centred serif title with animated letter spacing
  * Narration subtitles (burned-in) — optional; an .srt is always exported too

Style values come from config.yaml -> overlay and templates/source_overlay.json.

Usage: python scripts/source_overlay.py --project <slug>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import SKILL_ROOT, load_config, log, project_dir, read_json, setup_logging  # noqa: E402


def ass_time(t: float) -> str:
    t = max(0.0, t)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def srt_time(t: float) -> str:
    t = max(0.0, t)
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{(ms // 60000) % 60:02d}:{(ms // 1000) % 60:02d},{ms % 1000:03d}"


def esc(text: str) -> str:
    return text.replace("{", "(").replace("}", ")").replace("\n", "\\N")


def alpha_hex(opacity: float) -> str:
    return f"{int(round((1 - opacity) * 255)):02X}"


def load_style_template() -> dict:
    p = SKILL_ROOT / "templates" / "source_overlay.json"
    return read_json(p) if p.exists() else {}


def build_ass(tl: dict, cfg: dict) -> str:
    W, H = tl["settings"]["width"], tl["settings"]["height"]
    o = cfg["overlay"]
    k = H / 1080.0
    tpl = load_style_template().get("styles", {})
    font = o.get("font", "DejaVu Sans")
    serif = o.get("title_font", "DejaVu Serif")
    m = int(o["source_margin_px"] * k)
    a_src = alpha_hex(o.get("source_opacity", 0.85))
    align_src = 3 if o.get("source_position", "bottom_right") == "bottom_right" else 1
    styles = [
        # Name, Font, Size, Primary, Secondary, Outline, Back, Bold, Italic, Underline, Strike, ScaleX, ScaleY,
        # Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
        ("Credit", font, int(o["source_font_size"] * k), f"&H{a_src}F2F2F2", "&H000000FF", "&H90000000", "&HA0000000",
         0, 0, 0, 0, 100, 100, 0.5, 0, 1, 1.2 * k, 0.6 * k, align_src, m, m, int(m * 0.75)),
        ("Subtitle", font, int(o["subtitle_font_size"] * k), "&H00FFFFFF", "&H000000FF", "&H00101010", "&H80000000",
         0, 0, 0, 0, 100, 100, 0, 0, 1, 2.6 * k, 1.0 * k, 2, int(160 * k), int(160 * k), int(92 * k)),
        ("LTTitle", font, int(o["lower_third_font_size"] * k), "&H00FFFFFF", "&H000000FF", "&H00000000", "&H00000000",
         1, 0, 0, 0, 100, 100, 1, 0, 1, 0, 1.5 * k, 1, int(110 * k), int(110 * k), int(190 * k)),
        ("LTSub", font, int(o["lower_third_font_size"] * 0.62 * k), "&H00C8D7E6", "&H000000FF", "&H00000000", "&H00000000",
         0, 0, 0, 0, 100, 100, 2, 0, 1, 0, 1.0 * k, 1, int(112 * k), int(110 * k), int(150 * k)),
        ("DateCard", serif, int(150 * k), "&H00F0F6FA", "&H000000FF", "&H00000000", "&H60000000",
         1, 0, 0, 0, 100, 100, 18, 0, 1, 0, 3 * k, 5, 0, 0, 0),
        ("Chapter", serif, int(84 * k), "&H00FFFFFF", "&H000000FF", "&H00000000", "&H70000000",
         0, 0, 0, 0, 100, 100, 6, 0, 1, 0, 2.5 * k, 5, int(120 * k), int(120 * k), 0),
        ("Bar", font, 10, "&H30FFFFFF", "&H000000FF", "&H00000000", "&H00000000",
         0, 0, 0, 0, 100, 100, 0, 0, 1, 0, 0, 7, 0, 0, 0),
    ]
    for name, override in tpl.items():  # template overrides (colours, sizes)
        for i, s in enumerate(styles):
            if s[0] == name:
                scaled = {"Fontsize", "Outline", "Shadow", "MarginL", "MarginR", "MarginV"}  # template is for 1080p
                styles[i] = tuple((round(override[f] * k, 2) if f in scaled else override[f])
                                  if isinstance(override, dict) and f in override else v
                                  for f, v in zip(STYLE_FIELDS, s))
    lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 0",
             "ScaledBorderAndShadow: yes", "YCbCr Matrix: TV.709", "", "[V4+ Styles]",
             "Format: " + ", ".join(STYLE_FIELDS + ["Encoding"])]
    for s in styles:
        lines.append("Style: " + ",".join(str(round(x, 2)) if isinstance(x, float) else str(x) for x in s) + ",1")
    lines += ["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    fade = int(o.get("source_fade_sec", 0.4) * 1000)

    def ev(layer, s, e, style, text):
        lines.append(f"Dialogue: {layer},{ass_time(s)},{ass_time(e)},{style},,0,0,0,,{text}")

    for ov in tl["overlays"]:
        s, e = ov["start"], ov["end"]
        if e - s < 0.4:
            continue
        if ov["type"] == "credit":
            ev(5, s + 0.25, e - 0.1, "Credit", f"{{\\fad({fade},{fade})}}{esc(ov['text'])}")
        elif ov["type"] == "lower_third":
            x0, y_t, y_s = int(110 * k), H - int(318 * k), H - int(276 * k)
            bar_w, bar_h = int(8 * k), int(96 * k)
            # accent bar grows, title slides in from left, subtitle fades
            ev(3, s, e, "Bar", f"{{\\an7\\pos({x0 - int(28 * k)},{H - int(378 * k)})\\fad(250,300)\\c&H2FA8E8&\\fscy0\\t(0,350,\\fscy100)\\p1}}"
                               f"m 0 0 l {bar_w} 0 {bar_w} {bar_h} 0 {bar_h}{{\\p0}}")
            ev(4, s + 0.15, e, "LTTitle", f"{{\\an1\\move({x0 - int(40 * k)},{y_t},{x0},{y_t},0,450)\\fad(350,300)}}{esc(ov['title'])}")
            if ov.get("subtitle"):
                ev(4, s + 0.45, e, "LTSub", f"{{\\an1\\pos({x0},{y_s})\\fad(400,300)}}{esc(ov['subtitle'])}")
        elif ov["type"] == "date_card":
            cx, cy = W // 2, int(H * 0.36)
            ev(6, s, e, "DateCard", f"{{\\an5\\pos({cx},{cy})\\fad(250,400)\\fscx118\\fscy118\\fsp40"
                                    f"\\t(0,900,0.6,\\fscx100\\fscy100\\fsp18)}}{esc(ov['text'])}")
        elif ov["type"] == "chapter_title":
            cx, cy = W // 2, int(H * 0.5)
            ev(6, s, e, "Chapter", f"{{\\an5\\pos({cx},{cy})\\fad(500,500)\\fsp22\\t(0,1800,0.5,\\fsp6)}}{esc(ov['text'].upper())}")
    if cfg["overlay"].get("subtitles", True):
        for sub in tl.get("subtitles", []):
            ev(2, sub["start"], sub["end"], "Subtitle", esc(sub["text"]).replace("\\\\N", "\\N"))
    return "\n".join(lines) + "\n"


STYLE_FIELDS = ["Name", "Fontname", "Fontsize", "PrimaryColour", "SecondaryColour", "OutlineColour", "BackColour",
                "Bold", "Italic", "Underline", "StrikeOut", "ScaleX", "ScaleY", "Spacing", "Angle", "BorderStyle",
                "Outline", "Shadow", "Alignment", "MarginL", "MarginR", "MarginV", "Encoding"][:22]

def build_srt(tl: dict) -> str:
    out = []
    for i, s in enumerate(tl.get("subtitles", []), 1):
        out += [str(i), f"{srt_time(s['start'])} --> {srt_time(s['end'])}", s["text"].replace("\\N", "\n"), ""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--no-subtitles", action="store_true", help="do not burn narration subtitles")
    ap.add_argument("--config")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    setup_logging(a.verbose)
    cfg = load_config(a.config)
    if a.no_subtitles:
        cfg["overlay"]["subtitles"] = False
    pdir = project_dir(cfg, a.project)
    tl = read_json(pdir / "timeline.json")
    ass = build_ass(tl, cfg)
    (pdir / "render" / "overlays.ass").write_text(ass, encoding="utf-8")
    (pdir / "render" / "subtitles.srt").write_text(build_srt(tl), encoding="utf-8")
    n = sum(1 for o in tl["overlays"] if o["type"] == "credit")
    log.info("overlays: %d credits, %d other, %d subtitle lines", n, len(tl["overlays"]) - n, len(tl.get("subtitles", [])))
    print(pdir / "render" / "overlays.ass")


if __name__ == "__main__":
    main()
