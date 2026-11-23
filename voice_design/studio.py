"""Ovozni studiya sifatiga keltirish: nafasni olib tashlash, shovqin tozalash, mastering.

    python studio.py kirish.wav chiqish.wav

1. Nafas: ovozsiz (F0 yo'q), 150 ms dan uzun va nutqdan sokinroq bo'laklar topiladi va
   deyarli jimlikka tushiriladi (yumshoq o'tish bilan). Qisqa undoshlar (s, sh, ch, f)
   150 ms dan qisqa bo'lgani uchun tegilmaydi.
2. Uzun pauzalar 0.45 s gacha qisqartiriladi: nutq zichroq, studiyadagidek eshitiladi.
3. ffmpeg: shovqin tozalash, past g'uvillashni kesish, de-esser, EQ, kompressor, limiter, -16 LUFS.
"""

import subprocess
import sys
import tempfile

import librosa
import numpy as np
import soundfile as sf

HOP = 0.01  # 10 ms


def nafas_bolaklari(y, sr, min_uzunlik=0.15):
    hop = int(sr * HOP)
    f0, voiced, _ = librosa.pyin(y, fmin=60, fmax=300, sr=sr, frame_length=2048, hop_length=hop)
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop)[0]
    n = min(len(voiced), len(rms))
    voiced, rms = voiced[:n], rms[:n]
    nutq_rms = np.median(rms[voiced]) if voiced.any() else rms.max()
    sokin = rms < nutq_rms * 0.35
    shubhali = (~voiced) & sokin & (rms > nutq_rms * 0.01)  # jimlik emas, lekin ovozsiz va sokin
    bolaklar, i = [], 0
    while i < n:
        if shubhali[i]:
            j = i
            while j < n and (shubhali[j] or rms[j] < nutq_rms * 0.01):
                j += 1
            if (j - i) * HOP >= min_uzunlik and shubhali[i:j].sum() * HOP >= min_uzunlik * 0.7:
                bolaklar.append((i * hop, j * hop))
            i = j
        else:
            i += 1
    return bolaklar


def nafasni_olib_tashla(y, sr, bolaklar, kuchsizlantirish=0.02, fade=0.02):
    g = np.ones_like(y)
    f = int(sr * fade)
    for a, b in bolaklar:
        g[a:b] = kuchsizlantirish
        g[max(0, a - f):a] = np.minimum(g[max(0, a - f):a], np.linspace(1, kuchsizlantirish, a - max(0, a - f)))
        g[b:b + f] = np.minimum(g[b:b + f], np.linspace(kuchsizlantirish, 1, len(g[b:b + f])))
    return y * g


def pauzalarni_qisqartir(y, sr, eng_uzun=0.45, chegara_db=-45):
    oraliqlar = librosa.effects.split(y, top_db=-chegara_db, frame_length=1024, hop_length=256)
    qismlar, oldingi = [], 0
    for a, b in oraliqlar:
        sukut = y[oldingi:a]
        if len(sukut) > eng_uzun * sr:
            sukut = np.concatenate([sukut[: int(eng_uzun * sr / 2)], sukut[-int(eng_uzun * sr / 2):]])
        qismlar += [sukut, y[a:b]]
        oldingi = b
    qismlar.append(y[oldingi:][: int(0.3 * sr)])
    return np.concatenate(qismlar)


MASTERING = (
    "afftdn=nr=12:nf=-50:tn=1,"
    "highpass=f=75,lowpass=f=16000,"
    "deesser=i=0.4:m=0.5:f=0.5,"
    "equalizer=f=110:t=q:w=1.0:g=2,"
    "equalizer=f=300:t=q:w=1.0:g=-2.5,"
    "equalizer=f=3000:t=q:w=1.2:g=2,"
    "equalizer=f=10000:t=h:w=1:g=1.5,"
    "acompressor=threshold=-22dB:ratio=3.5:attack=4:release=90:makeup=2.5:knee=4,"
    "alimiter=limit=0.89:attack=2:release=40,"
    "loudnorm=I=-16:TP=-1.5:LRA=6"
)


def studio(kirish, chiqish):
    y, sr = librosa.load(kirish, sr=None, mono=True)
    bolaklar = nafas_bolaklari(y, sr)
    print(f"Nafas bo'laklari: {len(bolaklar)} ta, jami {sum(b - a for a, b in bolaklar) / sr:.1f} s", file=sys.stderr)
    y = nafasni_olib_tashla(y, sr, bolaklar)
    oldin = len(y) / sr
    y = pauzalarni_qisqartir(y, sr)
    print(f"Pauzalar: {oldin:.1f} s -> {len(y) / sr:.1f} s", file=sys.stderr)
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, y, sr)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp.name, "-af", MASTERING,
                        "-ar", "48000", chiqish], check=True)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    studio(sys.argv[1], sys.argv[2])
