#!/usr/bin/env python3
"""
Rasmlar + ovoz.mp3 -> jonlantirilgan bitta MP4 video (1080p, -crf 18).

Bosqichlar:
  1. ovoz.mp3 davomiyligini ffprobe bilan aniqlaydi.
  2. Har bir rasmni gradio_client orqali Hugging Face Image-to-Video Space'ga
     yuboradi (Wan 2.2 -> LTX-Video -> Wan 2.1, biri ishlamasa keyingisiga o'tadi).
  3. Sahna uchun bitta klip yetmasa, oxirgi kadrni olib, undan davom ettiradi.
  4. CPU'da FFmpeg bilan hammasini birlashtiradi, ovozni qo'shadi va
     1080p, libx264 -crf 18 MP4 chiqaradi.

O'rnatish:
  pip install gradio_client
  (ffmpeg va ffprobe PATH'da bo'lishi kerak)

Ishga tushirish:
  export HF_TOKEN=hf_xxx            # ZeroGPU kvotasi uchun deyarli shart
  python video_jonlantir.py --ovoz ovoz.mp3 --rasmlar rasmlar/ --chiqish tayyor.mp4

Rasmlar papkadagi nom tartibida olinadi (01.png, 02.png, ...).
Har bir sahnaga alohida prompt berish uchun: --promptlar promptlar.txt
(har qatorda bitta prompt, rasmlar tartibida).
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

RASM_TURLARI = {".png", ".jpg", ".jpeg", ".webp"}

STANDART_PROMPT = (
    "make this image come alive, cartoon characters move naturally, "
    "subtle expressive gestures, gentle cinematic camera motion, smooth animation"
)
STANDART_NEGATIV = (
    "static, still picture, blurry, distorted, deformed faces, extra fingers, "
    "jittery motion, flicker, text artifacts, watermark, worst quality"
)

# Eslatma: rasmiy "Wan-AI/Wan2.1" Space hozir RUNTIME_ERROR holatida,
# "Lightricks/LTX-Video" esa o'chirilgan - shuning uchun ishlaydigan nusxalari ishlatiladi.
# Space'lar ustuvorlik tartibida. Biri xato bersa, keyingisi sinab ko'riladi.
# "max_sek" - Space bir chaqiruvda beradigan eng uzun klip.
SPACELAR = {
    "wan22": {"id": "zerogpu-aoti/wan2-2-fp8da-aoti-faster", "max_sek": 5.0},
    "ltx": {"id": "Lightricks/ltx-video-distilled", "max_sek": 8.0},
    "wan21": {"id": "multimodalart/wan2-1-fast", "max_sek": 5.0},
}


# --------------------------------------------------------------------------
# Yordamchi funksiyalar
# --------------------------------------------------------------------------

def log(xabar):
    print(f"[{time.strftime('%H:%M:%S')}] {xabar}", flush=True)


def ishga_tushir(buyruq):
    natija = subprocess.run(buyruq, capture_output=True, text=True)
    if natija.returncode != 0:
        raise RuntimeError(
            "Buyruq xato bilan tugadi:\n" + " ".join(map(str, buyruq)) + "\n" + natija.stderr[-2000:]
        )
    return natija.stdout


def davomiylik(fayl):
    """Audio yoki video faylning davomiyligi (soniya)."""
    chiqish = ishga_tushir([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(fayl),
    ])
    return float(chiqish.strip())


def oxirgi_kadr(video, rasm):
    """Videoning eng oxirgi kadrini PNG qilib saqlaydi."""
    ishga_tushir([
        "ffmpeg", "-y", "-v", "error", "-sseof", "-0.5", "-i", str(video),
        "-update", "1", "-frames:v", "999", str(rasm),
    ])
    if not Path(rasm).exists():
        raise RuntimeError(f"Oxirgi kadr olinmadi: {video}")
    return rasm


def video_yolini_ol(natija):
    """gradio_client turli Space'larda turlicha qaytaradi: str, dict yoki tuple."""
    if isinstance(natija, (list, tuple)):
        natija = natija[0]
    if isinstance(natija, dict):
        natija = natija.get("video") or natija.get("path") or natija.get("value")
        if isinstance(natija, dict):
            natija = natija.get("path")
    if not natija or not Path(natija).exists():
        raise RuntimeError(f"Space video qaytarmadi: {natija!r}")
    return natija


