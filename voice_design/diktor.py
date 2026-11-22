"""Ummon Diktor: OmniVoice bilan maxsus o'zbekcha erkak ovozi (voice design).

Ovoz: jarangdor, past tembrli, o'rta yoshli erkak diktor. Faktlar va
ma'lumot beruvchi videolar uchun.

Ikki bosqich:

  1. dizayn  - OmniVoice'ga ovoz tavsifi beriladi (male, middle-aged, low pitch).
               Bir nechta nomzod ovoz yaratiladi, har biri o'zbekcha ASR
               (navai-uz/whisper-small-uzbek) bilan qayta tinglanadi va
               xatosi eng kam (CER), ovozi eng past va barqaror nomzod tanlanadi.
               U `ovozlar/diktor.pt` bo'lib saqlanadi, shundan keyin ovoz
               har safar bir xil chiqadi.

  2. ayt     - istalgan o'zbekcha matnni shu ovozda o'qiydi. Matn avval
               normallashtiriladi (raqamlar, foiz, birliklar so'z bilan yoziladi),
               gaplarga bo'linadi, har bir gap ASR bilan tekshiriladi va xato
               bo'lsa qayta yaratiladi. Oxirida radio uslubidagi ishlov
               (EQ, kompressor, -16 LUFS) beriladi.

Misollar:
    python diktor.py dizayn
    python diktor.py ayt "Bilasizmi? Yer yuzida 8 milliarddan ortiq odam yashaydi." -o fakt.wav
    python diktor.py ayt -f matn.txt -o video_ovoz.wav
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
import time

import numpy as np
import soundfile as sf
import torch

from uz_matn import normallash

BU_PAPKA = os.path.dirname(os.path.abspath(__file__))
OVOZ_FAYL = os.path.join(BU_PAPKA, "ovozlar", "diktor.pt")
OVOZ_WAV = os.path.join(BU_PAPKA, "ovozlar", "diktor_namuna.wav")
ASR_MODEL = "navai-uz/whisper-small-uzbek"

# OmniVoice voice design faqat shu belgilarni tushunadi: jins, yosh, tembr balandligi.
# "Jarangdor diktor" uchun eng yaqin tavsiflar:
TAVSIFLAR = [
    "male, middle-aged, low pitch",
    "male, middle-aged, very low pitch",
    "male, young adult, low pitch",
]

# Dizayn uchun namuna gap: faktlar uslubi, o'zbekchaga xos tovushlar (o', g', sh, ch, q, x, ng) bor.
NAMUNA_MATN = (
    "Assalomu alaykum! Bugun sizga hayratlanarli faktlarni aytib beraman. "
    "O'zbekistonda qadimiy shaharlar ko'p, Samarqand esa ikki ming yetti yuz yildan ham qadimiyroq."
)

GEN = dict(num_step=32, guidance_scale=2.0, class_temperature=0.0)


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# ---------------------------------------------------------------- modellar

def tts_model():
    from omnivoice import OmniVoice

    cuda = torch.cuda.is_available()
    return OmniVoice.from_pretrained(
        "k2-fsa/OmniVoice",
        device_map="cuda:0" if cuda else "cpu",
        dtype=torch.float16 if cuda else torch.float32,
    )


class Tekshiruvchi:
    """O'zbekcha ASR: yaratilgan ovozni qayta matnga aylantirib, xatoni o'lchaydi."""

    def __init__(self):
        from transformers import pipeline

        self.asr = pipeline(
            "automatic-speech-recognition",
            model=ASR_MODEL,
            device=0 if torch.cuda.is_available() else -1,
        )

    def matn(self, audio: np.ndarray, sr: int) -> str:
        out = self.asr(
            {"raw": audio.astype(np.float32), "sampling_rate": sr},
            generate_kwargs={"language": "uzbek", "task": "transcribe"},
        )
        return out["text"]

    def cer(self, audio, sr, kutilgan: str) -> tuple[float, str]:
        eshitilgan = self.matn(audio, sr)
        return belgi_xatosi(sodda(kutilgan), sodda(eshitilgan)), eshitilgan


def sodda(t: str) -> str:
    t = re.sub(r"[‘’ʻʼ`']", "", t.lower())
    t = re.sub(r"[^a-zЀ-ӿ ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def belgi_xatosi(a: str, b: str) -> float:
    """Levenshtein masofasi / kutilgan uzunlik (CER)."""
    if not a:
        return 0.0 if not b else 1.0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1] / len(a)


def tembr_hz(audio: np.ndarray, sr: int) -> float:
    """Ovozning o'rtacha asosiy chastotasi (F0, Hz). Past qiymat - qalinroq ovoz."""
    import torchaudio.functional as F

    f0 = F.detect_pitch_frequency(torch.from_numpy(audio).float().unsqueeze(0), sr).squeeze(0).numpy()
    f0 = f0[(f0 > 60) & (f0 < 300)]
    return float(np.median(f0)) if len(f0) else 0.0


