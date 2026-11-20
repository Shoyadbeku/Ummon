"""Generate Media_Sources.md and Storyboard.md from remotion/src/timeline.ts."""
import re, glob, json
S = '/tmp/claude-0/-home-user-Ummon/9c80e52c-de78-55fe-9548-5afcf3e773f9/scratchpad'
tl = open('remotion/src/timeline.ts').read(); comps = open('remotion/src/comps.tsx').read()
slug = {}
for f in glob.glob(S + '/mk/*.html') + glob.glob(S + '/mk2/*.html'):
    for m in re.finditer(r'/free-stock-video/([a-z0-9-]+-(\d+))/', open(f, errors='ignore').read()): slug[m.group(2)] = m.group(1)
shots = re.findall(r"^\s*\[([\d.]+), ([\w:'\"]+)", tl.split("export const SHOTS")[1].split("export type Ov")[0], re.M)
script = [(float(a), float(b), c) for a, b, c in (l.split('|', 2) for l in open('data/script_uz.txt').read().strip().split('\n'))]
def fmt(t): return f"{int(t//60)}:{t%60:05.2f}"
used = {}
for t, s in shots:
    s = s.strip("'\""); used.setdefault(s, []).append(float(t))
for m in re.findall(r"v/mk_(\d+)\.mp4", comps): used.setdefault(m, [])
for m in re.findall(r"v/(n_\w+)\.mp4", comps): used.setdefault(m, [])
for m in re.findall(r"img/(\w+)\.jpg", comps): used.setdefault('img:' + m, [])
nasa = {l.split('|')[0]: l.split('|')[1] for l in open('media_raw/nasa/cuts.txt').read().strip().split('\n')}
wiki = {m['file']: m for m in json.load(open('media_raw/wiki/wiki_sources.json'))}
wiki.update({m['file']: m for m in json.load(open('/home/user/Ummon/elon_mask_short/media_raw/wiki/wiki_sources.json'))})
imgmap = {'compaq': 'HewlettPackardCampusHarrisCoTX.jpg', 'eberhard': 'Martin_Eberhard_cropped_.jpg', 'falcon1': 'Falcon_1_Flight_4_liftoff.jpg', 'gigafactory': 'Gigafactory_Texas_Building_1_June_2022.jpg', 'hoover': 'Hoover_Tower_Stanford_January_2013.jpg', 'kimbal': 'KIMBAL_MUSK_OFFICIAL_HEADSHOT_cropped_.jpg', 'merlin': 'SpaceX_Testing_Merlin_1D_Engine_In_Texas.jpg', 'mosaic': 'NCSA_Mosaic_Browser_Screenshot.jpg', 'musk_2015': 'Elon_Musk_2015.jpg', 'musk_dark': 'Elon_Musk_Colorado_2022_cropped2_.jpg', 'musk_royal': 'Elon_Musk_Royal_Society_crop2_.jpg', 'musk_smile': 'USAFA_Hosts_Elon_Musk_Image_1_of_17_cropped_.jpg', 'musk_tesla': 'Elon_Musk_12271225556_.jpg', 'musk_young': 'Elon_Musk_2011_Shankbone.jpg', 'omelek': 'Omelek_Island.jpg', 'palo_alto': 'Ramona_Street_Architectural_District_261_Hamilton_St_Palo_Al.jpg', 'paypal_sj': 'PayPal_San_Jose_Headquarters.jpg', 'roadster': 'Roadster_San_Diego.jpg', 'stanford_church': 'Stanford_Memorial_Church_2025_L1007381.jpg', 'tesla_factory': 'New_Teslas_at_the_factory.jpg', 'tesla_m3': 'Tesla_Model_3_2023_Autofr_hling_Ulm_IMG_9282.jpg'}
ts = lambda k: ', '.join(fmt(t) for t in used[k]) or 'grafik sahna ichida'
o = ['# Media manbalari va litsenziyalar — "Ilon Mask: ofisdan raketalargacha" (8:08)\n',
     'Ijtimoiy tarmoqlardan (X, Facebook, VK, Reddit, YouTube, Rutube, Mover.uz) material **olinmadi** — ulardagi videolardan qayta foydalanish huquqini tekshirib bo\'lmaydi. Pexels/Pixabay ushbu muhitdan 403 xatosi berdi. Faqat litsenziyasi aniq manbalar ishlatildi.\n',
     '## Ovoz\n- Asl ovoz: foydalanuvchi yuklagan `Neytron_yulduzining_aql_bovar_qilmas_og‘irligi_SadoStudio 13.wav` (iCloud) — egasi foydalanuvchi.\n',
     '## NASA videolari (Public Domain; NASA logotipi ishlatilmagan)\n| Kesim | Manba | Videoda |\n|---|---|---|']
