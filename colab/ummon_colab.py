# Ummon Shorts — Colab versiyasi. Whisper GPU'da ishlaydi, subtitrlar ffmpeg (libass) bilan kuydiriladi.
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.request

import gradio as gr

WORK = os.environ.get('UMMON_WORK', '/content/ummon_work')
FONTS = os.path.join(WORK, 'fonts')
os.makedirs(FONTS, exist_ok=True)

# ---------------------------------------------------------------- shriftlar

GF = 'https://raw.githubusercontent.com/google/fonts/main/ofl/'
# (fayl nomi, URL, qalinlik yoki None) — o‘zgaruvchan shriftlardan kerakli qalinlik ajratib olinadi
FONT_SOURCES = {
    'Ummon Montserrat 900': (GF + 'montserrat/Montserrat%5Bwght%5D.ttf', 900),
    'Ummon Montserrat 800': (GF + 'montserrat/Montserrat%5Bwght%5D.ttf', 800),
    'Ummon Manrope 800': (GF + 'manrope/Manrope%5Bwght%5D.ttf', 800),
    'Ummon Manrope 600': (GF + 'manrope/Manrope%5Bwght%5D.ttf', 600),
    'Ummon Bebas Neue': (GF + 'bebasneue/BebasNeue-Regular.ttf', None),
    'Ummon Unbounded 700': (GF + 'unbounded/Unbounded%5Bwght%5D.ttf', 700),
    'Ummon Unbounded 500': (GF + 'unbounded/Unbounded%5Bwght%5D.ttf', 500),
    'Ummon Playfair 700': (GF + 'playfairdisplay/PlayfairDisplay-Italic%5Bwght%5D.ttf', 700),
    'Ummon Caveat 700': (GF + 'caveat/Caveat%5Bwght%5D.ttf', 700),
}


def ensure_fonts():
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    cache = {}
    for family, (url, wght) in FONT_SOURCES.items():
        out = os.path.join(FONTS, family.replace(' ', '') + '.ttf')
        if os.path.exists(out):
            continue
        if url not in cache:
            src = os.path.join(FONTS, '_src_' + str(abs(hash(url))) + '.ttf')
            urllib.request.urlretrieve(url, src)
            cache[url] = src
        font = TTFont(cache[url])
        if wght is not None and 'fvar' in font:
            font = instancer.instantiateVariableFont(font, {'wght': wght})
        # libass shriftni oila nomi bo‘yicha topadi, shuning uchun nomni o‘zimiz beramiz
        name = font['name']
        for rec in list(name.names):
            if rec.nameID in (16, 17, 21, 22, 25):
                name.removeNames(nameID=rec.nameID)
        for nid, val in ((1, family), (2, 'Regular'), (4, family), (6, family.replace(' ', '') + '-Regular')):
            name.setName(val, nid, 3, 1, 0x409)
            name.setName(val, nid, 1, 0, 0)
        if 'OS/2' in font:
            font['OS/2'].fsSelection = (font['OS/2'].fsSelection & ~0b1100001) | 0b1000000  # REGULAR
            font['head'].macStyle = 0
        font.save(out)
    for f in os.listdir(FONTS):
        if f.startswith('_src_'):
            os.remove(os.path.join(FONTS, f))


# ---------------------------------------------------------------- uslublar (js/templates.js bilan bir xil)

