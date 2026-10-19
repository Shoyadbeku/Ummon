Yuklagan rasmlarimni gapirayotgan qilib video qil, keyin yuklagan ovozimga moslab bitta montaj qil.

1-QISM. Har bir rasmdan video
- Har bir rasm uchun alohida video, har biri aniq 10 soniya, ovozsiz, subtitrsiz.
- Faqat lab harakati, mimika va yengil harakat (sham alangasi, tutun, orqadagi qahramonlar).
- Kamera qimirlamasin, rasm uslubi o'zgarmasin.
- Bepul usul: Shoyadbeku/Ummon reposidagi media-input branchiga rasmlarni images/NN.jpg
  (01, 02, ... yuklagan tartibimda) qilib yukla. Eski rasmlar va videolar ustidan yozilaversin.
- Har rasm uchun tools/prompts.json ga 2 ta inglizcha prompt yoz: 1-yarmida asosiy qahramon
  gapiradi, 2-yarmida ikkinchisi javob beradi. Har prompt "Static camera, 2D cartoon animation."
  bilan boshlansin va "mouth clearly opening and closing as he speaks" kabi so'zlar bo'lsin.
  Rasmda bitta qahramon bo'lsa, 2-yarmida o'sha qahramon tinglab, keyin javob beradi.
- Rasmlar soni 12 ta bo'lmasa, .github/workflows/animate.yml dagi matrix ro'yxatini
  rasmlar soniga moslab o'zgartir.
- Push qilgach mavjud animate.yml workflow (Wan 2.2) ishga tushadi (~10 daqiqa) va
  videos/NN.mp4 ni o'zi commit qiladi. sleep bilan kutma, background'da git fetch bilan kut.
- Tayyor bo'lgach har bir videoni kadrlab tekshir (davomiyligi 10 s, ovoz yo'q,
  uslub buzilmagan) va menga rasmlar tartibida yubor. Kamchiliklarini ochiq ayt.

2-QISM. Ovozga moslab montaj (ffmpeg bilan, yangi paket o'rnatma)
- Ovoz faylidagi pauzalarni top:
  ffmpeg -i OVOZ.mp3 -af silencedetect=noise=-35dB:d=0.35 -f null -
- Sahnalarni rasmlar tartibida qo'y; har sahna almashishi pauzaning o'rtasiga to'g'ri
  kelsin (sahnalar soni = pauzalar soni + 1 bo'lishi kerak; ko'p bo'lsa eng qisqa
  pauzalarni tashlab ket).
- Tayyor skript bor: montage/build.py. Undagi `cuts` ro'yxatini yangi pauzalarga,
  `end` ni ovoz uzunligiga almashtirib ishlat:
  python3 montage/build.py OVOZ.mp3 montage/hikoya_final.mp4
  U quyidagini qiladi: 1080x1920, 0.6 s silliq o'tishlar, 10 s dan uzun sahnani biroz
  sekinlashtiradi, iliq kino rang, vinyetka, kino donachasi, boshida/oxirida qora fade,
  ovozni -16 LUFS ga tenglaydi.
- Natijani kadrlab tekshir.
- Keyin yuklab olish uchun 100 MB dan kichik qilib siq:
  ffmpeg -i montage/hikoya_final.mp4 -c:v libx264 -preset slow -crf 22 -maxrate 5M
  -bufsize 10M -c:a copy -movflags +faststart montage/hikoya.mp4
- montage/hikoya.mp4 ni media-input branchiga commit/push qil (hikoya_final.mp4 .gitignore da).
- Menga videoni yubor va yuklab olish havolasini ber:
  https://github.com/Shoyadbeku/Ummon/raw/media-input/montage/hikoya.mp4
