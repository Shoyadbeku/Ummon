"""Generate SOURCES.md (credits + licences) and EDIT_PLAN.md (timed scene list) from the final timeline.

usage: python3 make_docs.py   (run from the project root)
"""
import html, json, re, time, urllib.parse, urllib.request

tl = json.load(open('src/timeline.json'))
shots = tl['shots']

def strip(s):
    return html.unescape(re.sub(r'<[^>]+>', ' ', s or '')).replace('\n', ' ').strip()

def fmt(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"

# ---- Mixkit ----
mk = {}
for line in open('scripts/data/mixkit_license_check.txt'):
    slug, lic, dur = line.strip().split('|')
    mk[slug.rsplit('-', 1)[1]] = (slug, lic)

# ---- Wikimedia (full attribution fetched from the Commons API) ----
wm = {json.loads(l)['key']: json.loads(l) for l in open('scripts/data/wm_selected.jsonl')}
wm.setdefault('wadirum', {'key': 'wadirum', 'title': 'File:VIDEO - Wadi Rum.webm'})
wm.setdefault('wadirum2', {'key': 'wadirum2', 'title': 'File:Wadi Rum,video 2014.webm'})
used_wm = sorted({s['src'].split(':', 1)[1] for s in shots if s['src'].startswith('wm:')})
if used_wm:
    titles = '|'.join(wm[k]['title'] for k in used_wm)
    url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({
        'action': 'query', 'titles': titles, 'prop': 'imageinfo', 'iiprop': 'extmetadata|url',
        'iiextmetadatafilter': 'LicenseShortName|Artist|Credit|LicenseUrl', 'format': 'json'})
    for attempt in range(6):
        try:
            data = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'IslamicReelsEditor/1.0 (credits)'})))
            break
        except Exception:
            time.sleep(15 * (attempt + 1))
    else:
        data = {'query': {'pages': {}}}
    by_title = {}
    for p in data['query']['pages'].values():
        ii = (p.get('imageinfo') or [{}])[0]
        m = ii.get('extmetadata', {})
        by_title[p['title']] = dict(lic=strip(m.get('LicenseShortName', {}).get('value')),
                                    licurl=strip(m.get('LicenseUrl', {}).get('value')),
                                    artist=strip(m.get('Artist', {}).get('value')),
                                    page=ii.get('descriptionurl'))
    norm = {t.replace('_', ' '): v for t, v in by_title.items()}
    for k in used_wm:
        wm[k].update(norm.get(wm[k]['title'], {}))

used = {}
for s in shots:
    used.setdefault(s['src'], []).append(fmt(s['start']))

L = ['# Manbalar va litsenziyalar / Sources & licences', '',
     "Barcha vizual materiallar foydalanishga ruxsat berilgan litsenziyalar ostida olindi. "
     "Mixkit'dagi \"Restricted (faqat shaxsiy foydalanish)\" kliplari ataylab chiqarib tashlandi.", '',
     '## 1. Video — Mixkit (Mixkit Free License, tijoriy foydalanishga ruxsat, attribution shart emas)',
     'Litsenziya: https://mixkit.co/license/#videoFree', '',
     '| Klip | Sahifa | Videoda (boshlanish vaqtlari) |', '|---|---|---|']
for src, ts in sorted(used.items()):
    if src.startswith('mk:'):
        slug, lic = mk[src[3:]]
        assert lic == 'Free', src
        L.append(f"| {slug.rsplit('-', 1)[0].replace('-', ' ')} | https://mixkit.co/free-stock-video/{slug}/ | {', '.join(ts)} |")
L += ['', '## 2. Video — Wikimedia Commons', '', '| Fayl | Muallif | Litsenziya | Videoda |', '|---|---|---|---|']
for src, ts in sorted(used.items()):
    if src.startswith('wm:'):
        d = wm[src[3:]]
        page = d.get('page') or 'https://commons.wikimedia.org/wiki/' + urllib.parse.quote(d['title'].replace(' ', '_'))
        L.append(f"| [{d['title'][5:]}]({page}) | {d.get('artist') or strip(d.get('artist', ''))} | {d.get('lic', '')} | {', '.join(ts)} |")
L += ['', "## 3. Qur'on qo'lyozmasi (rasmlar)", '',
      "Chester Beatty Library, CBL Is 1615(I) — ilk Hijoziy xatdagi Qur'on qo'lyozmasi varaqlari.",
      'Manba: https://archive.org/details/cbl_hijazi_maghrebi_quran_manuscript_1 — Public Domain Mark 1.0', '',
      '| Kalit | Sahifa | Videoda |', '|---|---|---|']
pages = {'ms1': '0009', 'ms2': '0004', 'ms3': '0012', 'ms4': '0025', 'ms5': '0010', 'ms6': '0038', 'ms7': '0037', 'ms8': '0042'}
for src, ts in sorted(used.items()):
    if src.startswith('img:'):
        k = src[4:]
        L.append(f"| {k} | jp2 #{pages.get(k, '?')} | {', '.join(ts)} |")
L += ['',
      "Eslatma: qo'lyozma varaqlari umumiy ramziy tasvir sifatida ishlatilgan; ular aynan Qasas surasining shu oyatlari yozilgan sahifalar emas.",
      '', '## 4. Motion graphics', '',
      "Oltin kalitlar, yer yorilishi, islomiy geometrik naqsh, nur, zarrachalar, film grain — barchasi Remotion'da kod bilan yaratilgan (`src/fx/`).",
      '', '## 5. Ovoz effektlari', '',
      "Barcha SFX (shamol foni, whoosh, impact, yer gumburlashi, momaqaldiroq, riser, shimmer) `scripts/synth_sfx.py` orqali sintez qilingan — tashqi namunalar ishlatilmagan. Fon musiqasi yo'q.",
      '', '## 6. Shriftlar', '',
      '- Amiri (Khaled Hosny) — SIL Open Font License 1.1',
      '- Cormorant Garamond (Christian Thalmann) — SIL Open Font License 1.1', '']
open('SOURCES.md', 'w').write('\n'.join(L))

P = ['# Montaj rejasi / Edit decision list', '',
     f"Davomiylik: {fmt(tl['duration'])} · {len(shots)} ta sahna · 1080×1920 · {tl['fps']} fps", '',
     '| # | Vaqt | Ovozda (qisqacha) | Kadr | Kamera | O‘tish | Effektlar |', '|---|---|---|---|---|---|---|']
for i, s in enumerate(shots):
    P.append(f"| {i + 1} | {fmt(s['start'])}–{fmt(s['end'])} | {s['note']} | `{s['src']}` | {s['mv']} | {s['tr']} | {', '.join(s['fx'])}{' · ' + s['badge'][1] if s.get('badge') else ''} |")
open('EDIT_PLAN.md', 'w').write('\n'.join(P) + '\n')
print('docs written')