STYLES = [
    dict(id='karaoke', name='Karaoke', font='Ummon Montserrat 900', size=0.075, color='#ffffff', active='#ffd43b',
         stroke=0.14, strokeColor='#000000', upper=False, anim='karaoke', maxWords=4),
    dict(id='pop', name='Pop', font='Ummon Montserrat 900', size=0.085, color='#ffffff', active='#7cff4f',
         stroke=0.16, strokeColor='#000000', upper=True, anim='pop', maxWords=3),
    dict(id='highlight', name='Belgilash', font='Ummon Montserrat 800', size=0.07, color='#ffffff', active='#ffffff',
         activeBg='#6e5bff', stroke=0.12, strokeColor='#000000', upper=False, anim='highlight', maxWords=4),
    dict(id='classic', name='Klassik', font='Ummon Manrope 800', size=0.058, color='#ffffff', active='#ffffff',
         stroke=0.12, strokeColor='#000000', upper=False, anim='none', maxWords=0),
    dict(id='box', name='Qutichali', font='Ummon Manrope 800', size=0.056, color='#ffffff', active='#ffffff',
         box=True, boxColor='rgba(0,0,0,0.72)', upper=False, anim='fade', maxWords=0),
    dict(id='headline', name='Sarlavha', font='Ummon Bebas Neue', size=0.13, color='#ffd43b', active='#ffffff',
         stroke=0.06, strokeColor='#000000', shadow=18, shadowColor='rgba(0,0,0,0.6)', upper=True, anim='bounce', maxWords=2),
    dict(id='neon', name='Neon', font='Ummon Unbounded 700', size=0.062, color='#c9fbff', active='#00f0ff',
         shadow=22, shadowColor='#00e5ff', upper=False, anim='karaoke', maxWords=3),
    dict(id='typewriter', name='Mashinka', font='Ummon Unbounded 500', size=0.052, color='#ffffff', active='#ffb23f',
         box=True, boxColor='rgba(19,17,27,0.85)', upper=False, anim='typewriter', maxWords=0),
    dict(id='minimal', name='Minimal', font='Ummon Manrope 600', size=0.044, color='#ffffff', active='#ffffff',
         shadow=8, shadowColor='rgba(0,0,0,0.9)', upper=False, anim='none', maxWords=0, pos=0.86),
    dict(id='cinema', name='Kino', font='Ummon Playfair 700', italic=True, size=0.058, color='#fff4dc', active='#fff4dc',
         shadow=10, shadowColor='rgba(0,0,0,0.9)', upper=False, anim='fade', maxWords=0, pos=0.84),
    dict(id='handwritten', name='Qo‘lyozma', font='Ummon Caveat 700', size=0.1, color='#ffffff', active='#ffb3d9',
         stroke=0.08, strokeColor='rgba(0,0,0,0.6)', upper=False, anim='karaoke', maxWords=3),
    dict(id='bold-box', name='Lenta', font='Ummon Montserrat 900', size=0.07, color='#13111b', active='#13111b',
         box=True, boxColor='#ffb23f', perLineBox=True, upper=True, anim='bounce', maxWords=3),
]
STYLE_BY_NAME = {s['name']: s for s in STYLES}

TEMPLATES = {
    'Reels hook (9:16)': dict(aspect='9:16', fit='To‘ldirish', style='Pop', hook='Buni bilmasangiz, vaqt yo‘qotasiz'),
    'YouTube Shorts (9:16)': dict(aspect='9:16', fit='To‘ldirish', style='Karaoke', hook=''),
    'Podkast klip (16:9 → 9:16)': dict(aspect='9:16', fit='Xira fon', style='Qutichali', hook='Podkast · 12-son'),
    'Instagram post (1:1)': dict(aspect='1:1', fit='To‘ldirish', style='Belgilash', hook=''),
    'Dars (16:9)': dict(aspect='16:9', fit='Qora fon', style='Minimal', hook='3-dars: Excel asoslari'),
    'Mahsulot reklamasi (9:16)': dict(aspect='9:16', fit='To‘ldirish', style='Sarlavha', hook='Yangi kolleksiya · 30% chegirma'),
    'Kino iqtibos (16:9)': dict(aspect='16:9', fit='To‘ldirish', style='Kino', hook=''),
    'Vlog (4:5)': dict(aspect='4:5', fit='To‘ldirish', style='Qo‘lyozma', hook='Toshkentda bir kun'),
}

ASPECTS = ['Asl', '9:16', '1:1', '4:5', '16:9']
FITS = ['To‘ldirish', 'Xira fon', 'Qora fon']
MAXWORDS = ['Uslub bo‘yicha', '1', '2', '3', '4', '5', '6', 'Butun gap']

# ---------------------------------------------------------------- lotin ⇄ kirill (js/translit.js dan)

CYR_TO_LAT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'ж': 'j', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l',
    'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'x', 'ц': 's',
    'ч': 'ch', 'ш': 'sh', 'щ': 'sh', 'ъ': '’', 'ь': '', 'ы': 'i', 'э': 'e', 'ю': 'yu', 'я': 'ya', 'ё': 'yo',
    'ў': 'o‘', 'қ': 'q', 'ғ': 'g‘', 'ҳ': 'h',
}
VOWELS_CYR = 'аеёиоуўэюяы'
CYR_RE = re.compile('[Ѐ-ӿ]')


