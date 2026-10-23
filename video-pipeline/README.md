# Onoda videosi: ishlab chiqarish quvuri

`onoda_29_yil.mp4` shu skriptlar bilan yig'ilgan. Yo'llar `/home/user/work` ga moslangan.

1. `scenes.py` — 42 ta sahna: ssenariy bo'lagi, rasm prompti, ekrandagi hook matni.
2. `gen.py` — `sd-server` (stable-diffusion.cpp, SDXL-Turbo q8_0 + TAESD-XL, 2 qadam, 1024×576) orqali rasmlar. `SEED_OFS=N python3 gen.py imgs 25,29` bilan alohida sahnalarni qayta yaratish mumkin.
3. `asr.py` — faster-whisper (medium) bilan diktor ovozidan so'z vaqtlari.
4. `align.py` — ssenariy so'zlarini ovoz vaqtlariga moslab, `remotion/public/timeline.json` (sahna vaqtlari + karaoke subtitrlar) yaratadi.
5. `music.py` — dasturiy yaratilgan fon musiqasi (D minor pad, yurak urishi pulsi).
6. `remotion/` — montaj: Ken Burns harakati, xira o'tishlar, "29 YIL" hook zarbasi, sarlavha kartasi, kino donadorligi, letterbox, karaoke subtitrlar, obuna tugmasi animatsiyasi.
7. `mix.sh` — ovoz + musiqa (sidechain ducking, -15 LUFS) va video bilan birlashtirish.
