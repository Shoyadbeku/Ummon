# Historical Video Editor — tarixiy hujjatli videolar uchun avtomatik montaj Skill

Tarixiy mavzu, ssenariy yoki ovozli narratsiyadan **YouTube uchun tayyor, kinematografik
hujjatli film** yasaydigan Skill: ssenariyni sahnalarga ajratadi, o‘zbek/rus/ingliz tillarida
arxiv videolari, rasmlar, miniatyuralar va xaritalarni qidiradi, litsenziya va asl manbani
tekshiradi, faqat ruxsat etilgan materiallarni yuklab oladi, FFmpeg bilan montaj qiladi,
har bir kadrda manbani avtomatik ko‘rsatadi va to‘liq manbalar hisobotini yozadi.

> Claude Agent Skills formatida (`SKILL.md` + `scripts/` + `references/`). Claude Code,
> Claude.ai (Skills), Claude Agent SDK yoki oddiy terminalda ishlaydi.

---

## 1. O‘rnatish

### Talablar
| Dastur | Versiya | Majburiy |
|---|---|---|
| Python | 3.10+ | ha |
| FFmpeg + FFprobe (libass, libfreetype, libx264; libx265 ixtiyoriy) | 5.0+ (6.x tavsiya) | ha |
| yt-dlp | 2024.10+ | tavsiya (platformalar, CC videolar) |
| edge-tts | 6.1+ | ixtiyoriy (narratsiya ovozi yo‘q bo‘lsa) |
| faster-whisper | 1.0+ | ixtiyoriy (ovozni so‘zma-so‘z sinxronlash) |

```bash
unzip Historical_Video_Editor_Skill.zip
cd historical-video-editor
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install edge-tts faster-whisper pytest              # ixtiyoriy
cp .env.example .env                                     # kalitlarni to'ldiring (ixtiyoriy)
python scripts/check_env.py --ping                       # nima ishlashini ko'rsatadi
python -m pytest -q tests                                # 21 ta oflayn test
```

FFmpeg: Windows — `winget install Gyan.FFmpeg`; macOS — `brew install ffmpeg`;
Ubuntu — `sudo apt install ffmpeg fonts-dejavu`.

### Claude’ga Skill sifatida qo‘shish
- **Claude Code**: papkani `~/.claude/skills/historical-video-editor/` (shaxsiy) yoki loyiha
  ichida `.claude/skills/historical-video-editor/` ga ko‘chiring. Claude `SKILL.md` ni o‘zi topadi.
- **Claude.ai / Desktop**: Settings → Capabilities → Skills → *Upload skill* → ZIP faylni yuklang
  (kod ishlatish yoqilgan bo‘lishi kerak; video render uchun FFmpeg bor muhit kerak —
  eng yaxshisi Claude Code yoki o‘z kompyuteringiz).
- **Agent SDK**: `skills/` katalogiga qo‘ying va `setting_sources` orqali yoqing.

---

## 2. Ishga tushirish

### A) Claude bilan (tavsiya)
> «historical-video-editor skill bilan *Amir Temur va Samarqand* mavzusida 8 daqiqalik video
> tayyorla. Ssenariy: script.txt, ovoz: narration.mp3»

Claude `SKILL.md` dagi 14 bosqichni bajaradi, storyboard’ni o‘zi boyitadi (kalit so‘zlar,
davrlar), hisobotlarni o‘qib chiqadi va natijani topshiradi.

### B) Bitta buyruq bilan
```bash
python scripts/run_pipeline.py \
  --script examples/samarkand_demo/script.txt \
  --title "Sohibqiron yurti: Amir Temur va Samarqand" \
  --config examples/samarkand_demo/project.yaml \
  --narration my_voice.mp3            # yoki: --tts   yoki: --duration 480
  --preview                           # avval tez 960x540 ko'rib chiqish
```
Keyin to‘liq sifatda: `--from render` (yoki `--4k --codec libx265`).
Biror bosqichdan davom ettirish: `--from verify`, to‘xtatish: `--to build`.

### C) Bosqichma-bosqich
```bash
P="--project amir-temur"
python scripts/analyze_script.py --script script.txt --title "Amir Temur" --narration voice.mp3 --project amir-temur
python scripts/search_videos.py $P
python scripts/search_images.py $P
python scripts/verify_license.py $P
python scripts/download_media.py $P
python scripts/audio_editor.py beats $P          # assets/music da trek bo'lsa
python scripts/scene_builder.py $P
python scripts/source_overlay.py $P
python scripts/video_editor.py $P --preview
python scripts/audio_editor.py mix $P
python scripts/export_video.py $P                # --4k --codec libx265
python scripts/quality_check.py $P
```