def to_latin(text):
    out = []
    for i, ch in enumerate(text):
        low = ch.lower()
        upper = ch != low
        prev = text[i - 1].lower() if i > 0 else ' '
        if low == 'е':
            r = 'ye' if (not re.match('[Ѐ-ӿa-z]', prev) or prev in VOWELS_CYR or prev in 'ъь') else 'e'
        elif low == 'ц':
            r = 'ts' if (not CYR_RE.match(prev) or prev in VOWELS_CYR) else 's'
        elif low in CYR_TO_LAT:
            r = CYR_TO_LAT[low]
        else:
            out.append(ch)
            continue
        if upper and r:
            nxt = text[i + 1] if i + 1 < len(text) else ''
            next_upper = nxt and nxt != nxt.lower()
            r = r.upper() if (next_upper or len(r) == 1) else r[0].upper() + r[1:]
        out.append(r)
    return ''.join(out)


APOS = "['‘’ʻʼ`]"
LAT_RULES = [
    ('o' + APOS, 'ў'), ('O' + APOS, 'Ў'), ('g' + APOS, 'ғ'), ('G' + APOS, 'Ғ'),
    ('sh', 'ш'), ('S[hH]', 'Ш'), ('ch', 'ч'), ('C[hH]', 'Ч'),
    ('yo', 'ё'), ('Y[oO]', 'Ё'), ('yu', 'ю'), ('Y[uU]', 'Ю'), ('ya', 'я'), ('Y[aA]', 'Я'),
    ('ye', 'е'), ('Y[eE]', 'Е'), (r'(?<![^\W\d_])e', 'э'), (r'(?<![^\W\d_])E', 'Э'), (APOS, 'ъ'),
]
LAT_SINGLE = dict(zip('abvgdejzyiklmnoprstufxqhcw', 'абвгдежзйиклмнопрстуфхқҳсв'))


def to_cyrillic(text):
    s = text
    for pat, rep in LAT_RULES:
        s = re.sub(pat, rep, s)
    out = []
    for ch in s:
        low = ch.lower()
        if low in LAT_SINGLE:
            r = LAT_SINGLE[low]
            out.append(r if ch == low else r.upper())
        else:
            out.append(ch)
    return ''.join(out)


def normalize_apostrophes(text):
    return re.sub(r"([oOgG])['ʻʼ`’]", '\\1‘', text)


def convert_script(text, script):
    if script == 'Lotin':
        return normalize_apostrophes(to_latin(text))
    if script == 'Kirill':
        return to_cyrillic(to_latin(text))
    return text


# ---------------------------------------------------------------- Whisper

_model = {'name': None, 'obj': None}


def load_model(name, cpu=False):
    key = (name, cpu)
    if _model['name'] == key:
        return _model['obj']
    from faster_whisper import WhisperModel
    _model['obj'] = None
    try:
        import ctranslate2
        if not cpu and ctranslate2.get_cuda_device_count() > 0:
            m = WhisperModel(name, device='cuda', compute_type='float16')
        else:
            raise RuntimeError('GPU yo‘q')
    except Exception as e:  # noqa: BLE001
        print('GPU ishlamadi, CPU ishlatiladi:', e)
        m = WhisperModel(name, device='cpu', compute_type='int8')
    _model.update(name=key, obj=m)
    return m


def load_audio(path):
    # PyAV versiyalariga bog‘liq bo‘lmaslik uchun audio ffmpeg bilan o‘qiladi
    import numpy as np
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vn', '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def transcribe(path, model_name, progress=None):
    audio = load_audio(path)
    if audio.size < 1600:
        return []
    try:
        return _transcribe(audio, load_model(model_name), progress)
    except RuntimeError as e:
        # masalan, cuDNN topilmasa — CPU da qayta urinib ko‘ramiz
        print('GPU xatosi, CPU da davom etiladi:', e)
        return _transcribe(audio, load_model(model_name, cpu=True), progress)


