#!/usr/bin/env python3
"""Uzbek voice-over with Abduqayum/uzbek-tts-natural-speech-chatterbox (MIT), aligned to the
video's burned-in subtitles.

Run from the root of a gokhaneraslan/chatterbox-finetuning clone (after its setup.py), with the
model repo downloaded to ./uzbek_chatterbox and its inference.py copied to the clone root:

    python chatterbox_voiceover.py VIDEO OUT.mp4

--dry-run uses espeak-ng instead of the model, to test timing and mixing without the weights.
"""
import argparse
import os
import subprocess

# (start, end, role, text) -- start/end are when the words are on screen; tulki = hikoyachi
S = [
    (0.0, 4.0, "N", "Ertaga pulingiz yo‘qolsa, bugun yoningizda yurganlarning nechtasi qoladi?"),
    (4.05, 5.2, "N", "Qo‘chqor jim qoldi."),
    (5.25, 6.2, "N", "Qo‘chqor kulib dedi:"),
    (6.25, 7.7, "RAM", "Mening do‘stlarim ko‘p!"),
    (7.75, 8.7, "N", "Tulki sekin so‘radi:"),
    (8.75, 10.2, "N", "Ularga nima bera olasan?"),
    (10.25, 12.2, "N", "Shaharda boy bir savdogar yashardi."),
    (12.25, 14.95, "N", "Uyi mehmonga to‘la, telefoni tinmay jiringlardi."),
    (15.0, 16.95, "N", "Bir kuni barcha pulidan ayrildi."),
    (17.0, 18.7, "N", "Avval do‘stlari band bo‘lib qoldi."),
    (18.75, 20.45, "N", "Keyin qo‘ng‘iroqlar kamaydi."),
    (20.5, 22.95, "N", "Oxiri, salom beradiganlar ham siyraklashdi."),
    (23.0, 24.95, "N", "Faqat bitta eski tanish har kuni kelardi."),
    (25.0, 27.7, "N", "Hech narsa so‘ramas, shunchaki yonida o‘tirardi."),
    (27.75, 28.7, "N", "Savdogar so‘radi:"),
    (28.75, 29.7, "MER", "Nega kelyapsan?"),
    (29.75, 30.45, "N", "Javob berdi:"),
    (30.5, 32.45, "OLD", "Men sening puling uchun kelmaganman."),
    (32.5, 33.95, "N", "Shu payt eshik taqilladi."),
    (34.0, 35.2, "N", "Qarzdor kirib keldi:"),
    (35.25, 37.7, "DEBT", "Eshitdim, kambag‘al bo‘libsan! Qarzingni qaytar!"),
    (37.75, 39.2, "N", "Qo‘chqor hayratdan yutindi."),
    (39.25, 41.7, "RAM", "Demak, ba’zilar faqat pul uchun kelarkan-da."),
    (41.75, 42.7, "N", "Tulki ohista dedi:"),
    (42.75, 44.45, "N", "Odamni bilmoqchimisiz?"),
    (44.5, 47.9, "N", "Nima bera olishingizni emas, nima bera olmasligingizni ko‘ring."),
]

# role -> (pitch factor, exaggeration). The model has one trained voice; characters get a small
# pitch shift so they are told apart, and more emotion for dialogue.
ROLES = {"N": (1.0, 0.5), "RAM": (1.08, 0.7), "MER": (1.03, 0.6), "OLD": (0.93, 0.5), "DEBT": (0.94, 0.9)}
MAX_TEMPO = 1.25  # speed up at most this much per line before letting it run into the next slot
GAP = 0.08


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", p]).strip())


def synth_all(work, dry_run):
    raws = []
    if dry_run:
        for i, (_, _, _, text) in enumerate(S):
            p = f"{work}/{i:02d}_raw.wav"
            subprocess.run(["espeak-ng", "-v", "uz", "-s", "130", "-w", p, text], check=True)
            raws.append(p)
        return raws

    import sys
    sys.path.insert(0, os.getcwd())  # inference.py lives in the toolkit clone we run from
    import soundfile as sf
    import torch
    from inference import load_engine, synthesize

    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.set_num_threads(os.cpu_count() or 4)
    engine = load_engine("pretrained_models", "uzbek_chatterbox/t3_finetuned_merged.safetensors", device)
    for i, (_, _, role, text) in enumerate(S):
        p = f"{work}/{i:02d}_raw.wav"
        audio, sr = synthesize(engine, text, "uzbek_chatterbox/reference_voice.wav",
                               exaggeration=ROLES[role][1], seed=42 + i)
        sf.write(p, audio, sr)
        print(f"{i:02d} {len(audio) / sr:.2f}s  {text}", flush=True)
        raws.append(p)
    return raws


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--work", default="voiceover_work")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.work, exist_ok=True)

    raws = synth_all(args.work, args.dry_run)

    # trim edges, apply character pitch
    clean, d = [], []
    for i, (raw, (_, _, role, _)) in enumerate(zip(raws, S)):
        p = f"{args.work}/{i:02d}_clean.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af",
                        "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                        "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                        f"rubberband=pitch={ROLES[role][0]},aresample=44100", p], check=True)
        clean.append(p)
        d.append(dur(p))

    # lay lines out: each starts with its subtitle (or right after the previous line), squeezed up
    # to MAX_TEMPO to fit its slot; if the whole thing still overruns the video, speed everything up
    video_end = dur(args.video) - 0.15
    g = 1.0
    while True:
        tempos, starts, t = [], [], 0.0
        for (a, b, _, _), di in zip(S, d):
            tempo = min(max(di / (b - a), 1.0), MAX_TEMPO) * g
            start = max(a, t + GAP if t else a)
            tempos.append(tempo)
            starts.append(start)
            t = start + di / tempo
        if t <= video_end or g >= 1.5:
            break
        g += 0.02

    inputs, filt = [], []
    for i, (p, tempo, start) in enumerate(zip(clean, tempos, starts)):
        print(f"{i:02d} start={start:6.2f} sub={S[i][0]:6.2f} speech={d[i]:.2f}s tempo={tempo:.2f}")
        inputs += ["-i", p]
        ms = int(start * 1000)
        filt.append(f"[{i + 1}:a]rubberband=tempo={tempo:.3f},adelay={ms}|{ms}[s{i}]")
    mix = "".join(f"[s{i}]" for i in range(len(S)))
    filt.append(f"{mix}amix=inputs={len(S)}:normalize=0,highpass=f=70,loudnorm=I=-16:TP=-1.5,apad[aout]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", args.video, *inputs, "-filter_complex", ";".join(filt),
                    "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", args.out], check=True)
    print("OK", args.out)


if __name__ == "__main__":
    main()