# ---------------------------------------------------------------- dizayn

def dizayn(args):
    model = tts_model()
    tek = Tekshiruvchi()
    sr = model.sampling_rate
    os.makedirs(os.path.dirname(OVOZ_FAYL), exist_ok=True)
    nomzod_papka = os.path.join(BU_PAPKA, "ovozlar", "nomzodlar")
    os.makedirs(nomzod_papka, exist_ok=True)

    natijalar = []
    for tavsif in TAVSIFLAR:
        for seed in range(args.nomzodlar):
            torch.manual_seed(seed)
            t0 = time.time()
            audio = model.generate(text=NAMUNA_MATN, language="uz", instruct=tavsif, **GEN)[0]
            cer, eshitildi = tek.cer(audio, sr, NAMUNA_MATN)
            hz = tembr_hz(audio, sr)
            # Ball: xato asosiy mezon; 140 Hz dan baland (ingichka) ovoz jarimalanadi.
            ball = cer + max(0.0, hz - 140) / 400
            nom = f"{tavsif.replace(', ', '_').replace(' ', '-')}_s{seed}.wav"
            sf.write(os.path.join(nomzod_papka, nom), audio, sr)
            natijalar.append(dict(tavsif=tavsif, seed=seed, cer=cer, hz=hz, ball=ball, audio=audio, nom=nom))
            log(f"{tavsif:34s} seed={seed}  CER={cer:.3f}  F0={hz:5.1f}Hz  "
                f"({time.time() - t0:.0f}s)  -> {eshitildi[:70]}")

    natijalar.sort(key=lambda r: r["ball"])
    eng = natijalar[0]
    log(f"\nTanlandi: {eng['tavsif']} seed={eng['seed']}  CER={eng['cer']:.3f}  F0={eng['hz']:.0f}Hz")
    sf.write(OVOZ_WAV, eng["audio"], sr)
    prompt = model.create_voice_clone_prompt(ref_audio=OVOZ_WAV, ref_text=NAMUNA_MATN)
    prompt.save(OVOZ_FAYL)
    with open(os.path.join(BU_PAPKA, "ovozlar", "natijalar.tsv"), "w") as f:
        f.write("ball\tcer\tf0_hz\ttavsif\tseed\tfayl\n")
        for r in natijalar:
            f.write(f"{r['ball']:.3f}\t{r['cer']:.3f}\t{r['hz']:.0f}\t{r['tavsif']}\t{r['seed']}\t{r['nom']}\n")
    log(f"Ovoz saqlandi: {OVOZ_FAYL}")


# ---------------------------------------------------------------- ayt

def gaplar(matn: str, max_belgi=220) -> list[str]:
    """Matnni gaplarga bo'ladi; juda uzun gapni vergul bo'yicha bo'ladi."""
    bolaklar = []
    for gap in re.split(r"(?<=[.!?])\s+", matn.strip()):
        while len(gap) > max_belgi:
            kesish = gap.rfind(", ", 0, max_belgi)
            if kesish < 40:
                kesish = gap.rfind(" ", 0, max_belgi)
            bolaklar.append(gap[: kesish + 1].strip())
            gap = gap[kesish + 1 :].strip()
        if gap:
            bolaklar.append(gap)
    return bolaklar