def _transcribe(audio, m, progress):
    segs, info = m.transcribe(
        audio, language='uz', task='transcribe', word_timestamps=True, vad_filter=True, beam_size=5,
        initial_prompt='Assalomu alaykum, do‘stlar! Bugun o‘zbek tilida gaplashamiz.',
    )
    out = []
    for s in segs:
        words = [dict(w=w.word.strip(), s=round(w.start, 3), e=round(w.end, 3)) for w in (s.words or []) if w.word.strip()]
        if not words:
            continue
        out.append(dict(start=words[0]['s'], end=words[-1]['e'], text=' '.join(w['w'] for w in words), words=words))
        if progress and info.duration:
            progress(min(1.0, s.end / info.duration), desc=f'Matnga aylantirilmoqda… {int(s.end)}/{int(info.duration)} s')
    return out


def split_long(segments, max_words=10, max_gap=0.8):
    """Whisper'ning uzun bo‘laklarini ekranga sig‘adigan gaplarga bo‘lish."""
    out = []
    for seg in segments:
        cur = []
        for w in seg['words']:
            if cur and (len(cur) >= max_words or w['s'] - cur[-1]['e'] > max_gap):
                out.append(cur)
                cur = []
            cur.append(w)
            if re.search(r'[.!?…]$', w['w']) and len(cur) >= 3:
                out.append(cur)
                cur = []
        if cur:
            out.append(cur)
    return [dict(start=c[0]['s'], end=c[-1]['e'], text=' '.join(w['w'] for w in c), words=c) for c in out]


# ---------------------------------------------------------------- SRT / VTT

def ts(t, sep=','):
    t = max(0.0, t)
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}'


def to_srt(segs):
    return '\n'.join(f'{i}\n{ts(s["start"])} --> {ts(s["end"])}\n{s["text"]}\n' for i, s in enumerate(segs, 1))


def to_vtt(segs):
    return 'WEBVTT\n\n' + '\n'.join(f'{ts(s["start"], ".")} --> {ts(s["end"], ".")}\n{s["text"]}\n' for s in segs)


TIME_RE = re.compile(r'(\d+):(\d{1,2}):(\d{1,2})[,.](\d{1,3})\s*-->\s*(\d+):(\d{1,2}):(\d{1,2})[,.](\d{1,3})')


def parse_srt(text):
    segs = []
    for block in re.split(r'\n\s*\n', text.replace('\r', '').strip()):
        lines = [l for l in block.split('\n') if l.strip()]
        for i, line in enumerate(lines):
            m = TIME_RE.search(line)
            if m:
                g = [int(x) for x in m.groups()]
                start = g[0] * 3600 + g[1] * 60 + g[2] + int(m.group(4).ljust(3, '0')) / 1000
                end = g[4] * 3600 + g[5] * 60 + g[6] + int(m.group(8).ljust(3, '0')) / 1000
                body = ' '.join(lines[i + 1:]).strip()
                if body and end > start:
                    segs.append(dict(start=start, end=end, text=body))
                break
    return segs


def attach_words(segs, known):
    """Tahrirlangan SRT ga so‘z vaqtlarini qo‘shish: o‘zgarmagan gaplar Whisper vaqtini saqlaydi,
    o‘zgarganlarida vaqt so‘z uzunligiga qarab bo‘linadi."""
    index = {(round(k['start'], 2), round(k['end'], 2), k['text']): k['words'] for k in (known or [])}
    for s in segs:
        words = index.get((round(s['start'], 2), round(s['end'], 2), s['text']))
        if words and len(words) == len(s['text'].split()):
            s['words'] = [dict(w) for w in words]
            continue
        toks = s['text'].split()
        total = sum(len(t) + 1 for t in toks) or 1
        t, dur, ws = s['start'], s['end'] - s['start'], []
        for tok in toks:
            d = dur * (len(tok) + 1) / total
            ws.append(dict(w=tok, s=t, e=t + d))
            t += d
        s['words'] = ws
    return segs


# ---------------------------------------------------------------- ASS

def ass_color(c):
    """'#rrggbb' yoki 'rgba(r,g,b,a)' → (&HBBGGRR&, alfa 00..FF)."""
    c = c.strip()
    if c.startswith('#'):
        r, g, b, a = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), 1.0
    else:
        p = [float(x) for x in re.findall(r'[\d.]+', c)]
        r, g, b = (int(x) for x in p[:3])
        a = p[3] if len(p) > 3 else 1.0
    return f'&H{b:02X}{g:02X}{r:02X}&', f'&H{int(round((1 - a) * 255)):02X}&'


