"""Yakuniy audio miks: tozalangan ovoz + fon musiqasi (ovoz ostida sidechain bilan pasayadi) + SFX."""
import json, subprocess, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sb=json.load(open(f"{ROOT}/src/data/storyboard.json"))
D=sb["duration"]
inputs=["-i",f"{ROOT}/public/audio/voice_clean.wav","-i",f"{ROOT}/public/music/news_bed_original.wav"]
fc=[]; labels=[]
for i,s in enumerate(sb["sfx"]):
    inputs+=["-i",f"{ROOT}/public/sfx/{s['name']}.wav"]
    ms=int(s["t"]*1000); k=i+2
    fc.append(f"[{k}:a]volume={s['db']}dB,adelay={ms}|{ms},apad=whole_dur={D}[s{i}]"); labels.append(f"[s{i}]")
fc.append(f"[0:a]asplit=2[v][vsc]")
fc.append(f"[1:a]volume=-15dB,atrim=0:{D}[m0]")
fc.append(f"[m0][vsc]sidechaincompress=threshold=0.02:ratio=6:attack=25:release=450:makeup=1[m]")
fc.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0[sfx]")
fc.append(f"[v][m][sfx]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.89,loudnorm=I=-14:TP=-1.0:LRA=11[out]")
cmd=["ffmpeg","-y","-loglevel","error"]+inputs+["-filter_complex",";".join(fc),"-map","[out]","-ar","48000","-ac","2",f"{ROOT}/public/audio/final_mix.wav"]
subprocess.run(cmd,check=True)
print("ok")