### Natijalar (`output/<loyiha>/`)
| Fayl | Mazmuni |
|---|---|
| `<nom>.mp4` | yakuniy video (MP4, 1080p/4K, 25 fps, H.264/H.265, AAC) |
| `reports/SOURCES.md`, `sources.csv`, `sources.json` | har bir material: URL, muallif, litsenziya, videoda qayerda, asl fayldagi vaqt oralig‘i |
| `reports/youtube_description.md` | YouTube tavsifi: qisqacha mazmun, bo‘limlar (chapters), manbalar, litsenziyalar |
| `reports/license_report.md` | tekshirilgan nomzodlar: tasdiqlangan / rad etilgan va sababi |
| `reports/qc_report.md` | sifat nazorati (✅/⚠️/❌) |
| `reports/manual_search_links.md` | API’siz platformalar uchun tayyor qidiruv havolalari |
| `render/subtitles.srt` | YouTube’ga alohida yuklash uchun subtitr |
| `storyboard.json`, `timeline.json` | sahnalar va montaj rejasi (qo‘lda tahrirlash mumkin) |

---

## 3. API kalitlari (`.env`, hammasi ixtiyoriy)

| Kalit | Nima beradi | Qayerdan |
|---|---|---|
| `WIKIMEDIA_CONTACT` | Wikimedia so‘rovlarida aloqa ma’lumoti (cheklovlarni kamaytiradi) | e-mail yoki sayt |
| `PEXELS_API_KEY` | zamonaviy stok video/foto | pexels.com/api |
| `PIXABAY_API_KEY` | stok video/foto | pixabay.com/api/docs |
| `EUROPEANA_API_KEY` | Yevropa arxivlari (kinoxronika, foto) | pro.europeana.eu/page/get-api |
| `SMITHSONIAN_API_KEY` | Smithsonian Open Access (CC0) | api.data.gov/signup |
| `OPENVERSE_CLIENT_ID/SECRET` | Openverse limitini oshiradi | api.openverse.org |
| `YANDEX_SEARCH_API_KEY` + `YANDEX_FOLDER_ID` | **Yandex Images** (asosiy rasm qidiruvi) | Yandex Cloud → Search API |
| `GOOGLE_API_KEY` + `GOOGLE_CSE_ID` | Google Images (CC filtr bilan) | Programmable Search Engine |
| `YOUTUBE_API_KEY` | YouTube’dagi faqat **Creative Commons** videolar | Google Cloud → YouTube Data API v3 |
| `VK_ACCESS_TOKEN` | VK Video qidiruvi (faqat topish) | vk.com/dev |
| `REDDIT_CLIENT_ID/SECRET` | Reddit qidiruvi (faqat topish) | reddit.com/prefs/apps |

Kalitsiz ham ishlaydi: Internet Archive, Wikimedia Commons, Library of Congress, The Met,
Openverse, YouTube qidiruvi (yt-dlp, faqat topish), Rutube (faqat topish).

---

## 4. Imkoniyatlar

**Tahlil**: sahnalarga ajratish (`# Bob` sarlavhalari, `[Vizual: ...]` izohlari), yillar/asrlar
(rim raqamlari, mil. avv.), joylar, shaxslar, voqealar (uz/ru/en lug‘at), kayfiyat va urg‘ular,
davr bo‘yicha anaxronizm filtri (`media_era`), 3 tilda qidiruv so‘rovlari, narratsiya bo‘yicha vaqt.

**Qidiruv**: 17 provayder, parallel, kesh, takroriy so‘rovlarsiz; reyting = moslik + litsenziya
xavfsizligi + sifat + arxiv/kollektsiya bonusi + davr mosligi − anaxronizm − AI belgilari.

**Huquq**: litsenziya shkalasi 0–4, NC/ND bloklanadi, platforma videolari faqat CC bo‘lsa
yoki ruxsat yozilgan bo‘lsa yuklanadi, Yandex/Google natijalari uchun asl sahifa tekshiriladi,
Fair Use parchalari faqat qo‘lda tasdiqlash bilan (ixtiyoriy).

**Montaj**: sahna kayfiyatiga mos ritm, impact cut (oq chaqnash + zoom), dissolve,
fade-to-black, beat sync, Ken Burns (silliq, jitter’siz), pseudo-parallax, smooth zoom,
4:3 arxiv uchun xira fon bilan pillarbox, sxematik xarita animatsiyasi (marshrut),
kinetik sana kartalari, bob sarlavhalari, lower thirds, subtitrlar, color grading
(4 preset yoki .cube LUT), film grain, vignette, letterbox.

**Manba yozuvlari**: har bir kadrda pastki o‘ng/chap burchakda, kichik, yumshoq fade bilan:
`Manba: Wikimedia Commons / Muallif, CC BY-SA 4.0`, `Archive footage: Internet Archive, Public Domain`,
`Source: X / @username`. Bir xil manbali ketma-ket kadrlar bitta barqaror yozuvga birlashtiriladi.