def ass_full(c):
    col, alpha = ass_color(c)
    return '&H' + alpha[2:4] + col[2:8]


def esc(t):
    return t.replace('\\', '＼').replace('{', '(').replace('}', ')')


def build_ass(segs, W, H, st, font_scale=1.0, pos=None, max_words=None, hook=''):
    px = round(min(W, H) * st['size'] * font_scale)
    pos = pos if pos is not None else st.get('pos', 0.72)
    mw = st['maxWords'] if max_words is None else max_words
    bord, shad, blur, border_style = 0.0, 0.0, 0.0, 1
    outline_col = st.get('strokeColor', '#000000')
    if st.get('stroke'):
        bord = px * st['stroke'] / 2
    if st.get('shadow'):
        # canvas shadowBlur ≈ libass \blur; kontur bo‘lmasa yupqa xira kontur soya vazifasini bajaradi
        blur = st['shadow'] * (px / 50) / 3
        if not st.get('stroke'):
            bord = max(1.0, px * 0.07)
            outline_col = st['shadowColor']
    if st.get('box'):
        border_style, bord, blur = 3, px * 0.22, 0
        outline_col = st['boxColor']
    italic = -1 if st.get('italic') else 0
    margin = round(W * 0.07)

    def style_line(name, font, size, prim, sec, outl, back, bs, b, s):
        return (f'Style: {name},{font},{size},{ass_full(prim)},{ass_full(sec)},{ass_full(outl)},{ass_full(back)},'
                f'0,{italic if name == "Cap" else 0},0,0,100,100,0,0,{bs},{b:.1f},{s:.1f},5,{margin},{margin},0,1')

    head = [
        '[Script Info]', 'ScriptType: v4.00+', f'PlayResX: {W}', f'PlayResY: {H}', 'WrapStyle: 0',
        'ScaledBorderAndShadow: yes', 'YCbCr Matrix: TV.709', '',
        '[V4+ Styles]',
        'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, '
        'Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, '
        'MarginR, MarginV, Encoding',
        style_line('Cap', st['font'], px, st['color'], st['active'], outline_col, 'rgba(0,0,0,0.6)', border_style, bord, shad),
        style_line('Hook', 'Ummon Montserrat 800', round(min(W, H) * 0.052), '#13111b', '#13111b', '#ffffff',
                   '#ffffff', 3, min(W, H) * 0.02, 0),
        '', '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
    ]

    def at(t):
        cs = int(round(max(0.0, t) * 100))
        h, cs = divmod(cs, 360000)
        m, cs = divmod(cs, 6000)
        s, cs = divmod(cs, 100)
        return f'{h}:{m:02d}:{s:02d}.{cs:02d}'

    events = []

    glow = bool(st.get('shadow')) and not st.get('stroke') and not st.get('box')

    def add(start, end, text, style='Cap', layer=0):
        if end - start < 0.01:
            return
        events.append(f'Dialogue: {layer},{at(start)},{at(end)},{style},,0,0,0,,{text}')
        if glow and style == 'Cap':
            # porlash pastki qatlamda, aniq matn ustida
            crisp = text.replace('}', '\\bord0\\blur0}', 1)
            events.append(f'Dialogue: {layer + 1},{at(start)},{at(end)},{style},,0,0,0,,{crisp}')

    base = f'\\an5\\pos({W // 2},{round(H * pos)})' + (f'\\blur{blur:.1f}' if blur else '')
    main_c = ass_color(st['color'])[0]
    act_c = ass_color(st['active'])[0]
    anim = st['anim']

    for si, seg in enumerate(segs):
        words = seg['words']
        if not words:
            continue
        if st.get('upper'):
            words = [dict(w, w=w['w'].upper()) for w in words]
        chunks = [words[i:i + mw] for i in range(0, len(words), mw)] if mw > 0 else [words]
        nxt_seg = segs[si + 1]['start'] if si + 1 < len(segs) else None
        for ci, chunk in enumerate(chunks):
            c_start = chunk[0]['s'] if ci else seg['start']
            if ci + 1 < len(chunks):
                c_end = chunks[ci + 1][0]['s']
            else:
                c_end = max(seg['end'], chunk[-1]['e'])
                if nxt_seg is not None and 0 < nxt_seg - c_end < 0.6:
                    c_end = nxt_seg
            intro = ''
            if anim == 'bounce':
                intro = '\\fscx60\\fscy60\\t(0,220,\\fscx100\\fscy100)'
            elif anim == 'fade' and ci == 0:
                intro = '\\fad(250,0)'

            if anim in ('none', 'fade'):
                add(c_start, c_end, '{' + base + intro + '}' + esc(' '.join(w['w'] for w in chunk)))
                continue

            for wi, w in enumerate(chunk):
                w_start = c_start if wi == 0 else w['s']
                w_end = chunk[wi + 1]['s'] if wi + 1 < len(chunk) else c_end
                parts = []
                for k, o in enumerate(chunk):
                    t = esc(o['w'])
                    if anim == 'karaoke':
                        parts.append(f'{{\\c{act_c if k <= wi else main_c}}}{t}')
                    elif anim == 'pop':
                        parts.append(f'{{\\c{act_c}\\fscx114\\fscy114}}{t}{{\\c{main_c}\\fscx100\\fscy100}}' if k == wi else t)
                    elif anim == 'bounce':
                        parts.append(f'{{\\c{act_c}}}{t}{{\\c{main_c}}}' if k == wi else t)
                    elif anim == 'highlight':
                        hb = ass_color(st['activeBg'])[0]
                        parts.append(f'{{\\3c{hb}\\bord{px * 0.2:.1f}}}{t}{{\\3c{ass_color(st["strokeColor"])[0]}\\bord{bord:.1f}}}'
                                     if k == wi else t)
                    elif anim == 'typewriter':
                        if k <= wi:
                            parts.append(t)
                    else:
                        parts.append(t)
                add(w_start, w_end, '{' + base + (intro if wi == 0 else '') + '}' + ' '.join(parts))

    if hook.strip() and segs:
        end = max(s['end'] for s in segs) + 1
        add(0, end, f'{{\\an8\\pos({W // 2},{round(H * 0.08)})}}' + esc(hook.strip()), style='Hook', layer=1)
    return '\n'.join(head + events) + '\n'


