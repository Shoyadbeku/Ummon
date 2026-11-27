# Pasport kuchi — hujjatli YouTube videosi (16:9, Remotion)

Muallifning asl ovozi asosida yaratilgan hujjatli video: **“Nega o‘zbekistonliklar ko‘p davlatlarga vizasiz bora olmaydi?”**
(Henley Passport Index 2026, Shengen, migratsiya siyosati, Qozog‘iston / Qirg‘iziston / Singapur bilan taqqoslash).

> Eslatma: iCloud’dagi audio fayl nomi “Neytron yulduzining aql bovar qilmas og‘irligi” edi, lekin audio mazmuni pasport va vizalar haqida. Video audio **mazmuniga** qarab qurildi.

## Fayllar
| Fayl | Mazmuni |
|---|---|
| `Final_YouTube_Video_16x9.mp4` | 1920×1080, 30 fps, H.264 + AAC 320k, ≈7:27 (asl audio 7:11 + 15 s manbalar titri). Hajmi katta bo‘lgani uchun git’ga qo‘shilmagan (`.gitignore`) |
| `Subtitles.srt` | O‘zbekcha (lotin) subtitrlar, asl ovoz bilan sinxron |
| `Remotion_Project/` | React + TypeScript manba kodi |
| `Storyboard.csv` | Har bir sahna: vaqt, asl nutq, footage, grafika, sababi |
| `Authentic_Media_Sources.csv` | Har bir manba videosi: kim yoki nima, URL, autentiklik dalili, huquq asosi |
| `YouTube_Footage_Sources.csv` | Har bir parcha: asl va yakuniy vaqt kodi, davomiyligi, ekrandagi manba yozuvi |
| `YouTube_Description_Sources.txt` | YouTube tavsifiga tayyor manbalar ro‘yxati |
| `Fair_Use_Assessment.md` | Fair use / xavf bahosi |
| `YouTube_Download_Report.md` | Qidiruv, snapyt.app orqali yuklab olish, tekshiruv |
| `Missing_Authentic_Footage.md` | Topilmagan kadrlar va ularning o‘rniga qo‘llangan halol yechimlar |
| `Quality_Report.md` | Yakuniy QC |
| `data/` | `storyboard.py` (sahnalar manbasi), `cut_clips.py`, xom va tozalangan transkript, metama’lumot |

## Qayta qurish
```bash
# 1) Manba videolar (snapyt.app orqali yuklab olingan) <yt_dir>/<youtube_id>.mp4 ko‘rinishida turishi kerak
python3 data/storyboard.py data/storyboard.json
python3 data/cut_clips.py data/storyboard.json <yt_dir> Remotion_Project/public/clips
cp data/storyboard.json data/meta.json Remotion_Project/src/data/

# 2) Shriftlar (OFL) tizimga o‘rnatiladi — render vaqtida bloklanmasligi uchun
sudo cp Remotion_Project/public/fonts/*.ttf /usr/share/fonts/truetype/ && fc-cache -f

# 3) Render
cd Remotion_Project && npm install
npx remotion studio                    # ko‘rib chiqish
npx remotion render Documentary out/remotion_master.mp4 --codec=h264 --audio-codec=aac --crf=17 --audio-bitrate=320k
# 4) Yakuniy grain + faststart
ffmpeg -i out/remotion_master.mp4 -vf "noise=alls=5:allf=t" -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a copy -movflags +faststart ../Final_YouTube_Video_16x9.mp4
```
`public/clips` va `public/audio` (≈370 MB) git’ga qo‘shilmagan. Ular 1-qadam va `public/audio` ichidagi ffmpeg buyruqlari (`Quality_Report.md` → Audio) bilan qayta yaratiladi.

Biror kadrni almashtirish uchun `data/storyboard.py` dagi tegishli qatorni (`clip=[youtube_id, soniya]`) o‘zgartiring va 1–3-qadamlarni takrorlang.
