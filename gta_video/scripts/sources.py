import json, re, os, urllib.parse
used = json.load(open('deliverables/_usage.json'))
slugs = {}
for l in open('scripts/mixkit_slugs.txt'):
    p = l.split()
    if len(p) == 2: slugs.setdefault(p[0], p[1])
clips = [l.split() for l in open('scripts/mixkit_clips.txt') if l.strip()]
clipinfo = json.load(open('src/data/clips.json'))
meta = [m for m in json.load(open('scripts/commons_meta.json')) if os.path.exists('public/img/' + m['local'])]
art = lambda m: re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', m['artist'] or '')).strip()
name = lambda m: urllib.parse.unquote(m['page'].split('File:')[1]).replace('_', ' ')
L = ['# Media_Sources — manbalar va litsenziyalar\n',
     'Barcha vizual va audio materiallar foydalanishga ruxsat berilgan manbalardan olingan. Ijtimoiy tarmoqlardagi videolar (YouTube, X, VK, Rutube, Mover, Reddit) va GTA o‘yin kadrlari/treylerlari **ishlatilmadi**: ular mualliflik huquqi bilan himoyalangan va qayta foydalanishga ochiq ruxsat yo‘q.\n',
     '## 1. Video — Mixkit (Mixkit Stock Video Free License)\n',
     'Litsenziya: https://mixkit.co/license/#videoFree — tijoriy va notijoriy loyihalarda bepul, atribut talab qilinmaydi.\n',
     '| Fayl | Mixkit ID | Sahifa | Sifat | Sahnalar soni |', '|---|---|---|---|---|']
for cid, n in clips:
    if n not in clipinfo: continue
    ci = clipinfo[n]
    L.append(f"| {n}.mp4 | {cid} | https://mixkit.co/free-stock-video/{slugs.get(cid, '')}-{cid}/ | {ci['w']}x{ci['h']} | {used.get(n, 0)} |")
L += ['\n## 2. Rasmlar — Wikimedia Commons\n', '| Fayl | Muallif | Litsenziya | Manba |', '|---|---|---|---|']
for m in meta:
    L.append(f"| {m['local']} | {art(m)} | {m['license']} | {m['page']} |")
L += ['\nGTA, Grand Theft Auto, Vice City va Rockstar Games logotiplari Rockstar Games / Take-Two Interactive kompaniyasining savdo belgilaridir. Commons ularni oddiy matnli logotip sifatida mualliflik huquqidan tashqari (public domain) deb belgilagan; videoda ular faqat o‘yinlarni **identifikatsiya qilish** uchun ko‘rsatilgan.',
      '\nCC BY / CC BY-SA rasmlar atribut talab qiladi: `deliverables/Attribution.txt` matnini video tavsifiga qo‘shing.',
      '\n## 3. Musiqa — Mixkit (Mixkit Stock Music Free License)\n', 'Litsenziya: https://mixkit.co/license/#musicFree\n',
      '| Vaqt | Trek | Muallif | Fayl |', '|---|---|---|---|',
      '| 00:00–01:24 | Trapanomics | Arulo | public/music/283.mp3 |', '| 01:24–02:49 | Selpan | Eugenio Mininni | public/music/612.mp3 |',
      '| 02:49–04:03 | Cyberpunk City | Alejandro Magaña (A. M.) | public/music/140.mp3 |', '| 04:03–05:11 | Billy the Kid | Arulo | public/music/399.mp3 |',
      '| 05:11–07:10 | We Will Get It | Eugenio Mininni | public/music/598.mp3 |', '| 07:10–08:34 | Delirium | Eugenio Mininni | public/music/605.mp3 |',
      '| 08:34–10:10 | Sparta | Arulo | public/music/370.mp3 |', '| 10:10–11:49 | Epical Drums 03 | Grigoriy Nuzhny | public/music/678.mp3 |',
      '\n## 4. Ovoz effektlari — Mixkit (Mixkit Sound Effects Free License)\n',
      'https://mixkit.co/license/#sfxFree — `public/sfx/` dagi 35 ta fayl; Mixkit ID lari `scripts/sfx_ids.txt` da.',
      '\n## 5. Shriftlar\n', 'Montserrat va Anton — SIL Open Font License 1.1, `public/fonts/` da.',
      '\n## 6. Xarita ma’lumotlari\n', 'Natural Earth (public domain), `world-atlas` npm paketi orqali.',
      '\n## 7. Original grafika\n', 'Yuqoridan ko‘rinadigan piksel-shahar, 2D→3D o‘tish, infografikalar, xaritalar, taymlayn, sanalar kartasi, so‘rovnoma — barchasi shu loyihada Remotion/React kodi bilan noldan chizilgan (o‘yin grafikasidan nusxa emas).',
      '\n## 8. Ovoz\n', 'Original ovoz — foydalanuvchi yuklagan WAV fayl (sun’iy ovoz bilan almashtirilmagan); faqat tozalash va normalizatsiya qilingan.']
open('deliverables/Media_Sources.md', 'w', encoding='utf8').write('\n'.join(L) + '\n')
A = ['Manbalar / Credits:', 'Stock video, musiqa va ovoz effektlari: Mixkit (mixkit.co), Mixkit Free License.']
for m in meta:
    if m['license'] not in ('Public domain', 'CC0'):
        A.append(f"Rasm: “{name(m)}” — {art(m)}, {m['license']}, Wikimedia Commons")
A.append('GTA va Rockstar Games logotiplari — Rockstar Games / Take-Two Interactive savdo belgilari, faqat identifikatsiya uchun.')
open('deliverables/Attribution.txt', 'w', encoding='utf8').write('\n'.join(A) + '\n')
print('ok', len(L))