# ---------------------------------------------------------------- video

def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                          'stream=width,height:stream_tags=rotate:stream_side_data=rotation:format=duration',
                          '-of', 'json', path], capture_output=True, text=True).stdout
    info = json.loads(out or '{}')
    st = (info.get('streams') or [{}])[0]
    w, h = st.get('width', 1280), st.get('height', 720)
    rot = 0
    for sd in st.get('side_data_list', []) or []:
        rot = int(sd.get('rotation', 0) or 0)
    rot = rot or int((st.get('tags') or {}).get('rotate', 0) or 0)
    if abs(rot) % 180 == 90:
        w, h = h, w
    return w, h, float((info.get('format') or {}).get('duration', 0) or 0)


def even(x):
    return max(2, int(round(x / 2)) * 2)


def out_size(src_w, src_h, aspect, short):
    if aspect == 'Asl':
        s = min(short, min(src_w, src_h))
        k = s / min(src_w, src_h)
        return even(src_w * k), even(src_h * k)
    a, b = (int(x) for x in aspect.split(':'))
    return (even(short), even(short * b / a)) if a <= b else (even(short * a / b), even(short))


_encoder = {}


def video_encoder():
    if 'v' not in _encoder:
        ok = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=s=256x256:d=0.2', '-c:v', 'h264_nvenc',
                             '-f', 'null', '-'], capture_output=True).returncode == 0
        _encoder['v'] = (['-c:v', 'h264_nvenc', '-preset', 'p5', '-cq', '21', '-b:v', '0'] if ok
                         else ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20'])
    return _encoder['v']


def filter_graph(W, H, fit, ass_path):
    sub = f"ass='{ass_path}':fontsdir='{FONTS}'"
    if fit == 'Xira fon':
        return (f'[0:v]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=24:2[bg];'
                f'[b]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,'
                f'setsar=1,format=yuv420p,{sub}[v]')
    if fit == 'Qora fon':
        return (f'[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,'
                f'setsar=1,format=yuv420p,{sub}[v]')
    return f'[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,format=yuv420p,{sub}[v]'


def run_ffmpeg(args, duration=None, progress=None, desc=''):
    proc = subprocess.Popen(['ffmpeg', '-y', '-hide_banner', '-v', 'error', '-progress', 'pipe:1', '-nostats'] + args,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    for line in proc.stdout:
        if progress and duration and line.startswith('out_time_us='):
            try:
                progress(min(1.0, int(line.split('=')[1]) / 1e6 / duration), desc=desc)
            except ValueError:
                pass
    err = proc.stderr.read()
    if proc.wait() != 0:
        raise gr.Error('ffmpeg xatosi: ' + err[-800:])


# ---------------------------------------------------------------- Gradio

def ui_transcribe(video, model, script, state, progress=gr.Progress()):
    if not video:
        raise gr.Error('Avval video yuklang.')
    progress(0, desc='Model yuklanmoqda (birinchi marta 1–3 daqiqa)…')
    segs = split_long(transcribe(video, model, progress))
    if not segs:
        raise gr.Error('Videoda nutq topilmadi.')
    for s in segs:
        for w in s['words']:
            w['w'] = convert_script(w['w'], script)
        s['text'] = ' '.join(w['w'] for w in s['words'])
    return to_srt(segs), segs


def ui_load_srt(file):
    if not file:
        return gr.update()
    with open(file, encoding='utf-8-sig', errors='replace') as f:
        return to_srt(parse_srt(f.read()))


def ui_template(name):
    t = TEMPLATES[name]
    return t['aspect'], t['fit'], t['style'], t['hook']


def prepare(video, srt_text, state, style_name, aspect, fit, quality, hook, font_scale, pos, maxw, script):
    if not video:
        raise gr.Error('Avval video yuklang.')
    segs = parse_srt(srt_text or '')
    if not segs:
        raise gr.Error('Subtitr bo‘sh. Avval «Subtitr yaratish» ni bosing yoki SRT yuklang.')
    segs = attach_words(segs, state)
    if script != 'Asl':
        for s in segs:
            for w in s['words']:
                w['w'] = convert_script(w['w'], script)
            s['text'] = ' '.join(w['w'] for w in s['words'])
        hook = convert_script(hook or '', script)
    st = STYLE_BY_NAME[style_name]
    mw = None if maxw == MAXWORDS[0] else (0 if maxw == MAXWORDS[-1] else int(maxw))
    src_w, src_h, dur = probe(video)
    W, H = out_size(src_w, src_h, aspect, 1080 if quality.startswith('1080') else 720)
    job = tempfile.mkdtemp(dir=WORK, prefix='job_')
    ass = os.path.join(job, 'subtitr.ass')
    with open(ass, 'w', encoding='utf-8') as f:
        f.write(build_ass(segs, W, H, st, font_scale, pos, mw, hook or ''))
    return segs, W, H, dur, job, ass


def ui_preview(video, srt_text, state, style_name, aspect, fit, quality, hook, font_scale, pos, maxw, script, at_sec):
    segs, W, H, dur, job, ass = prepare(video, srt_text, state, style_name, aspect, fit, quality, hook, font_scale,
                                        pos, maxw, script)
    t = at_sec if at_sec is not None and at_sec >= 0 else (segs[0]['words'][0]['e'] + 0.05)
    t = min(t, max(0, dur - 0.1)) if dur else t
    out = os.path.join(job, 'kadr.jpg')
    # -ss ni kirishdan keyin qo‘yamiz, shunda subtitr vaqti video vaqti bilan bir xil bo‘ladi
    run_ffmpeg(['-i', video, '-filter_complex', filter_graph(W, H, fit, ass), '-map', '[v]', '-ss', f'{t:.2f}',
                '-frames:v', '1', '-q:v', '3', out])
    return out


def ui_render(video, srt_text, state, style_name, aspect, fit, quality, hook, font_scale, pos, maxw, script,
              progress=gr.Progress()):
    segs, W, H, dur, job, ass = prepare(video, srt_text, state, style_name, aspect, fit, quality, hook, font_scale,
                                        pos, maxw, script)
    base = os.path.splitext(os.path.basename(video))[0][:40] or 'video'
    mp4 = os.path.join(job, f'{base}_ummon.mp4')
    if progress:
        progress(0, desc='Video tayyorlanmoqda…')
    run_ffmpeg(['-i', video, '-filter_complex', filter_graph(W, H, fit, ass), '-map', '[v]', '-map', '0:a?']
               + video_encoder() + ['-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', mp4],
               dur, progress, 'Video tayyorlanmoqda…')
    files = [mp4]
    for ext, data in (('srt', to_srt(segs)), ('vtt', to_vtt(segs)), ('txt', '\n'.join(s['text'] for s in segs) + '\n')):
        p = os.path.join(job, f'{base}.{ext}')
        with open(p, 'w', encoding='utf-8') as f:
            f.write(data)
        files.append(p)
    final_ass = os.path.join(job, f'{base}.ass')
    shutil.copy(ass, final_ass)
    files.append(final_ass)
    return mp4, files


CSS = '#title{text-align:center} #title h1{margin-bottom:0}'


def build_app():
    with gr.Blocks(title='Ummon Shorts') as app:
        gr.Markdown('# Ummon Shorts\nO‘zbekcha AI subtitr · Colab GPU', elem_id='title')
        state = gr.State([])
        with gr.Row():
            with gr.Column(scale=1):
                video = gr.Video(label='1. Video (MP4, MOV, WEBM)', sources=['upload'])
                with gr.Row():
                    model = gr.Dropdown(['large-v3', 'large-v3-turbo', 'medium', 'small'], value='large-v3',
                                        label='Whisper modeli', info='large-v3 — eng aniq, turbo — tezroq')
                    script = gr.Radio(['Lotin', 'Kirill', 'Asl'], value='Lotin', label='Yozuv')
                btn_tr = gr.Button('Subtitr yaratish', variant='primary')
                srt_file = gr.File(label='yoki tayyor SRT yuklang', file_types=['.srt'], height=90)
                srt = gr.Textbox(label='2. Subtitrlar (tahrirlash mumkin)', lines=14, max_lines=30,
                                 placeholder='1\n00:00:00,200 --> 00:00:02,600\nAssalomu alaykum, do‘stlar!')
            with gr.Column(scale=1):
                template = gr.Dropdown(list(TEMPLATES), value=None, label='3. Shablon (ixtiyoriy)')
                with gr.Row():
                    style = gr.Dropdown([s['name'] for s in STYLES], value='Karaoke', label='Subtitr uslubi')
                    maxw = gr.Dropdown(MAXWORDS, value=MAXWORDS[0], label='Ekranda so‘z soni')
                with gr.Row():
                    aspect = gr.Radio(ASPECTS, value='9:16', label='Format')
                    fit = gr.Radio(FITS, value='To‘ldirish', label='Sig‘dirish')
                hook = gr.Textbox(label='Sarlavha (hook)', placeholder='Bo‘sh qoldirsa bo‘ladi')
                with gr.Row():
                    font_scale = gr.Slider(0.6, 1.6, value=1.0, step=0.05, label='Shrift o‘lchami')
                    pos = gr.Slider(0.1, 0.92, value=0.72, step=0.01, label='Balandlik (0 — tepa, 1 — past)')
                quality = gr.Radio(['720p', '1080p'], value='1080p', label='Sifat')
                with gr.Row():
                    at_sec = gr.Number(value=-1, label='Kadr soniyasi (-1 = avto)', precision=1)
                    btn_prev = gr.Button('Kadrni ko‘rish')
                preview = gr.Image(label='Ko‘rinish', height=360)
                btn_go = gr.Button('4. Videoni tayyorlash', variant='primary')
                out_video = gr.Video(label='Natija')
                out_files = gr.File(label='Yuklab olish: MP4, SRT, VTT, TXT, ASS', file_count='multiple')

        btn_tr.click(ui_transcribe, [video, model, script, state], [srt, state])
        srt_file.upload(ui_load_srt, srt_file, srt)
        template.change(ui_template, template, [aspect, fit, style, hook])
        style.change(lambda n: STYLE_BY_NAME[n].get('pos', 0.72), style, pos)
        common = [video, srt, state, style, aspect, fit, quality, hook, font_scale, pos, maxw, script]
        btn_prev.click(ui_preview, common + [at_sec], preview)
        btn_go.click(ui_render, common, [out_video, out_files])
    return app


def launch(**kw):
    print('Shriftlar tayyorlanmoqda…')
    ensure_fonts()
    app = build_app()
    app.queue(default_concurrency_limit=1).launch(share=True, css=CSS, theme=gr.themes.Soft(primary_hue='violet'), **kw)
    return app