**Ovoz**: narratsiya kompressiyasi, musiqa ducking (sidechain), ambience, SFX zarbalari,
J/L-cut arxiv ovozi, 2 bosqichli EBU R128 normalizatsiya (−14 LUFS, −1 dBTP).

**Sifat nazorati**: format/kodek/o‘lcham/fps/AAC, davomiylik, loudness, qora kadrlar, sukunat,
muzlagan kadr, har bir kadrda manba borligi, litsenziya xavfi, takroriy kadrlar,
vizual nisbat, anaxronizm/AI belgilari.

---

## 5. Sinov loyihasi

`examples/samarkand_demo/` — «Sohibqiron yurti: Amir Temur va Samarqand» (o‘zbekcha ssenariy,
4 bob, ~72 s). Oflayn (internet va kalitsiz) to‘liq zanjirni sinash:

```bash
python scripts/analyze_script.py --script examples/samarkand_demo/script.txt \
  --title "Sohibqiron yurti: Amir Temur va Samarqand" --project demo \
  --config examples/samarkand_demo/project.yaml
python scripts/make_demo_assets.py --project demo --config examples/samarkand_demo/project.yaml
python scripts/run_pipeline.py --title "Sohibqiron yurti: Amir Temur va Samarqand" --project demo \
  --config examples/samarkand_demo/project.yaml --from beats --preview
```
`make_demo_assets.py` sintetik (CC0) kliplar, rasmlar, musiqa va SFX yaratadi — bu faqat
texnik sinov, YouTube’ga yuklamang. Haqiqiy loyiha uchun `--from search_videos` bilan ishga tushiring.

---

## 6. Moslashtirish

- `config.yaml` — barcha parametrlar; loyiha uchun `project.yaml` bilan ustidan yoziladi (`--config`).
- `templates/source_overlay.json` — manba yozuvi va titrlar uslubi (ASS).
- `templates/youtube_description.md` — tavsif shabloni.
- `scripts/data/lexicon.json` — joylar/shaxslar/atamalar lug‘ati (koordinatalar xarita uchun).
- `assets/fonts/` (o‘z shriftingiz), `assets/music/` (fayl nomida kayfiyat: `epic_…`, `calm_…`,
  `dramatic_…`), `assets/sfx/` (nomlar: `wind`, `impact`, `horses`, `city_ambience`, `crowd_market`,
  `battle_distant`, `train` …), `assets/luts/*.cube` (`render.grade: lut:film.cube`).
  Demo musiqa/SFX sintetik — haqiqiy loyihada CC0/litsenziyali fayllar bilan almashtiring.
- `manual_urls.txt` (loyiha papkasida) — X, Facebook, Mover.uz, Mixkit, muzeylar havolalari:
  `URL | license=CC BY 4.0 | author=@user | scene=s003 | present_day=yes`.

### NLE hand-off (Premiere / DaVinci / CapCut)
`timeline.json` har bir kadr uchun fayl yo‘li, in/out, effekt va o‘tishni saqlaydi;
`render/segments/*.mp4` — tayyor kadrlar, `render/overlays.ass` / `subtitles.srt` — titrlar,
`audio/mix.wav` — tayyor ovoz. Ularni NLE’ga import qilib, qo‘lda yakunlash mumkin.

---

## 7. Cheklovlar (halol hisobot)

- X, Facebook, Mover.uz, Mixkit, Telegram uchun ochiq qidiruv API’si yo‘q → avtomatik qidiruv
  emas, `manual_search_links.md` + `manual_urls.txt` orqali (yt-dlp metadata va yuklash ishlaydi).
- YouTube’dan ko‘proq material: `YOUTUBE_API_KEY` (faqat CC videolar, avtomatik yuklanadi) va
  `python scripts/permission_requests.py --project <slug>` — kanal egalariga tayyor ruxsat xatlari;
  ruxsat kelgach `manual_urls.txt` ga `license=permission` bilan qo‘shiladi. snapyt/savefrom kabi
  yuklovchi saytlar litsenziyani chetlab o‘tgani uchun ishlatilmaydi.
- Rutube, VK, Reddit, YouTube (CC bo‘lmagan) — faqat *topish*; litsenziyasi noma’lum bo‘lgani
  uchun avtomatik yuklanmaydi.
- Yandex/Google — kalit kerak; topilgan rasm faqat asl sahifa litsenziyasi tasdiqlansa ishlatiladi.
- Parallax — haqiqiy 3D qatlamlarsiz pseudo-parallax; xaritalar sxematik (haqiqiy chegaralar emas).
- Avtomatik tahlil lug‘atga asoslangan; sifat uchun agent (Claude) storyboard’ni ko‘rib chiqadi.
- Fair Use — huquqiy himoya emas, qaror inson zimmasida (`references/fair_use.md`).