def radio_ishlov(kirish: str, chiqish: str):
    """Diktor ovoziga radio uslubi: past shovqinni kesish, qalinlik, aniqlik, kompressor, -16 LUFS."""
    filtr = (
        "highpass=f=70,"
        "equalizer=f=120:t=q:w=1.0:g=2.5,"   # ko'krak jarangi
        "equalizer=f=350:t=q:w=1.2:g=-2,"    # g'o'ng'illashni kamaytirish
        "equalizer=f=3500:t=q:w=1.0:g=2,"    # so'z aniqligi
        "acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=2,"
        "loudnorm=I=-16:TP=-1.5:LRA=7"
    )
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", kirish, "-af", filtr, "-ar", "48000", chiqish],
                   check=True)


def ovoz_yoli(nom: str) -> str:
    return nom if nom.endswith(".pt") else os.path.join(BU_PAPKA, "ovozlar", f"{nom}.pt")


def ayt(args):
    ovoz = ovoz_yoli(args.ovoz)
    if not os.path.exists(ovoz):
        sys.exit(f"Ovoz topilmadi: {ovoz}. Avval: python diktor.py dizayn yoki python diktor.py klon ...")
    from omnivoice.models.omnivoice import VoiceClonePrompt

    matn = open(args.fayl, encoding="utf-8").read() if args.fayl else " ".join(args.matn)
    if not matn.strip():
        sys.exit("Matn bering: python diktor.py ayt \"...\" yoki -f matn.txt")
    tayyor = normallash(matn)
    log("Normallashgan matn:\n" + tayyor + "\n")

    model = tts_model()
    sr = model.sampling_rate
    prompt = VoiceClonePrompt.load(ovoz)
    tek = None if args.tekshirmaslik else Tekshiruvchi()

    pauza = np.zeros(int(sr * args.pauza), dtype=np.float32)
    qismlar = []
    for i, gap in enumerate(gaplar(tayyor), 1):
        eng = None
        for urinish in range(args.urinish):
            torch.manual_seed(urinish)
            audio = model.generate(text=gap, language="uz", voice_clone_prompt=prompt, speed=args.tezlik, **GEN)[0]
            if tek is None:
                eng = (0.0, audio, "")
                break
            cer, eshitildi = tek.cer(audio, sr, gap)
            if eng is None or cer < eng[0]:
                eng = (cer, audio, eshitildi)
            if cer <= args.chegara:
                break
        holat = "" if tek is None else f"CER={eng[0]:.3f}"
        log(f"[{i}] {holat} {gap}")
        if tek is not None and eng[0] > args.chegara:
            log(f"    ! diqqat, ASR eshitgani: {eng[2]}")
        qismlar += [eng[1].astype(np.float32), pauza]

    toliq = np.concatenate(qismlar[:-1])
    chiqish = args.chiqish
    if args.xom:
        sf.write(chiqish, toliq, sr)
    else:
        with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
            sf.write(tmp.name, toliq, sr)
            radio_ishlov(tmp.name, chiqish)
    log(f"\nTayyor: {chiqish}  ({len(toliq) / sr:.1f} s)")


# ---------------------------------------------------------------- klon

KLON_SINOV = "Assalomu alaykum! Bu mening ovozim. Bugun sizga ikki ming yigirma oltinchi yilning eng qiziq faktlarini aytib beraman."