# --------------------------------------------------------------------------
# Hugging Face Space'lar bilan ishlash
# --------------------------------------------------------------------------

class Jonlantiruvchi:
    def __init__(self, tartib, token, urinishlar):
        from gradio_client import Client  # noqa: F401  (o'rnatilganini tekshirish)
        self.tartib = tartib
        self.token = token
        self.urinishlar = urinishlar
        self.mijozlar = {}
        self.ishlamaydi = set()

    def _mijoz(self, nom):
        from gradio_client import Client
        if nom not in self.mijozlar:
            sid = SPACELAR[nom]["id"]
            log(f"  Space'ga ulanilmoqda: {sid}")
            self.mijozlar[nom] = Client(sid, hf_token=self.token, verbose=False)
        return self.mijozlar[nom]

    def _chaqir(self, nom, rasm, prompt, sek):
        from gradio_client import handle_file
        mijoz = self._mijoz(nom)
        if nom == "wan22":
            natija = mijoz.predict(
                input_image=handle_file(str(rasm)), prompt=prompt,
                negative_prompt=STANDART_NEGATIV, steps=6,
                duration_seconds=sek, randomize_seed=True,
                api_name="/generate_video",
            )
        elif nom == "ltx":
            # Vertikal 9:16 ga yaqin o'lcham (32 ga karrali).
            natija = mijoz.predict(
                prompt=prompt, negative_prompt=STANDART_NEGATIV,
                input_image_filepath=handle_file(str(rasm)),
                height_ui=1024, width_ui=576, mode="image-to-video",
                duration_ui=sek, randomize_seed=True, improve_texture_flag=True,
                api_name="/image_to_video",
            )
        else:  # wan21
            natija = mijoz.predict(
                input_image=handle_file(str(rasm)), prompt=prompt,
                height=896, width=512, negative_prompt=STANDART_NEGATIV,
                duration_seconds=sek, randomize_seed=True,
                api_name="/generate_video",
            )
        return video_yolini_ol(natija)

    def klip(self, rasm, prompt, sek, saqlash):
        """Bitta rasmdan bitta klip. Kvota tugasa kutadi, Space buzuq bo'lsa keyingisiga o'tadi."""
        oxirgi_xato = None
        for nom in self.tartib:
            if nom in self.ishlamaydi:
                continue
            sek_bu = min(sek, SPACELAR[nom]["max_sek"])
            for urinish in range(1, self.urinishlar + 1):
                try:
                    log(f"  -> {nom}: {Path(rasm).name}, {sek_bu:.1f} s (urinish {urinish})")
                    yol = self._chaqir(nom, rasm, prompt, sek_bu)
                    shutil.copy(yol, saqlash)
                    return saqlash
                except Exception as e:  # noqa: BLE001
                    oxirgi_xato = e
                    matn = str(e)
                    log(f"     xato: {matn[:200]}")
                    if "ZeroGPU quota" in matn or "quota" in matn.lower():
                        kut = 60 * urinish
                        log(f"     ZeroGPU kvotasi tugadi, {kut} s kutilmoqda...")
                        time.sleep(kut)
                        continue
                    if "RUNTIME_ERROR" in matn or "invalid state" in matn or "not found" in matn.lower():
                        self.ishlamaydi.add(nom)
                        break
                    time.sleep(10)
        raise RuntimeError(f"Hech bir Space klip bera olmadi. Oxirgi xato: {oxirgi_xato}")


# --------------------------------------------------------------------------
# CPU zaxira: Space ishlamasa, rasmga Ken Burns (sekin zoom) harakat beradi
# --------------------------------------------------------------------------

