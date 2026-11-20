"""Sound design + mix: cleaned voice, chaptered music bed with sidechain ducking, SFX cued from src/shots.json.
Output: public/audio/final_mix.wav (-14 LUFS, -1.5 dBTP)."""
import json, subprocess, os
A = "raw/audio"; os.makedirs("public/audio", exist_ok=True)
shots = json.load(open("src/shots.json"))
END = 614.47
# (file, start_in_video, end_in_video, source_offset, gain_db)
MUSIC = [("m188", 0.0, 95.4, 0.0, 0), ("m565", 95.0, 239.6, 0.0, 0), ("m140", 239.2, 322.0, 0.0, -2),
         ("m73", 321.6, 372.0, 0.0, 0), ("m588", 371.6, 491.4, 0.0, 0), ("m587", 491.0, END, 0.0, 0)]
cues = [(0.0, "sfx1279", -4), (0.0, "sfx1491", -8)]
for s in shots:
    t = s["start"]
    if s["kind"] == "mg":
        if s["mg"] == "chapter": cues += [(max(0, t - 0.35), "sfx1489", -9), (t, "sfx1143", -7)]
        elif s["mg"] == "question": cues += [(max(0, t - 0.2), "sfx1491", -10), (t, "sfx2150", -12)]
        else: cues += [(max(0, t - 0.15), "sfx1485", -13)]
    ov = s.get("overlay")
    if ov:
        if ov["type"] == "stamp": cues.append((t + 4 / 30, "sfx2150", -7))
        elif ov["type"] in ("label", "stat"): cues.append((t + 2 / 30, "sfx2357", -16))
        elif ov["type"] in ("quote", "big"): cues.append((t, "sfx1485", -12))
        elif ov["type"] == "breaking": cues.append((t, "sfx1031", -10))
inputs = ["-i", "raw/../" + "dl_audio.wav"]
inputs = ["-i", "raw/audio/voice.wav"]
fc = []
# voice chain
fc.append("[0:a]aresample=48000,highpass=f=80,afftdn=nr=10:nf=-40,equalizer=f=300:t=q:w=1.2:g=-2,"
          "equalizer=f=3200:t=q:w=1.0:g=2.5,equalizer=f=11000:t=h:w=0.7:g=1.5,deesser=i=0.35,"
          "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=3,asplit=2[voice][sc]")
mus = []
for k, (f, a, b, off, g) in enumerate(MUSIC):
    inputs += ["-i", f"{A}/{f}.mp3"]; idx = len(inputs) // 2 - 1
    d = b - a
    fc.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,atrim={off}:{off + d},asetpts=PTS-STARTPTS,"
              f"afade=t=in:d=1.2,afade=t=out:st={d - 1.5}:d=1.5,volume={g}dB,adelay={int(a * 1000)}|{int(a * 1000)}[m{k}]")
    mus.append(f"[m{k}]")
fc.append("".join(mus) + f"amix=inputs={len(mus)}:normalize=0,volume=-17dB[mbed]")
fc.append("[mbed][sc]sidechaincompress=threshold=0.04:ratio=6:attack=20:release=400:makeup=1[mduck]")
sfxfiles = sorted(set(c[1] for c in cues)); sfxidx = {}
for f in sfxfiles:
    inputs += ["-i", f"{A}/{f}.mp3"]; sfxidx[f] = len(inputs) // 2 - 1
from collections import Counter
cnt = Counter(c[1] for c in cues); used = Counter(); fx = []
for f in sfxfiles:
    n = cnt[f]; fc.append(f"[{sfxidx[f]}:a]aresample=48000,aformat=channel_layouts=stereo,asplit={n}" + "".join(f"[{f}_{i}]" for i in range(n)))
for j, (t, f, g) in enumerate(cues):
    i = used[f]; used[f] += 1
    ms = int(t * 1000)
    fc.append(f"[{f}_{i}]volume={g}dB,adelay={ms}|{ms}[x{j}]"); fx.append(f"[x{j}]")
fc.append("".join(fx) + f"amix=inputs={len(fx)}:normalize=0[sfx]")
fc.append("[voice]aformat=channel_layouts=stereo[vst]")
fc.append(f"[vst][mduck][sfx]amix=inputs=3:normalize=0,atrim=0:{END},alimiter=limit=0.95[out]")
open("raw/audio/filter.txt", "w").write(";\n".join(fc))
cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", "raw/audio/filter.txt", "-map", "[out]", "-c:a", "pcm_s24le", "raw/audio/premix.wav"]
subprocess.run(cmd, check=True)
# two-pass loudness normalisation to -14 LUFS
m = subprocess.run(["ffmpeg", "-i", "raw/audio/premix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
js = json.loads(m[m.rfind("{"):m.rfind("}") + 1])
af = (f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
      f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "raw/audio/premix.wav", "-af", af, "-ar", "48000", "-c:a", "pcm_s16le", "public/audio/final_mix.wav"], check=True)
print(len(cues), "sfx cues; measured", js["input_i"], "LUFS ->", "-14")