def klon(args):
    """O'z ovozingizdan klon: 5-20 soniyalik toza bo'lak va uning aniq matni kerak."""
    import torchaudio.functional as F

    audio, sr = sf.read(args.audio, dtype="float32", always_2d=True)
    audio = audio.mean(axis=1)
    bosh = int((args.boshi or 0) * sr)
    oxir = int(args.oxiri * sr) if args.oxiri else len(audio)
    audio = audio[bosh:oxir]
    if len(audio) / sr > 20:
        log(f"Diqqat: bo'lak {len(audio) / sr:.0f} s. 5-20 soniya eng yaxshi; --boshi/--oxiri bilan qisqartiring.")

    model = tts_model()
    tek = Tekshiruvchi()
    audio24 = F.resample(torch.from_numpy(audio), sr, model.sampling_rate).numpy()
    matn = args.matn or tek.matn(audio24, model.sampling_rate)
    if not args.matn:
        log("Diqqat: matn ASR bilan olindi, xatolar bo'lsa klon sifati pasayadi. Aniq matnni --matn bilan bering.")
    log(f"Namuna matni: {matn}")

    yol = ovoz_yoli(args.nom)
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    prompt = model.create_voice_clone_prompt(ref_audio=(torch.from_numpy(audio24), model.sampling_rate), ref_text=matn)
    prompt.save(yol)
    log(f"Ovoz saqlandi: {yol}")

    torch.manual_seed(0)
    sinov = model.generate(text=KLON_SINOV, language="uz", voice_clone_prompt=prompt, **GEN)[0]
    cer, eshitildi = tek.cer(sinov, model.sampling_rate, KLON_SINOV)
    log(f"Sinov: CER={cer:.3f}  F0 asl={tembr_hz(audio24, model.sampling_rate):.0f}Hz  "
        f"klon={tembr_hz(sinov, model.sampling_rate):.0f}Hz  -> {eshitildi}")
    sinov_fayl = os.path.splitext(yol)[0] + "_sinov.wav"
    sf.write(sinov_fayl, sinov, model.sampling_rate)
    log(f"Sinov fayli: {sinov_fayl}")


def main():
    p = argparse.ArgumentParser(description="Ummon Diktor: OmniVoice o'zbekcha erkak ovozi")
    sub = p.add_subparsers(dest="buyruq", required=True)

    d = sub.add_parser("dizayn", help="ovozni loyihalash va eng yaxshisini saqlash")
    d.add_argument("-n", "--nomzodlar", type=int, default=4, help="har bir tavsif uchun nomzodlar soni")
    d.set_defaults(fn=dizayn)

    a = sub.add_parser("ayt", help="matnni diktor ovozida o'qish")
    a.add_argument("matn", nargs="*")
    a.add_argument("-f", "--fayl", help="matn fayli (UTF-8)")
    a.add_argument("-o", "--chiqish", default="diktor.wav")
    a.add_argument("--ovoz", default="diktor", help="ovoz nomi (ovozlar/<nom>.pt) yoki .pt fayl yo'li")
    a.add_argument("--tezlik", type=float, default=None, help="masalan 0.95 sekinroq, 1.05 tezroq")
    a.add_argument("--pauza", type=float, default=0.35, help="gaplar orasidagi pauza (soniya)")
    a.add_argument("--urinish", type=int, default=3, help="xato bo'lsa necha marta qayta yaratish")
    a.add_argument("--chegara", type=float, default=0.08, help="qabul qilinadigan eng katta CER")
    a.add_argument("--tekshirmaslik", action="store_true", help="ASR tekshiruvisiz, tezroq")
    a.add_argument("--xom", action="store_true", help="radio ishlovisiz, 24 kHz WAV")
    a.set_defaults(fn=ayt)

    k = sub.add_parser("klon", help="o'z ovozingizdan klon yaratish")
    k.add_argument("audio", help="ovoz yozuvi (wav/mp3)")
    k.add_argument("--nom", default="mening_ovozim", help="saqlanadigan ovoz nomi")
    k.add_argument("--matn", help="bo'lakda aytilgan aniq matn (tavsiya etiladi)")
    k.add_argument("--boshi", type=float, help="bo'lak boshi, soniya")
    k.add_argument("--oxiri", type=float, help="bo'lak oxiri, soniya")
    k.set_defaults(fn=klon)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