def ken_burns(rasm, sek, saqlash, fps, w, h, indeks):
    kadrlar = max(1, round(sek * fps))
    # Juft/toq sahnalarda zoom-in va zoom-out almashinadi.
    if indeks % 2 == 0:
        z = f"min(1+0.12*on/{kadrlar},1.12)"
    else:
        z = f"max(1.12-0.12*on/{kadrlar},1)"
    vf = (
        f"scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase,crop={w * 2}:{h * 2},"
        f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={kadrlar}:s={w}x{h}:fps={fps},"
        "format=yuv420p"
    )
    ishga_tushir([
        "ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(rasm), "-vf", vf,
        "-frames:v", str(kadrlar), "-c:v", "libx264", "-crf", "16", "-preset", "medium",
        str(saqlash),
    ])
    return saqlash


# --------------------------------------------------------------------------
# Sahnani tayyorlash: kerakli uzunlikka yetguncha oxirgi kadrdan davom etadi
# --------------------------------------------------------------------------

def sahna_yasash(i, rasm, prompt, kerakli_sek, ish, jon, args):
    tayyor = ish / f"sahna_{i:02d}.mp4"
    if tayyor.exists() and not args.qayta:
        log(f"Sahna {i}: oldin tayyorlangan, o'tkazib yuborildi ({tayyor.name})")
        return tayyor

    if jon is None:
        log(f"Sahna {i}: CPU Ken Burns rejimi ({kerakli_sek:.2f} s)")
        return ken_burns(rasm, kerakli_sek, tayyor, args.fps, args.kenglik, args.balandlik, i)

    bolaklar = []
    jami = 0.0
    boshlangich = Path(rasm)
    j = 0
    while jami < kerakli_sek - 0.25 and j < args.max_bolak:
        qoldi = kerakli_sek - jami
        bolak = ish / f"sahna_{i:02d}_b{j}.mp4"
        if not bolak.exists() or args.qayta:
            # Davom ettirish bo'lagi uchun promptga uzluksizlik ishorasi qo'shiladi.
            p = prompt if j == 0 else prompt + ", continue the same motion seamlessly"
            jon.klip(boshlangich, p, max(2.0, qoldi), bolak)
        uzunlik = davomiylik(bolak)
        log(f"Sahna {i}: bo'lak {j} = {uzunlik:.2f} s")
        bolaklar.append(bolak)
        jami += uzunlik
        if jami < kerakli_sek - 0.25:
            # 3-bosqich: oxirgi kadrni olib, keyingi bo'lakni shundan boshlaymiz.
            boshlangich = oxirgi_kadr(bolak, ish / f"sahna_{i:02d}_b{j}_oxirgi.png")
        j += 1

    # Bo'laklarni bitta sahnaga yig'ish. Keyingi bo'lakning 1-kadri oldingisining
    # oxirgi kadri bilan bir xil, shuning uchun uni tashlab yuboramiz.
    kirishlar, filtrlar = [], []
    for k, b in enumerate(bolaklar):
        kirishlar += ["-i", str(b)]
        boshi = "trim=start_frame=1," if k > 0 else ""
        filtrlar.append(
            f"[{k}:v]{boshi}setpts=PTS-STARTPTS,"
            f"scale={args.kenglik}:{args.balandlik}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={args.kenglik}:{args.balandlik},fps={args.fps},setsar=1,format=yuv420p[v{k}]"
        )
    birlash = "".join(f"[v{k}]" for k in range(len(bolaklar)))
    filtrlar.append(f"{birlash}concat=n={len(bolaklar)}:v=1:a=0[out]")
    ishga_tushir([
        "ffmpeg", "-y", "-v", "error", *kirishlar,
        "-filter_complex", ";".join(filtrlar), "-map", "[out]", "-an",
        "-c:v", "libx264", "-crf", "16", "-preset", "medium", str(tayyor),
    ])
    return tayyor


