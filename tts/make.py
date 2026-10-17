#!/usr/bin/env python3
"""Uzbek voice-over with espeak-ng (open source), aligned to the video's burned-in subtitles."""
import subprocess, sys, os, json

VIDEO = sys.argv[1]
OUT = sys.argv[2]
W = os.path.dirname(os.path.abspath(__file__)) + "/seg"
os.makedirs(W, exist_ok=True)

# (start, end, voice, pitch, text)  -- tulki = hikoyachi (narrator)
N, RAM, MER, OLD, DEBT = ("uz+m3", 38), ("uz+m1", 62), ("uz+m2", 48), ("uz+m7", 30), ("uz+m6", 45)
S = [
    (0.0, 4.0, N, "Ertaga pulingiz yo‘qolsa, bugun yoningizda yurganlarning nechtasi qoladi?"),
    (4.05, 5.2, N, "Qo‘chqor jim qoldi."),
    (5.25, 6.2, N, "Qo‘chqor kulib dedi:"),
    (6.25, 7.7, RAM, "Mening do‘stlarim ko‘p."),
    (7.75, 8.7, N, "Tulki sekin so‘radi:"),
    (8.75, 10.2, N, "Ularga nima bera olasan?"),
    (10.25, 12.2, N, "Shaharda boy bir savdogar yashardi."),
    (12.25, 14.95, N, "Uyi mehmonga to‘la, telefoni tinmay jiringlardi."),
    (15.0, 16.95, N, "Bir kuni barcha pulidan ayrildi."),
    (17.0, 18.7, N, "Avval do‘stlari band bo‘lib qoldi."),
    (18.75, 20.45, N, "Keyin qo‘ng‘iroqlar kamaydi."),
    (20.5, 22.95, N, "Oxiri, salom beradiganlar ham siyraklashdi."),
    (23.0, 24.95, N, "Faqat bitta eski tanish har kuni kelardi."),
    (25.0, 27.7, N, "Hech narsa so‘ramas, shunchaki yonida o‘tirardi."),
    (27.75, 28.7, N, "Savdogar so‘radi:"),
    (28.75, 29.7, MER, "Nega kelyapsan?"),
    (29.75, 30.45, N, "Javob berdi:"),
    (30.5, 32.45, OLD, "Men sening puling uchun kelmaganman."),
    (32.5, 33.95, N, "Shu payt eshik taqilladi."),
    (34.0, 35.2, N, "Qarzdor kirib keldi:"),
    (35.25, 37.7, DEBT, "Eshitdim, kambag‘al bo‘libsan! Qarzingni qaytar!"),
    (37.75, 39.2, N, "Qo‘chqor hayratdan yutindi."),
    (39.25, 41.7, RAM, "Demak, ba’zilar faqat pul uchun kelarkan-da."),
    (41.75, 42.7, N, "Tulki ohista dedi:"),
    (42.75, 44.45, N, "Odamni bilmoqchimisiz?"),
    (44.5, 47.9, N, "Nima bera olishingizni emas, nima bera olmasligingizni ko‘ring."),
]

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", p]).strip())

inputs, filt = [], []
for i, (a, b, (voice, pitch), text) in enumerate(S):
    raw, fit = f"{W}/{i:02d}_raw.wav", f"{W}/{i:02d}.wav"
    def synth(rate):
        subprocess.run(["espeak-ng", "-v", voice, "-s", str(rate), "-p", str(pitch), "-g", "1", "-w", raw, text], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af",
                        "silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
                        "silenceremove=start_periods=1:start_threshold=-50dB,areverse", f"{W}/{i:02d}_t.wav"], check=True)
        return dur(f"{W}/{i:02d}_t.wav")
    slot, rate = b - a, 155
    d = synth(rate)
    if d > slot:  # speak faster natively (espeak keeps clarity better than time-stretching)
        rate = min(int(rate * d / slot * 1.03), 260)
        d = synth(rate)
    tempo = max(1.0, d / slot)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{W}/{i:02d}_t.wav", "-af",
                    f"atempo={tempo:.3f},aresample=44100", fit], check=True)
    print(f"{i:02d} rate={rate} slot={slot:.2f}s speech={d:.2f}s tempo={tempo:.2f}  {text}")
    inputs += ["-i", fit]
    ms = int(a * 1000)
    filt.append(f"[{i+1}:a]adelay={ms}|{ms}[s{i}]")

mix = "".join(f"[s{i}]" for i in range(len(S)))
filt.append(f"{mix}amix=inputs={len(S)}:normalize=0,"
            "highpass=f=80,lowpass=f=9000,aecho=0.8:0.6:40:0.15,"
            "loudnorm=I=-16:TP=-1.5,apad[aout]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO, *inputs, "-filter_complex", ";".join(filt),
                "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-shortest", OUT], check=True)
print("OK", OUT)
