#!/usr/bin/env python3
"""Step 14: sound design and final audio mix.

Sub-commands
  tts    generate narration from storyboard text with edge-tts (optional, no key needed;
         voices uz-UZ-SardorNeural / uz-UZ-MadinaNeural, ru-RU-*, en-*) and re-time the
         storyboard to the real speech length
  beats  detect beats/onsets of the music track (numpy) -> audio/beats.json, used by
         scene_builder to snap cuts to the music
  mix    narration + music (looped, faded, side-chain ducked under the voice) +
         ambience beds + SFX hits + J/L-cut archive clip audio, then two-pass EBU R128
         loudness normalisation to -14 LUFS / -1 dBTP (YouTube reference)

Usage:
  python scripts/audio_editor.py tts   --project <slug> [--voice uz-UZ-SardorNeural]
  python scripts/audio_editor.py beats --project <slug> [--music file.mp3]
  python scripts/audio_editor.py mix   --project <slug>
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import SKILL_ROOT, load_config, log, media_info, project_dir, read_json, run, setup_logging, write_json  # noqa: E402

AFMT = "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo"


# --------------------------------------------------------------------------
# TTS
# --------------------------------------------------------------------------
def tts(pdir: Path, cfg: dict, voice: str | None, pause: float = 0.35) -> Path:
    try:
        import edge_tts  # type: ignore
    except ImportError as e:
        raise SystemExit("edge-tts is not installed: pip install edge-tts  (or provide --narration audio)") from e
    sb = read_json(pdir / "storyboard.json")
    lang = sb.get("language", "uz")
    voice = voice or os.environ.get(f"TTS_VOICE_{lang.upper()}") or {
        "uz": "uz-UZ-SardorNeural", "ru": "ru-RU-DmitryNeural", "en": "en-GB-RyanNeural"}.get(lang, "en-GB-RyanNeural")
    tdir = pdir / "audio" / "tts"
    tdir.mkdir(parents=True, exist_ok=True)

    async def speak(text, out):
        await edge_tts.Communicate(text, voice, rate="-4%").save(str(out))

    t = 0.0
    parts = []
    for sc in sb["scenes"]:
        mp3 = tdir / f"{sc['id']}.mp3"
        if not mp3.exists():
            asyncio.run(speak(sc["narration"], mp3))
        d = media_info(mp3)["duration"]
        sc["start"], sc["duration"] = round(t, 3), round(d + pause, 3)
        t += d + pause
        parts.append((mp3, d))
    # concatenate with pauses
    inputs, chain = [], []
    for i, (mp3, d) in enumerate(parts):
        inputs += ["-i", mp3]
        chain.append(f"[{i}:a]{AFMT},apad=pad_dur={pause}[a{i}]")
    chain.append("".join(f"[a{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1[out]")
    out = pdir / "audio" / "narration.wav"
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(chain), "-map", "[out]", out])
    sb["narration_audio"] = str(out)
    sb["timing_source"] = f"tts:{voice}"
    sb["total_duration"] = round(t, 3)
    for sc in sb["scenes"]:
        sc["shots"] = max(1, round(sc["duration"] / ((cfg["timeline"]["min_shot_sec"] + cfg["timeline"]["max_shot_sec"]) / 2)))
    write_json(pdir / "storyboard.json", sb)
    log.info("TTS narration %.1fs with %s -> %s", t, voice, out)
    return out


# --------------------------------------------------------------------------
# beat detection
# --------------------------------------------------------------------------
def decode_mono(path: Path, sr: int = 22050):
    import numpy as np
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.float32), sr


def detect_beats(path: Path) -> dict:
    import numpy as np
    x, sr = decode_mono(path)
    if len(x) < sr:
        return {"bpm": 0, "beats": [], "onsets": []}
    hop, win = 512, 2048
    n = 1 + (len(x) - win) // hop
    frames = np.lib.stride_tricks.as_strided(x, shape=(n, win), strides=(x.strides[0] * hop, x.strides[0]))
    spec = np.abs(np.fft.rfft(frames * np.hanning(win), axis=1))
    flux = np.maximum(0, np.diff(np.log1p(spec), axis=0)).sum(axis=1)
    flux = (flux - flux.mean()) / (flux.std() + 1e-9)
    fps = sr / hop
    # onset peaks
    k = int(fps * 0.1)
    onsets = []
    for i in range(k, len(flux) - k):
        if flux[i] > 1.2 and flux[i] == flux[i - k:i + k + 1].max():
            onsets.append(round((i + 1) / fps, 3))
    # tempo by autocorrelation (60-180 bpm)
    ac = np.correlate(flux, flux, mode="full")[len(flux) - 1:]
    lo, hi = int(fps * 60 / 180), int(fps * 60 / 60)
    lag = lo + int(np.argmax(ac[lo:hi]))
    bpm = 60 * fps / lag
    period = lag / fps
    # phase: align grid to strongest onsets
    best_phase, best = 0.0, -1
    for ph in np.linspace(0, period, 24, endpoint=False):
        idx = ((np.arange(ph, len(flux) / fps, period)) * fps).astype(int)
        idx = idx[idx < len(flux)]
        s = flux[idx].sum()
        if s > best:
            best, best_phase = s, ph
    beats = [round(float(t), 3) for t in np.arange(best_phase, len(x) / sr, period)]
    return {"bpm": round(float(bpm), 1), "beats": beats, "onsets": onsets, "source": str(path)}


# --------------------------------------------------------------------------
# mix
# --------------------------------------------------------------------------
def loudnorm_two_pass(src: Path, dst: Path, I: float, TP: float, LRA: float = 11.0) -> dict:
    p = run(["ffmpeg", "-hide_banner", "-i", src, "-af", f"loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json",
             "-f", "null", "-"], check=False)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr, re.S)
    if not m:
        run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af", f"loudnorm=I={I}:TP={TP}:LRA={LRA},{AFMT}", "-ar", "48000", dst])
        return {}
    j = json.loads(m.group(0))
    if float(j.get("input_i", -70)) < -60:  # silence: nothing to normalise
        run(["ffmpeg", "-y", "-v", "error", "-i", src, "-c:a", "pcm_s24le", "-ar", "48000", dst])
        return j
    af = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,{AFMT}")
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af", af, "-ar", "48000", "-c:a", "pcm_s24le", dst])
    return j


def mix(pdir: Path, cfg: dict, music_override: str | None = None) -> Path:
    tl = read_json(pdir / "timeline.json")
    A = cfg["audio"]
    total = float(tl["total_duration"])
    narr = tl["audio"].get("narration")
    music = music_override or tl["audio"].get("music")
    inputs: list = []
    chain: list[str] = []
    mix_labels: list[str] = []
    idx = 0
    narr_sc = None
    if narr and Path(narr).exists():
        inputs += ["-i", narr]
        chain.append(f"[{idx}:a]{AFMT},highpass=f=70,acompressor=threshold=0.125:ratio=2.5:attack=15:release=250,"
                     f"apad,atrim=0:{total:.3f}[narr0];[narr0]asplit=2[narr][narrsc]")
        mix_labels.append("[narr]")
        narr_sc = "[narrsc]"
        idx += 1
    else:
        log.warning("no narration audio — mix contains music/ambience only")
    if music and Path(music).exists():
        inputs += ["-stream_loop", "-1", "-i", music]
        fade_out = max(0, total - 4)
        base = (f"[{idx}:a]{AFMT},atrim=0:{total:.3f},asetpts=PTS-STARTPTS,volume={A['music_volume_db']}dB,"
                f"afade=t=in:st=0:d=2.5,afade=t=out:st={fade_out:.3f}:d=4")
        if narr_sc:
            ratio = max(2, min(20, 10 ** (A["duck_amount_db"] / 20) * 2))
            chain.append(f"{base}[mus0];[mus0]{narr_sc}sidechaincompress=threshold=0.02:ratio={ratio:.1f}:attack=30:release=600:makeup=1[mus]")
        else:
            chain.append(f"{base}[mus]")
        mix_labels.append("[mus]")
        idx += 1
    elif narr_sc:
        chain.append(f"{narr_sc}anullsink")
    for k, e in enumerate(tl["audio"].get("events", [])):
        p = Path(e["path"])
        if not p.exists():
            continue
        d = float(e["duration"])
        delay = int(float(e["start"]) * 1000)
        if e["type"] == "clip_audio":
            inputs += ["-ss", f"{e.get('src_in', 0):.3f}", "-t", f"{d / max(0.5, e.get('speed', 1.0)) + 0.2:.3f}", "-i", p]
            tempo = f",atempo={max(0.5, e.get('speed', 1.0)):.3f}" if abs(e.get("speed", 1.0) - 1) > 0.01 else ""
            chain.append(f"[{idx}:a]{AFMT}{tempo},atrim=0:{d:.3f},asetpts=PTS-STARTPTS,volume={e['gain_db']}dB,"
                         f"afade=t=in:st=0:d=0.35,afade=t=out:st={max(0, d - 0.45):.3f}:d=0.45,adelay={delay}|{delay}[e{k}]")
        elif e["type"] == "ambience":
            inputs += ["-stream_loop", "-1", "-i", p]
            chain.append(f"[{idx}:a]{AFMT},atrim=0:{d:.3f},asetpts=PTS-STARTPTS,volume={e['gain_db']}dB,"
                         f"afade=t=in:st=0:d=0.8,afade=t=out:st={max(0, d - 1.0):.3f}:d=1.0,adelay={delay}|{delay}[e{k}]")
        else:
            inputs += ["-i", p]
            chain.append(f"[{idx}:a]{AFMT},atrim=0:{d:.3f},asetpts=PTS-STARTPTS,volume={e['gain_db']}dB,adelay={delay}|{delay}[e{k}]")
        mix_labels.append(f"[e{k}]")
        idx += 1
    raw = pdir / "audio" / "mix_raw.wav"
    if not mix_labels:
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{total:.3f}", raw])
    else:
        # anullsrc base guarantees exact total length
        inputs += ["-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
        chain.append(f"[{idx}:a]{AFMT}[base]")
        labels = "[base]" + "".join(mix_labels)
        chain.append(f"{labels}amix=inputs={len(mix_labels) + 1}:normalize=0:duration=first:dropout_transition=0,"
                     f"alimiter=limit=0.97:level=false[out]")
        script = pdir / "audio" / "mix_filter.txt"
        script.write_text(";\n".join(chain), encoding="utf-8")
        run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex_script", script, "-map", "[out]",
             "-t", f"{total:.3f}", "-c:a", "pcm_s24le", raw], timeout=3600)
    out = pdir / "audio" / "mix.wav"
    stats = loudnorm_two_pass(raw, out, A["final_lufs"], A["true_peak_db"])
    write_json(pdir / "audio" / "mix_stats.json", {"loudnorm_first_pass": stats, "inputs": len(mix_labels)})
    log.info("mix -> %s (%d stems)", out, len(mix_labels))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["tts", "beats", "mix"])
    ap.add_argument("--project", required=True)
    ap.add_argument("--voice")
    ap.add_argument("--music", help="music file (default: picked from assets/music by mood)")
    ap.add_argument("--config")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    setup_logging(a.verbose)
    cfg = load_config(a.config)
    pdir = project_dir(cfg, a.project)
    if a.command == "tts":
        print(tts(pdir, cfg, a.voice))
    elif a.command == "beats":
        music = a.music
        if not music:
            files = sorted(p for p in (SKILL_ROOT / cfg["paths"]["music_dir"]).rglob("*")
                           if p.suffix.lower() in (".mp3", ".wav", ".ogg", ".flac", ".m4a"))
            music = str(files[0]) if files else None
        if not music:
            raise SystemExit("no music in assets/music — beats skipped")
        res = detect_beats(Path(music))
        write_json(pdir / "audio" / "beats.json", res)
        log.info("beats: %.1f bpm, %d beats", res["bpm"], len(res["beats"]))
        print(pdir / "audio" / "beats.json")
    else:
        print(mix(pdir, cfg, a.music))


if __name__ == "__main__":
    main()