def sahnani_moslash(klip, kerakli_sek, saqlash, args):
    """Klipni aniq kerakli uzunlikka keltiradi: ortig'ini kesadi, kamini sekinlashtiradi."""
    bor = davomiylik(klip)
    vf = []
    if bor < kerakli_sek * 0.97:
        # Juda qisqa bo'lsa biroz sekinlashtiramiz (max 1.35x), qolganini oxirgi kadr bilan to'ldiramiz.
        koef = min(kerakli_sek / bor, 1.35)
        vf.append(f"setpts={koef:.5f}*PTS")
    vf += [
        f"scale={args.kenglik}:{args.balandlik}:force_original_aspect_ratio=increase:flags=lanczos",
        f"crop={args.kenglik}:{args.balandlik}",
        f"fps={args.fps}",
    ]
    if args.silliq:
        vf.append(f"minterpolate=fps={args.fps}:mi_mode=mci:mc_mode=aobmc:vsbmc=1")
    vf += [f"tpad=stop_mode=clone:stop_duration={kerakli_sek:.3f}", "setsar=1", "format=yuv420p"]
    ishga_tushir([
        "ffmpeg", "-y", "-v", "error", "-i", str(klip), "-vf", ",".join(vf),
        "-t", f"{kerakli_sek:.3f}", "-an",
        "-c:v", "libx264", "-crf", "14", "-preset", "medium", str(saqlash),
    ])
    return saqlash


# --------------------------------------------------------------------------
# 4-bosqich: yakuniy birlashtirish + ovoz
# --------------------------------------------------------------------------

