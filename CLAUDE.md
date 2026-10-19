# Ummon

## Ovoz klon (foydalanuvchi o'zbekcha matn tashlasa)

Foydalanuvchi izohsiz o'zbekcha matn (yangilik, post va h.k.) yuborsa, bu
"shu matnni mening ovozimda o'qit" degani. Savol bermasdan:

1. `bash ovoz-klon/setup.sh` — OmniVoice'ni `~/.ovoz-venv`'ga o'rnatadi (bor bo'lsa o'tkazib yuboradi).
2. Matnni scratchpad'dagi `.txt` faylga yoz, so'ng fonda (run_in_background) ishga tushir:
   `~/.ovoz-venv/bin/python ovoz-klon/klon.py <matn.txt> <scratchpad>/<nom>.mp3`
   CPU'da bir gap ~1-2 daqiqa oladi; foydalanuvchiga taxminiy vaqtni ayt.
3. Tayyor `.mp3`'ni SendUserFile bilan yubor. Javoblar o'zbek tilida.

Ovoz namunasi: `ovoz-klon/namuna.wav` (~5 s), uning matni `klon.py`dagi `NAMUNA_MATNI`.
Namuna fayli yo'q bo'lsa, foydalanuvchidan 5-10 soniyalik toza yozuv va
unda aytilgan gapning aniq matnini so'ra. Matnni Whisper'ga tanitma — o'zbekchada
noto'g'ri taniydi va natija buziladi.

Repo ochiq (public) bo'lsa, `namuna.wav`'ni commit qilma. `ovoz-klon/` GitHub Pages'ga chiqmaydi
(`pages.yml` uni o'chirib tashlaydi).
