# "Dunyoni aslida kim boshqaradi?" — Shorts/Reels/TikTok montaji (Remotion)

Muallif ovozi (`Neytron_yulduzining_..._SadoStudio 15.wav`, 10:14) asosida qurilgan 9:16 hujjatli-uslubdagi video.
> Eslatma: fayl nomi "Neytron yulduzi" bo'lsa-da, ovozdagi mazmun — "Dunyoni aslida kim boshqaradi?". Montaj ovozdagi mazmunga qurilgan.

## Tuzilma
| Yo'l | Nima |
|---|---|
| `data/transcript_uz.txt` | Qo'lda tahrirlangan o'zbekcha transkripsiya (155 gap, Whisper segmentlari bilan bir xil tartibda) |
| `data/asr_whisper.json` | Whisper large-v3 xom natijasi (so'z vaqtlari) |
| `data/timeline.json` | Moslashtirilgan so'z-darajasidagi vaqtlar (`scripts/align.py`) |
| `data/Subtitles.srt` | Tayyor SRT |
| `data/storyboard.py` | Shot list: har bir gap/so'zga qaysi footage yoki motion graphic |
| `src/` | Remotion + React + TypeScript loyihasi (`Main.tsx`, `Captions.tsx`, `Overlays.tsx`, `MG.tsx`, `Effects.tsx`) |
| `scripts/` | `align.py`, `build_shots.py`, `prep_clips.py` (ffmpeg grading/framing), `mix_audio.py` (ovoz tozalash + musiqa + SFX), `stills.mjs` |

## Qayta qurish
```bash
npm install
python3 scripts/align.py data/asr_whisper.json data/transcript_uz.txt data
python3 scripts/build_shots.py .
# raw/<mixkit id>.mp4 kliplarini yuklab olish (Media_Sources.md), raw/audio/voice.wav — original ovoz
python3 scripts/prep_clips.py
python3 scripts/mix_audio.py
npx remotion studio            # tahrirlash
npx remotion render src/index.ts Main out/video_noaudio.mp4 --muted
ffmpeg -i out/video_noaudio.mp4 -i public/audio/final_mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest Final_Video.mp4
```
Matn yoki vizualni o'zgartirish: `data/transcript_uz.txt` / `data/storyboard.py` ni tahrirlab, yuqoridagi zanjirni qayta ishga tushiring.