for k in sorted(x for x in used if x.startswith('n_')):
    src = nasa.get(k, '').split('/video/')[-1].split('/')[0] if 'nasa.gov' in nasa.get(k, '') else ('KSC-20221005 Crew-5 Highlights' if 'crew5' in nasa.get(k, '') else 'KSC-20210417 Crew-2 Falcon 9 Drone')
    o.append(f"| {k} | images.nasa.gov — {src} | {ts(k)} |")
o += ['\n## Mixkit videolari (Mixkit Stock Video Free License — tijoriy foydalanish mumkin, atribut shart emas) — https://mixkit.co/license/#videoFree\n| ID | Lavha | Videoda |\n|---|---|---|']
for k in sorted((x for x in used if x.isdigit()), key=int):
    o.append(f"| {k} | [{slug.get(k, k)}](https://mixkit.co/free-stock-video/{slug.get(k, k)}/) | {ts(k)} |")
o += ['\n## Rasmlar — Wikimedia Commons\n| Fayl | Manba | Muallif | Litsenziya | Videoda |\n|---|---|---|---|---|']
for k in sorted(x for x in used if x.startswith('img:')):
    m = wiki.get(imgmap.get(k[4:], ''), {})
    o.append(f"| {k[4:]}.jpg | {m.get('page', '?')} | {re.sub(r'[|\\n]', ' ', m.get('author', '') or 'Commons sahifasiga qarang')[:60]} | {m.get('license', '?')} | {ts(k)} |")
o += ['\n**Post tavsifi uchun tayyor atribut qatori (CC BY / CC BY-SA rasmlar uchun majburiy):**',
      '> Photos via Wikimedia Commons: David Shankbone (CC BY 3.0), Steve Jurvetson (CC BY 2.0), Debbie Rowe (CC BY-SA 3.0), King of Hearts (CC BY-SA 3.0), Frank Schulenburg (CC BY-SA 4.0), Sagar Savla (CC BY-SA 3.0), Sanfranman59 (CC BY-SA 3.0), Nicki Dugan (CC BY-SA 2.0), Alexander-93 (CC BY-SA 4.0), Larry D. Moore (CC BY 4.0), SpaceX (CC BY-SA 3.0 / CC0), Kimbal Musk headshot (CC BY-SA 4.0), U.S. Air Force / USGS (PD). Footage: NASA (PD), Mixkit. Music & SFX: Mixkit.\n',
      '## Musiqa (Mixkit Free License) — bob bo\'yicha, 2.5 s crossfade, ovoz ostida sidechain ducking',
      '| Vaqt | Trek |\n|---|---|',
      '| 0:00–0:47 | Silent Descent (mixkit.co/music/614) |', '| 0:47–4:03 | Echoes (mixkit.co/music/188) |', '| 4:03–5:34 | Skyline (mixkit.co/music/601) |', '| 5:34–7:10 | Vastness (mixkit.co/music/184) |', '| 7:10–8:08 | Drawing the Sky (mixkit.co/music/606) |',
      '\n## Ovoz effektlari (Mixkit Free License)\n788, 2908, 1143, 1492, 1490, 166, 772, 3120, 3005, 1053, 1714, 1715, 498, 784 — `https://assets.mixkit.co/active_storage/sfx/<id>/<id>-preview.mp3`\n',
      '## Ma\'lumot manbasi\n- Internet foydalanuvchilari diagrammasi (1995–1999: 16, 36, 70, 147, 248 mln) — Internet World Stats.\n',
      '## Shriftlar\nAnton, Montserrat — Google Fonts (SIL OFL).\n',
      '## Savdo belgilari\nPayPal, Tesla, SpaceX, Zip2, X.com, Compaq, eBay nomlari faqat matn sifatida (hujjatli kontekstda). Rasmiy logotip fayllari ishlatilmagan. "Zip2" brauzer oynasi, shahar xaritasi, diagrammalar — original grafika.']
open('Media_Sources.md', 'w').write('\n'.join(o) + '\n')
# storyboard
sb = ['# Storyboard — 1080×1920, 30 fps, 8:08\n', 'Har bir qator: kadr boshlanishi → ovozdagi gap → vizual. Motion graphics overleylari `remotion/src/timeline.ts` dagi `OVERLAYS` ro\'yxatida.\n', '| Vaqt | Ovoz (shu paytda) | Vizual |\n|---|---|---|']
for i, (t, s) in enumerate(shots):
    t = float(t); s = s.strip("'\"")
    line = next((c for a, b, c in script if a <= t + 0.05 < b + 0.6), '')
    vis = ('Motion graphics: ' + s[5:]) if s.startswith('comp:') else ('Rasm: ' + s[4:]) if s.startswith('img:') else ('NASA: ' + s) if s.startswith('n_') else ('Mixkit: ' + slug.get(s, s))
    sb.append(f"| {fmt(t)} | {line} | {vis} |")
open('Storyboard.md', 'w').write('\n'.join(sb) + '\n')
print(len(shots), 'shots documented')