def yakuniy_video(sahnalar, ovoz, chiqish, sahna_sek, args):
    o = args.otish
    kirishlar = []
    for s in sahnalar:
        kirishlar += ["-i", str(s)]
    kirishlar += ["-i", str(ovoz)]
    audio_ix = len(sahnalar)

    if o > 0 and len(sahnalar) > 1:
        # Sahnalar orasida silliq crossfade (xfade).
        filtrlar, oldingi, offset = [], "[0:v]", 0.0
        for k in range(1, len(sahnalar)):
            offset += sahna_sek - o
            nom = f"[x{k}]"
            filtrlar.append(
                f"{oldingi}[{k}:v]xfade=transition={args.otish_turi}:duration={o}:offset={offset:.3f}{nom}"
            )
            oldingi = nom
        filtrlar.append(f"{oldingi}format=yuv420p[v]")
    else:
        birlash = "".join(f"[{k}:v]" for k in range(len(sahnalar)))
        filtrlar = [f"{birlash}concat=n={len(sahnalar)}:v=1:a=0,format=yuv420p[v]"]

    ishga_tushir([
        "ffmpeg", "-y", "-v", "error", "-stats", *kirishlar,
        "-filter_complex", ";".join(filtrlar),
        "-map", "[v]", "-map", f"{audio_ix}:a",
        "-c:v", "libx264", "-crf", "18", "-preset", args.preset,
        "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(args.fps),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-shortest", "-movflags", "+faststart", str(chiqish),
    ])


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Rasmlar + ovoz -> jonlantirilgan 1080p MP4")
    ap.add_argument("--ovoz", default="ovoz.mp3", help="tayyor ovoz fayli")
    ap.add_argument("--rasmlar", default="rasmlar", help="rasmlar papkasi (nom tartibida)")
    ap.add_argument("--chiqish", default="tayyor_video.mp4")
    ap.add_argument("--ish-papka", default="ish_papka", help="oraliq kliplar (qayta ishga tushirishda qayta ishlatiladi)")
    ap.add_argument("--promptlar", help="har qatorda bitta prompt (yoki JSON ro'yxat)")
    ap.add_argument("--space", default="wan22,ltx,wan21",
                    help=f"Space'lar tartibi, vergul bilan. Mavjud: {', '.join(SPACELAR)}")
    ap.add_argument("--hf-token", default=os.environ.get("HF_TOKEN"), help="yoki HF_TOKEN muhit o'zgaruvchisi")
    ap.add_argument("--faqat-cpu", action="store_true", help="AI'siz, faqat CPU Ken Burns harakati")
    ap.add_argument("--otish", type=float, default=0.5, help="sahnalar orasidagi crossfade (s), 0 = yo'q")
    ap.add_argument("--otish-turi", default="fade", help="xfade turi: fade, dissolve, smoothleft, ...")
    ap.add_argument("--kenglik", type=int, default=1080)
    ap.add_argument("--balandlik", type=int, default=1920, help="vertikal 9:16 uchun 1920; gorizontal uchun --kenglik 1920 --balandlik 1080")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--silliq", action="store_true", help="16fps AI kliplarni 30fps'ga minterpolate (CPU'da sekin)")
    ap.add_argument("--max-bolak", type=int, default=3, help="bir sahna uchun eng ko'p davom ettirish bo'laklari")
    ap.add_argument("--urinishlar", type=int, default=3)
    ap.add_argument("--preset", default="slow", help="libx264 preset (sifat/tezlik)")
    ap.add_argument("--qayta", action="store_true", help="oldingi kliplarni e'tiborsiz qoldirib qayta yaratish")
    args = ap.parse_args()

    for dastur in ("ffmpeg", "ffprobe"):
        if not shutil.which(dastur):
            sys.exit(f"{dastur} topilmadi. O'rnating: https://ffmpeg.org/download.html")

    ovoz = Path(args.ovoz)
    if not ovoz.exists():
        sys.exit(f"Ovoz fayli topilmadi: {ovoz}")
    rasmlar = sorted(p for p in Path(args.rasmlar).iterdir() if p.suffix.lower() in RASM_TURLARI)
    if not rasmlar:
        sys.exit(f"Rasmlar topilmadi: {args.rasmlar}")

    # 1-bosqich
    ovoz_sek = davomiylik(ovoz)
    n = len(rasmlar)
    o = args.otish if n > 1 else 0.0
    # xfade har bir o'tishda o'tish uzunligicha vaqt "yeydi", shuni qoplaymiz.
    sahna_sek = (ovoz_sek + o * (n - 1)) / n
    log(f"Ovoz: {ovoz_sek:.2f} s | Rasmlar: {n} ta | Har sahna: {sahna_sek:.2f} s")

    promptlar = [STANDART_PROMPT] * n
    if args.promptlar:
        matn = Path(args.promptlar).read_text(encoding="utf-8").strip()
        royxat = json.loads(matn) if matn.startswith("[") else [q.strip() for q in matn.splitlines() if q.strip()]
        for k, p in enumerate(royxat[:n]):
            promptlar[k] = p

    ish = Path(args.ish_papka)
    ish.mkdir(parents=True, exist_ok=True)

    jon = None
    if not args.faqat_cpu:
        if not args.hf_token:
            log("OGOHLANTIRISH: HF_TOKEN yo'q - ZeroGPU kvotasi juda kichik bo'ladi.")
        tartib = [s.strip() for s in args.space.split(",") if s.strip()]
        for s in tartib:
            if s not in SPACELAR:
                sys.exit(f"Noma'lum Space: {s}. Mavjud: {', '.join(SPACELAR)}")
        jon = Jonlantiruvchi(tartib, args.hf_token, args.urinishlar)

    # 2-3-bosqich
    moslangan = []
    for i, (rasm, prompt) in enumerate(zip(rasmlar, promptlar), start=1):
        log(f"Sahna {i}/{n}: {rasm.name}")
        try:
            klip = sahna_yasash(i, rasm, prompt, sahna_sek, ish, jon, args)
        except Exception as e:  # noqa: BLE001
            log(f"Sahna {i}: AI klip olinmadi ({str(e)[:150]}). CPU Ken Burns zaxirasi ishlatiladi.")
            klip = ken_burns(rasm, sahna_sek, ish / f"sahna_{i:02d}.mp4", args.fps, args.kenglik, args.balandlik, i)
        moslangan.append(sahnani_moslash(klip, sahna_sek, ish / f"tayyor_{i:02d}.mp4", args))

    # 4-bosqich
    log("FFmpeg: sahnalar birlashtirilmoqda va ovoz qo'shilmoqda (CPU)...")
    yakuniy_video(moslangan, ovoz, Path(args.chiqish), sahna_sek, args)
    log(f"TAYYOR: {args.chiqish} ({davomiylik(args.chiqish):.2f} s, "
        f"{args.kenglik}x{args.balandlik}, crf 18)")


if __name__ == "__main__":
    main()
