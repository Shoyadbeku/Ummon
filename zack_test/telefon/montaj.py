# Kadrlarni 24 fps MP4 ga yig'ish (1080x1920) + foydalanuvchi ovozi + tovush effektlari (sfx.py).
# Zack D. montaji: zarbalarda qisqa oq chaqnash, vinyetka, kino donadorligi, oxirida qorayish.
# Harorat ko'rsatkichi (°C) 3D da emas, shu yerda drawtext bilan chiziladi (DOF xiralashtirmasin): qiymat TEMP jadvalidan
# bo'lakli-chiziqli ifoda  v0 + sum(k_i * clip(t - t_i, 0, dt_i)).
# python3 -I montaj.py <kadrlar_papkasi> <ovoz.wav> <sfx.wav> <events.json> <chiqish.mp4>
import json, subprocess, sys
FR, VO, SFX, EV, OUT = sys.argv[1:6]
ev = json.load(open(EV)); END = ev["end"]; DUR = END / 24.0
def t(f): return (f - 1) / 24.0
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"

# harorat ifodasi
T_ = ev["temp"]; parts = [f"{T_[0][1]:.2f}"]
for (a, va), (b, vb) in zip(T_, T_[1:]):
    dt = t(b) - t(a)
    if dt > 0: parts.append(f"{(vb - va) / dt:.4f}*clip(t-{t(a):.3f}\\,0\\,{dt:.3f})")
expr = "+".join(parts)
hud_on = "+".join(f"between(t\\,{t(a):.3f}\\,{t(b) + 1 / 24 - 0.001:.3f})" for a, b in ev["hud"])

flashes = [ev["plug"], ev["xr"], ev["cpu_zoom"], ev["short"], ev["short"] + 2, ev["crack"], ev["boom"]]
FLASH = "+".join(f"between(t,{t(f):.3f},{t(f) + 0.07:.3f})" for f in flashes)

vf = (f"[0:v]scale=1080:1920:flags=lanczos,"
      f"lutyuv=y='min(255,val*1.6+60)':enable='{FLASH}',"
      f"eq=saturation=1.08:contrast=1.05,vignette=PI/5,noise=alls=5:allf=t,"
      f"drawbox=x=300:y=150:w=480:h=210:color=black@0.45:t=fill:enable='{hud_on}',"
      f"drawtext=fontfile={FONT}:text='BATAREYA HARORATI':fontsize=34:fontcolor=white@0.85:x=(w-text_w)/2:y=170:enable='{hud_on}',"
      f"drawtext=fontfile={FONT}:text='%{{eif\\:{expr}\\:d}}°C':fontsize=120:fontcolor=white:borderw=5:bordercolor=0xff3b1f:"
      f"x=(w-text_w)/2:y=215:enable='{hud_on}',"
      f"fade=t=in:st=0:d=0.08,fade=t=out:st={DUR - 0.6:.3f}:d=0.6,format=yuv420p[v];"
      f"[1:a]aformat=sample_rates=48000:channel_layouts=mono,apad,asplit=2[vo][vsc];"
      f"[2:a]aformat=sample_rates=48000:channel_layouts=mono,volume=0.9[fx];"
      f"[fx][vsc]sidechaincompress=threshold=0.04:ratio=4:attack=15:release=250[fxd];"
      f"[vo][fxd]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,atrim=0:{DUR:.3f}[a]")
cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", "24", "-i", f"{FR}/%04d.png", "-i", VO, "-i", SFX, "-frames:v", str(END),
       "-filter_complex", vf, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-maxrate", "9M",
       "-bufsize", "18M", "-c:a", "aac", "-b:a", "192k", "-t", f"{DUR:.3f}", "-movflags", "+faststart", OUT]
subprocess.run(cmd, check=True)
subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height,r_frame_rate", "-of", "compact", OUT])
