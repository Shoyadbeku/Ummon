#!/usr/bin/env python3
"""Step 12: render timeline.json into a picture-only master (render/assembled.mp4).

Per clip (render/segments/*.mp4, identical codec params so they concat losslessly):
  video  -> trim on detected shot boundaries, cover-crop 16:9, or for 4:3 / portrait archive
            film a blurred-background pillarbox; optional smooth zoom; gentle slow-motion
            when a shot is shorter than needed; frame-hold padding as last resort
  image  -> Ken Burns (eased zoom + pan, oversampled to avoid jitter), pseudo-parallax
            (blurred moving background + floating foreground), map zoom
  map    -> procedural schematic map with animated route (motion_graphics.py)
  card   -> textured title card (fallback when no licensed visual exists)
Transitions
  cut, impact (white flash + zoom punch), fadeblack (fade out/in), dissolve (xfade groups)

Global look (grade, grain, vignette, letterbox) and text overlays are applied in
export_video.py in a single final encode.

Usage: python scripts/video_editor.py --project <slug> [--preview] [--jobs 3]
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import find_font, load_config, log, media_info, project_dir, read_json, run, setup_logging, write_json  # noqa: E402
import motion_graphics as mg  # noqa: E402

LEX = None


def enc_args(cfg: dict, preview: bool) -> list[str]:
    fps = cfg["render"]["fps"]
    return ["-an", "-c:v", "libx264", "-preset", "ultrafast" if preview else "veryfast", "-crf", "20" if preview else "15",
            "-pix_fmt", "yuv420p", "-r", str(fps), "-g", str(fps), "-bf", "0",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-video_track_timescale", "90000"]


def fill_chain(W: int, H: int, src_w: int, src_h: int) -> str:
    """Filter to fit any source into WxH. Wide -> cover crop; narrow -> blurred pillarbox."""
    ar = (src_w / src_h) if src_w and src_h else 16 / 9
    if ar >= 1.6:
        return f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1"
    return (f"split=2[bgsrc][fgsrc];[bgsrc]scale={W // 4}:{H // 4}:force_original_aspect_ratio=increase,crop={W // 4}:{H // 4},"
            f"boxblur=8:2,scale={W}:{H},eq=brightness=-0.10:saturation=0.7[bg];"
            f"[fgsrc]scale=-2:{H}:flags=lanczos,setsar=1[fg];[bg][fg]overlay=(W-w)/2:0,setsar=1")


def zoom_expr(z0: float, z1: float, D: float) -> str:
    # smoothstep eased zoom factor as ffmpeg expression of t
    p = f"min(1,max(0,t/{D:.3f}))"
    return f"({z0}+({z1}-{z0})*({p}*{p}*(3-2*{p})))"


def kb_filter(W: int, H: int, img_w: int, img_h: int, D: float, eff: dict) -> str:
    """Ken Burns with 2x oversampling: scale (eval=frame) then crop with eased pan, then downscale."""
    OW, OH = W * 2, H * 2
    cover = max(OW / img_w, OH / img_h)
    bw, bh = img_w * cover, img_h * cover
    z = float(eff.get("zoom", 1.12))
    direction = eff.get("direction", "in")
    z0, z1 = (1.0, z) if direction in ("in", "left", "right", "up") else (z, 1.0)
    if eff.get("type") == "map_zoom":
        z0, z1 = 1.0, max(z, 1.25)
    ze = zoom_expr(z0, z1, D)
    p = f"(min(1,max(0,t/{D:.3f})))"
    px = {"left": f"(1-{p})", "right": p}.get(direction, "0.5")
    py = {"up": f"(1-{p}*0.6)"}.get(direction, "0.5")
    return (f"scale=w='trunc({bw:.1f}*{ze}/2)*2':h='trunc({bh:.1f}*{ze}/2)*2':eval=frame:flags=bicubic,"
            f"crop={OW}:{OH}:x='(iw-{OW})*{px}':y='(ih-{OH})*{py}',scale={W}:{H}:flags=lanczos,setsar=1")


def parallax_filter(W: int, H: int, img_w: int, img_h: int, D: float) -> str:
    """Pseudo-parallax: blurred background drifts left, sharp foreground drifts right & grows."""
    p = f"(min(1,max(0,t/{D:.3f})))"
    bgw = int(W * 1.25)
    bgh = int(H * 1.25)
    fg_h = int(H * 0.86)
    fg_w = int(img_w * fg_h / img_h) // 2 * 2
    if fg_w > W * 0.92:
        fg_w = int(W * 0.92) // 2 * 2
        fg_h = int(img_h * fg_w / img_w) // 2 * 2
    ze = zoom_expr(1.0, 1.06, D)
    return (f"split=2[a][b];[a]scale={bgw}:{bgh}:force_original_aspect_ratio=increase,crop={bgw}:{bgh},gblur=sigma=22,"
            f"eq=brightness=-0.12:saturation=0.75,crop={W}:{H}:x='({bgw}-{W})*(1-{p})':y='({bgh}-{H})/2'[bg];"
            f"[b]scale=w='trunc({fg_w}*{ze}/2)*2':h='trunc({fg_h}*{ze}/2)*2':eval=frame:flags=bicubic[fg];"
            f"[bg][fg]overlay=x='(W-w)/2-{W * 0.015:.1f}+{W * 0.03:.1f}*{p}':y='(H-h)/2',setsar=1")


def transition_filters(clip: dict, nxt: dict | None, D: float) -> str:
    f = []
    ti = clip.get("transition_in", {})
    if ti.get("type") == "fadeblack":
        f.append(f"fade=t=in:st=0:d={ti['duration'] / 2:.3f}")
    elif ti.get("type") == "impact":
        f.append(f"fade=t=in:st=0:d={max(0.08, ti['duration']):.3f}:color=white")
    if nxt and nxt.get("transition_in", {}).get("type") == "fadeblack":
        d = nxt["transition_in"]["duration"] / 2
        f.append(f"fade=t=out:st={max(0, D - d):.3f}:d={d:.3f}")
    return ",".join(f)


def render_clip(clip: dict, nxt: dict | None, extra_tail: float, cfg: dict, pdir: Path, preview: bool) -> Path:
    W, H, fps = cfg["render"]["width"], cfg["render"]["height"], cfg["render"]["fps"]
    D = round(clip["duration"] + extra_tail, 3)
    out = pdir / "render" / "segments" / f"{clip['id']}.mp4"
    font = find_font(cfg)
    serif = find_font(cfg, cfg["overlay"].get("title_font"))
    trans = transition_filters(clip, nxt, D)
    post = f",{trans}" if trans else ""
    tail = f"tpad=stop_mode=clone:stop_duration={D:.3f},trim=duration={D:.3f},fps={fps},format=yuv420p"
    kind = clip["kind"]
    if kind == "map":
        global LEX
        if LEX is None:
            from common import SKILL_ROOT
            LEX = read_json(SKILL_ROOT / "scripts" / "data" / "lexicon.json")
        lang = cfg["project"]["language"]
        places = []
        for p in clip.get("places", []):
            d = LEX["places"].get(p, {})
            places.append({"name": d.get(lang, p) if lang != "en" else p, "lat": d.get("lat"), "lon": d.get("lon")})
        raw = out.with_name(out.stem + "_raw.mp4")
        mg.render_map(raw, places, " — ".join(x["name"] for x in places[:3]), clip["credit"]["text"], D, W, H, fps,
                      font, serif, "ultrafast" if preview else "veryfast")
        src_filter = f"{tail}{post}"
        run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-vf", src_filter, *enc_args(cfg, preview), out])
        raw.unlink(missing_ok=True)
        return out
    if kind == "card":
        raw = out.with_name(out.stem + "_raw.mp4")
        mg.render_card(raw, clip.get("text", ""), "", D, W, H, fps, serif, font, "ultrafast" if preview else "veryfast")
        run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-vf", f"{tail}{post}", *enc_args(cfg, preview), out])
        raw.unlink(missing_ok=True)
        return out
    if kind == "image":
        eff = clip.get("effect", {})
        iw, ih = clip.get("width") or W, clip.get("height") or H
        if eff.get("type") == "parallax":
            core = parallax_filter(W, H, iw, ih, D)
        else:
            core = kb_filter(W, H, iw, ih, D, eff)
        fc = f"[0:v]format=rgb24,{core},{tail}{post}[v]"
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(fps), "-t", f"{D + 0.2:.3f}", "-i", clip["path"],
             "-filter_complex", fc, "-map", "[v]", "-t", f"{D:.3f}", *enc_args(cfg, preview), out], timeout=1800)
        return out
    # video
    speed = clip.get("speed", 1.0) or 1.0
    src_len = clip["out_point"] - clip["in_point"]
    iw, ih = clip.get("width") or 0, clip.get("height") or 0
    if not (iw and ih):
        info = media_info(clip["path"])
        iw, ih = info["width"], info["height"]
    chain = fill_chain(W, H, iw, ih)
    pre = f"setpts=(PTS-STARTPTS)/{speed:.4f}," if abs(speed - 1.0) > 0.01 else "setpts=PTS-STARTPTS,"
    zoom = ""
    if clip.get("effect", {}).get("type") == "smooth_zoom":
        ze = zoom_expr(1.0, 1.06, D)
        zoom = f",scale=w='trunc({W}*{ze}/2)*2':h='trunc({H}*{ze}/2)*2':eval=frame,crop={W}:{H},setsar=1"
    if clip.get("transition_in", {}).get("type") == "impact":
        ze = "(1+0.07*max(0,1-t/0.3))"
        zoom += f",scale=w='trunc({W}*{ze}/2)*2':h='trunc({H}*{ze}/2)*2':eval=frame,crop={W}:{H},setsar=1"
    fc = f"[0:v]{pre}{chain}{zoom},{tail}{post}[v]"
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{clip['in_point']:.3f}", "-t", f"{src_len + 0.5:.3f}", "-i", clip["path"],
         "-filter_complex", fc, "-map", "[v]", "-t", f"{D:.3f}", *enc_args(cfg, preview), out], timeout=1800)
    return out


def group_dissolves(clips: list[dict]) -> list[list[int]]:
    groups: list[list[int]] = []
    for i, c in enumerate(clips):
        if i > 0 and c.get("transition_in", {}).get("type") == "dissolve":
            groups[-1].append(i)
        else:
            groups.append([i])
    return groups


def xfade_group(files: list[Path], durs: list[float], T: float, out: Path, cfg: dict, preview: bool) -> Path:
    """durs are rendered durations (every clip except the last carries +T tail)."""
    inputs = []
    for f in files:
        inputs += ["-i", f]
    chain, last, offset = [], "[0:v]", 0.0
    for k in range(1, len(files)):
        offset += durs[k - 1] - T
        lab = f"[x{k}]"
        chain.append(f"{last}[{k}:v]xfade=transition=fade:duration={T:.3f}:offset={offset:.3f}{lab}")
        last = lab
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(chain), "-map", last,
         *enc_args(cfg, preview), out], timeout=3600)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--preview", action="store_true", help="fast low-res render (960x540, ultrafast)")
    ap.add_argument("--jobs", type=int, default=3, help="parallel segment renders")
    ap.add_argument("--only", help="comma separated clip ids to (re)render")
    ap.add_argument("--config")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    setup_logging(a.verbose)
    cfg = load_config(a.config)
    pdir = project_dir(cfg, a.project)
    tl = read_json(pdir / "timeline.json")
    if a.preview:
        cfg["render"].update(width=960, height=540)
    W, H = cfg["render"]["width"], cfg["render"]["height"]
    tl["settings"].update(width=W, height=H)
    clips = tl["clips"]
    T = cfg["timeline"]["transition_sec"]
    groups = group_dissolves(clips)
    tails = {}
    for g in groups:
        for i in g[:-1]:
            tails[i] = T
    only = set(a.only.split(",")) if a.only else None

    def job(i):
        c = clips[i]
        if only and c["id"] not in only and (pdir / "render" / "segments" / f"{c['id']}.mp4").exists():
            return pdir / "render" / "segments" / f"{c['id']}.mp4"
        nxt = clips[i + 1] if i + 1 < len(clips) else None
        try:
            return render_clip(c, nxt, tails.get(i, 0.0), cfg, pdir, a.preview)
        except Exception as e:  # noqa: BLE001 -> fallback card keeps timeline intact
            log.error("clip %s (%s) failed: %s — using fallback card", c["id"], c.get("kind"), str(e)[:300])
            fb = dict(c, kind="card", text=tl["title"], transition_in={"type": "cut", "duration": 0})
            c["render_error"] = str(e)[:300]
            return render_clip(fb, nxt, tails.get(i, 0.0), cfg, pdir, a.preview)

    with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as ex:
        files = list(ex.map(job, range(len(clips))))
    log.info("rendered %d segments", len(files))

    parts = []
    for gi, g in enumerate(groups):
        if len(g) == 1:
            parts.append(files[g[0]])
        else:
            out = pdir / "render" / "segments" / f"group_{gi:04d}.mp4"
            durs = [clips[i]["duration"] + tails.get(i, 0.0) for i in g]
            parts.append(xfade_group([files[i] for i in g], durs, T, out, cfg, a.preview))
    lst = pdir / "render" / "concat.txt"
    lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in parts), encoding="utf-8")
    assembled = pdir / "render" / "assembled.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", assembled])
    info = media_info(assembled)
    tl["render"] = {"assembled": str(assembled), "duration": info["duration"], "width": W, "height": H,
                    "preview": a.preview, "errors": {c["id"]: c["render_error"] for c in clips if c.get("render_error")}}
    write_json(pdir / "timeline.json", tl)
    drift = info["duration"] - tl["total_duration"]
    log.info("assembled %.2fs (timeline %.2fs, drift %+.2fs) -> %s", info["duration"], tl["total_duration"], drift, assembled)
    print(assembled)


if __name__ == "__main__":
    main()
