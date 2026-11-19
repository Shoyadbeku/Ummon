"""Builds storyboard.json (scenes, hook edit, kinetic text, SFX cues, music plan, ducking curve, subtitle pages)
from the aligned transcript.  usage: python build_storyboard.py transcript.json voice16k.wav out_dir"""
import sys, json, re, wave
import numpy as np
tr = json.load(open(sys.argv[1])); wavp = sys.argv[2]; out = sys.argv[3]
FPS = 30
S = tr["sentences"]
W = [w for s in S for w in s["words"]]
for i, s in enumerate(S):
    for w in s["words"]: w["sid"] = i

def st(sid, word=None, lead=0.25):
    """time (audio seconds) of sentence start or of a word inside it, minus lead"""
    if word is None: return max(0, S[sid]["start"] - lead)
    for w in S[sid]["words"]:
        if re.sub(r"[^\w'\-]", "", w["text"].lower()).startswith(word.lower()): return max(0, w["start"] - lead)
    raise KeyError((sid, word))
def wt(sid, word): return st(sid, word, 0)

# ---------------- HOOK (cold open, re-uses two strong lines of the original voice) ----------------
HOOK_CLIPS = [  # [audio_in, audio_out, video_start_frame]
    {"from": 38.80, "to": 41.55, "at": 8},
    {"from": 53.95, "to": 63.45, "at": 8 + int(2.75 * FPS) + 14},
]
hook_b_end = HOOK_CLIPS[1]["at"] + int((HOOK_CLIPS[1]["to"] - HOOK_CLIPS[1]["from"]) * FPS)
TITLE_START = hook_b_end + 6
HOOK_FRAMES = TITLE_START + 96          # title card ~3.2 s
OFF = HOOK_FRAMES / FPS                 # main narration offset (s)
DUR_AUDIO = tr["duration"]
TAIL = 2.5
TOTAL = HOOK_FRAMES + int(np.ceil((DUR_AUDIO + TAIL) * FPS))
def hookf(audio_t):  # audio time inside hook clips -> video frame
    for c in HOOK_CLIPS:
        if c["from"] <= audio_t <= c["to"]: return c["at"] + (audio_t - c["from"]) * FPS
    return None
def vf(audio_t): return int(round((audio_t + OFF) * FPS))   # main-story audio time -> video frame

# ---------------- SCENES ----------------
img = lambda n: [p for p in IMGS if p.startswith(f"{n:02d}_")][0]
IMGS = sorted(json.load(open(f"{out}/../remotion-project/public/image_meta.json")), key=lambda m: m["file"])
IMGS = [m["file"] for m in IMGS]
# (startTimeAudio, image#, motion, fx, fy, zoomFrom, zoomTo, note)
M = [
 (0.0, 1, "pushIn", .45, .55, 1.0, 1.16, "Ochilish: XII asr qishlog'i, tuman ichida"),
 (st(2), 2, "panR", .45, .55, 1.08, 1.12, "O'roq mavsumi"),
 (st(4), 3, "pushIn", .45, .62, 1.0, 1.25, "Bo'ri o'ralari — qorong'i chuqurlikka kirib borish"),
 (st(5), 4, "tiltDown", .5, .45, 1.12, 1.05, "Dehqonlar to'xtab qoladi"),
 (st(6), 5, "pushIn", .55, .5, 1.0, 1.3, "Qo'l ushlashgan ikki bola — sekin yaqinlashuv"),
 (st(8), 6, "panL", .55, .5, 0.92, 0.98, "G'alati kiyimlar (yuzlar ko'rinadi)"),
 (st(9), 7, "drift", .45, .5, 1.05, 1.12, "Tushunarsiz til"),
 (st(10), 9, "shake", .5, .5, 1.05, 1.15, "Dahshat"),
 (st(11), 8, "slam", .5, .45, 1.35, 0.95, "YASHIL TERI — hissiy zarba"),
 (st(13), 10, "pushIn", .55, .5, 1.0, 1.2, "800 yillik sir"),
 (st(15), 5, "pullOut", .55, .5, 1.35, 1.05, "Kim? Qayerdan? Nega yashil?"),
 (st(16), 54, "panR", .4, .5, 1.05, 1.1, "Ertak emas — solnomalar"),
 (st(18), 11, "pushIn", .55, .45, 1.0, 1.18, "Nyuberglik Uilyam"),
 (st(20), 12, "panL", .72, .5, 1.05, 1.1, "Koggeshollik Ralf"),
 (st(21), 13, "drift", .5, .5, 1.0, 1.1, "Guvohdan eshitilgan"),
 (st(22), 14, "tiltUp", .5, .45, 1.15, 1.02, "Qirol Stiven davri"),
 (st(23), 15, "pushIn", .62, .4, 1.0, 1.22, "Uilyamning shubhasi"),
 (st(23, "ishonchli", 0.15), 16, "panR", .5, .5, 1.05, 1.1, "Ishonchli guvohlar"),
 (st(24), 17, "pushIn", .55, .55, 1.0, 1.15, "Bolalarni qishloqqa olib kelish"),
 (st(26), 18, "pullOut", .5, .55, 1.25, 1.0, "Butun qishloq yig'ildi"),
 (st(27), 19, "tiltDown", .4, .45, 1.12, 1.04, "Ser Richard uyi"),
 (st(28), 20, "panR", .45, .55, 1.05, 1.12, "Non, go'sht, sut"),
 (st(30), 21, "pushIn", .5, .5, 0.92, 1.08, "Yig'layotgan bolalar"),
 (st(32), 22, "pushIn", .45, .55, 1.0, 1.2, "Ochlikdan holsizlanish"),
 (st(35), 23, "panL", .58, .5, 1.05, 1.1, "Loviya poyalari"),
 (st(36), 24, "pushIn", .5, .45, 0.95, 1.12, "Jonlanish"),
 (st(38), 25, "panR", .45, .55, 1.05, 1.15, "Poyani yorish"),
 (st(40), 26, "pushIn", .4, .55, 1.0, 1.25, "Xom loviya"),
 (st(42), 27, "drift", .45, .5, 1.05, 1.15, "Oylar davomida loviya"),
 (st(43), 28, "panR", .35, .5, 1.05, 1.1, "Boshqa ovqatlarga o'rganish"),
 (st(44), 29, "desat", .55, .45, 1.0, 1.2, "Yashil rang so'nmoqda"),
 (st(47), 31, "pushIn", .4, .5, 1.0, 1.15, "Kasal o'g'il"),
 (st(48), 30, "tiltUp", .5, .5, 1.1, 1.02, "Suvga cho'mdirish"),
 (st(48, "o'g'il", 0.3), 31, "dim", .3, .55, 1.25, 1.35, "O'g'il vafot etdi — qorong'ilashuv"),
 (st(49), 32, "pullOut", .5, .45, 1.2, 1.0, "Qiz omon qoldi"),
 (st(51), 33, "pushIn", .75, .45, 1.0, 1.25, "Qiz hikoya qiladi"),
 (st(54), 34, "pushIn", .5, .5, 1.0, 1.18, "Avliyo Martin yurti"),
 (st(55), 35, "panR", .4, .55, 1.05, 1.12, "Yashil odamlar"),
 (st(56), 34, "panL", .62, .45, 1.12, 1.2, "Quyosh chiqmaydigan yurt"),
 (st(58), 35, "pullOut", .55, .4, 1.3, 1.05, "G'ira-shira yorug'lik"),
 (st(59), 36, "pushIn", .5, .45, 1.0, 1.2, "Daryo narigi yorug' yurt"),
 (st(61), 37, "panR", .35, .5, 1.05, 1.12, "Poda va qo'ng'iroq"),
 (st(64), 38, "pushIn", .5, .55, 1.0, 1.35, "Qorong'i g'or"),
 (st(66), 39, "flash", .4, .5, 1.25, 1.0, "Ko'zni qamashtiruvchi quyosh"),
 (st(68), 38, "pullOut", .45, .5, 1.3, 1.05, "Qaytish yo'li yo'q"),
 (st(69), 32, "panL", .55, .5, 1.1, 1.18, "Xizmatkor qiz — Agnes"),
 (st(71), 40, "pushIn", .45, .5, 1.0, 1.15, "Turmush"),
 (st(72), 18, "panR", .4, .5, 1.1, 1.15, "Avlodlar"),
 (st(74), 41, "pushIn", .5, .5, 1.0, 1.18, "Olimlar izlanishi"),
 (st(76), 42, "panR", .45, .5, 1.05, 1.12, "Xloroz"),
 (st(80), 29, "pushIn", .5, .45, 1.15, 1.35, "Och-yashil tus"),
 (st(83), 22, "panL", .5, .5, 1.05, 1.12, "Nega och qolgan?"),
 (st(85), 43, "pushIn", .5, .5, 1.0, 1.15, "Flamand to'quvchilar"),
 (st(88), 44, "shake", .5, .5, 1.05, 1.15, "Ta'qib"),
 (st(89), 45, "pushIn", .45, .55, 1.0, 1.25, "O'rmondagi yetimlar"),
 (st(92), 7, "panR", .4, .5, 1.12, 1.18, "Tushunmagan dehqonlar"),
 (st(93), 46, "tiltDown", .5, .45, 1.15, 1.0, "Fordem Sent-Martin"),
 (st(95), 36, "panL", .55, .5, 1.1, 1.18, "Avliyo Martin yurti?"),
 (st(96), 47, "pushIn", .5, .5, 1.0, 1.22, "Zich o'rmon soyasi"),
 (st(97), 48, "panR", .45, .5, 1.05, 1.12, "Tanqidchilar"),
 (st(99), 49, "pushIn", .5, .55, 1.0, 1.3, "Non jumbog'i"),
 (st(100), 50, "pushIn", .5, .55, 1.0, 1.2, "Yer osti dunyosi"),
 (st(102), 51, "drift", .5, .5, 1.05, 1.15, "Parilar olami"),
 (st(104), 52, "rotate", .5, .5, 1.0, 1.2, "Boshqa sayyora"),
 (st(106), 53, "pushIn", .5, .55, 1.0, 1.2, "Fotosintez farazi"),
 (st(108), 54, "panL", .55, .5, 1.12, 1.2, "Rivoyat yoki fakt"),
 (st(110), 55, "pushIn", .3, .45, 1.0, 1.15, "Bugungi Vulpit belgisi"),
 (st(113), 1, "panL", .55, .55, 1.1, 1.18, "Avloddan-avlodga"),
 (st(115), 56, "pushIn", .5, .5, 1.0, 1.2, "Begona yurtda ikki bola"),
 (st(119), 31, "dim", .4, .5, 1.15, 1.25, "Biri vafot etdi"),
 (st(120), 40, "panR", .4, .5, 1.12, 1.18, "Yangi hayot"),
 (st(121), 57, "pushIn", .62, .45, 1.0, 1.22, "Agnesning sog'inchi"),
 (st(124), 18, "pullOut", .5, .5, 1.25, 1.05, "Begonaga hayrat"),
 (st(126), 58, "pushIn", .5, .5, 1.0, 1.45, "Inson qalbidagi sir"),
 (st(127), 59, "pushIn", .5, .55, 1.0, 1.15, "Siz qanday o'ylaysiz?"),
 (st(129), 45, "punch", .45, .55, 1.15, 1.25, "Och qolgan yetimlarmi?"),
 (st(130), 50, "punch", .5, .55, 1.15, 1.25, "Yer osti dunyosimi?"),
 (st(131), 52, "punch", .5, .5, 1.1, 1.22, "Boshqa bir sirmi?"),
 (st(132), 59, "pullOut", .5, .55, 1.25, 1.05, "Izohlarda yozing"),
 (st(133), 60, "pushIn", .5, .5, 1.0, 1.2, "Outro"),
]
scenes = []
for i, (t0, n, mot, fx, fy, z0, z1, note) in enumerate(M):
    t1 = M[i + 1][0] if i + 1 < len(M) else DUR_AUDIO + TAIL
    scenes.append({"id": f"S{i+1:02d}", "from": vf(t0) if i else HOOK_FRAMES, "to": vf(t1), "audioStart": round(t0, 2), "audioEnd": round(t1, 2),
                   "image": img(n), "motion": mot, "fx": fx, "fy": fy, "z0": z0, "z1": z1, "note": note,
                   "narration": " ".join(s["text"] for s in S if s["start"] >= t0 - 0.01 and s["start"] < t1 - 0.01)})
# hook scenes
hook_scenes = [
 {"id": "H1", "from": 0, "to": HOOK_CLIPS[1]["at"], "image": img(8), "motion": "slam", "fx": .5, "fy": .45, "z0": 1.45, "z1": 1.0, "note": "HOOK: yashil teri, keskin ochilish"},
 {"id": "H2", "from": HOOK_CLIPS[1]["at"], "to": int(hookf(56.9)), "image": img(10), "motion": "pushIn", "fx": .55, "fy": .5, "z0": 1.05, "z1": 1.25, "note": "800 yil"},
 {"id": "H3", "from": int(hookf(56.9)), "to": TITLE_START, "image": img(6), "motion": "pushIn", "fx": .5, "fy": .5, "z0": 0.9, "z1": 1.1, "note": "Kim? Qayerdan? Nega?"},
 {"id": "TITLE", "from": TITLE_START, "to": HOOK_FRAMES, "image": img(60), "motion": "pullOut", "fx": .5, "fy": .5, "z0": 1.25, "z1": 1.05, "note": "Sarlavha"},
]
scenes = hook_scenes + scenes
for sc in scenes: sc["image"] = "images/" + sc["image"]

# ---------------- KINETIC TEXT / OVERLAYS ----------------
K = []
def k(frame, typ, text, dur=None, **kw):
    K.append({"from": int(frame), "dur": int(dur or 75), "type": typ, "text": text, **kw})
# hook
k(hookf(wt(11, "yashil")), "impact", "YASHIL", 60, color="green")
k(hookf(wt(14, "sakkiz")), "counter", "800", 95, suffix="+ YIL", sub="YECHILMAGAN SIR")
k(hookf(wt(15, "kim")), "word", "KIM?", 40, pos=0)
k(hookf(wt(15, "qayerdan")), "word", "QAYERDAN?", 40, pos=1)
k(hookf(wt(15, "nega")), "word", "NEGA YASHIL?", 70, pos=2, color="green")
k(TITLE_START, "title", "VULPITNING|YASHIL|BOLALARI", HOOK_FRAMES - TITLE_START + 10, sub="ANGLIYA · XII ASR · HAQIQIY SOLNOMA")
# chapters
for sid, word, label, num in [(0, None, "TOPILMA", "I"), (16, None, "GUVOHLAR", "II"), (24, None, "LOVIYA SIRI", "III"),
                              (44, None, "YASHIL RANG SO'NADI", "IV"), (52, None, "QIZNING HIKOYASI", "V"),
                              (74, None, "NAZARIYALAR", "VI"), (115, None, "BEGONA YURTDA", "VII"), (127, None, "SIZ-CHI?", "VIII")]:
    k(vf(st(sid, word, 0.1)), "chapter", label, 120, num=num)
k(vf(wt(0, "o'n")) + 4, "stamp", "XII ASR", 110, sub="VULPIT · SHARQIY ANGLIYA")
k(vf(wt(14, "sakkiz")), "counter", "800", 75, suffix="+ YIL", sub="")
k(vf(wt(18, "nyuberglik")), "name", "NYUBERGLIK UILYAM", 90, sub="Rohib, solnomachi")
k(vf(wt(20, "koggeshollik")), "name", "KOGGESHOLLIK RALF", 90, sub="Abbatlik boshlig'i")
k(vf(wt(22, "1135")), "dates", "1135 — 1154", 120, sub="QIROL STIVEN DAVRI")
k(vf(wt(27, "ser")), "name", "SER RICHARD DE KALNE", 90, sub="Mahalliy zodagon")
k(vf(wt(29, "non")), "list", "NON|GO'SHT|SUT", 70, times=[0, int((wt(29, "go'sht") - wt(29, "non")) * FPS), int((wt(29, "sut") - wt(29, "non")) * FPS)])
k(vf(wt(32, "bir")), "word", "1-KUN", 28, pos=1)
k(vf(wt(33, "ikki")), "word", "2-KUN", 40, pos=1)
k(vf(wt(52, "sen")), "quote", "Sen kimsan va|qayerdan kelding?", int((S[52]["end"] - wt(52, "sen")) * FPS) + 40)
k(vf(wt(54, "avliyo")), "title2", "AVLIYO MARTIN|YURTI", 110, color="green")
k(vf(wt(70, "agnes")), "name", "AGNES", 90, sub="Omon qolgan qiz")
k(vf(wt(76, "birinchi")), "theory", "KASALLIK", 120, num="1")
k(vf(wt(77, "xloroz")), "term", "XLOROZ", 100, sub="«yashil kasallik»")
k(vf(wt(85, "bu")), "theory", "FLAMAND YETIMLARI", 120, num="2")
k(vf(wt(85, "pol")), "name", "POL XARRIS", 80, sub="Tarixchi")
k(vf(wt(86, "flandriyadan")), "route", "FLANDRIYA → ANGLIYA", 90, sub="bugungi Belgiya")
k(vf(wt(93, "fordem")), "name", "FORDEM SENT-MARTIN", 100, sub="Daryo ortidagi qishloq")
k(vf(wt(101, "ba'zilar")), "theory", "YER OSTI DUNYOSI", 120, num="3")
k(vf(wt(105, "ba'zi")), "theory", "BOSHQA SAYYORA", 120, num="4")
k(vf(wt(108, "ba'zi")), "theory", "RIVOYAT", 110, num="5")
k(vf(wt(128, "vulpitning")), "word", "KIM EDI?", 60, pos=1, color="green")
k(vf(wt(133, "qiziq-a")), "cta", "QIZIQ-A?", int((DUR_AUDIO - wt(133, "qiziq-a")) * FPS), bell=vf(wt(134, "qo'ng'iroqchani")) - vf(wt(133, "qiziq-a")))

# ---------------- SFX ----------------
X = []
def sfx(frame, name, vol=0.5): X.append({"from": max(0, int(frame)), "src": f"sfx/{name}.wav", "volume": vol})
sfx(0, "boom", 0.55); sfx(0, "whoosh_rev", 0.3)
sfx(hookf(wt(11, "yashil")) - 2, "boom", 0.42)
sfx(hookf(wt(14, "sakkiz")) - 3, "whoosh", 0.25)
for w in ("kim", "qayerdan", "nega"): sfx(hookf(wt(15, w)) - 1, "tick", 0.22)
sfx(TITLE_START - 80, "riser", 0.32); sfx(TITLE_START, "boom", 0.6); sfx(TITLE_START + 4, "shimmer", 0.3)
for c in [x for x in K if x["type"] == "chapter"][1:]: sfx(c["from"] - 6, "whoosh", 0.22)
sfx(vf(wt(10, "dahshatga")), "heartbeat", 0.35); sfx(vf(wt(10, "dahshatga")) + 26, "heartbeat", 0.3)
sfx(vf(wt(11, "yashil")) - 2, "subdrop", 0.4)
sfx(vf(wt(14, "sakkiz")), "tick", 0.15)
sfx(vf(wt(22, "1135")) - 2, "whoosh", 0.18)
for w in ("non", "go'sht", "sut"): sfx(vf(wt(29, w)) - 1, "tick", 0.2)
sfx(vf(wt(32, "bir")), "heartbeat", 0.25); sfx(vf(wt(33, "ikki")), "heartbeat", 0.3)
sfx(vf(wt(48, "vafot")) - 4, "subdrop", 0.45)
sfx(vf(wt(52, "sen")) - 3, "whoosh", 0.18)
sfx(vf(wt(54, "avliyo")) - 2, "shimmer", 0.35)
sfx(vf(wt(63, "qo'ng'iroqlarning")) - 2, "bells", 0.3)
sfx(vf(wt(66, "ko'zni")) - 3, "flash", 0.35)
for t in [x for x in K if x["type"] == "theory"]: sfx(t["from"] - 3, "whoosh", 0.2)
sfx(vf(wt(77, "xloroz")), "tick", 0.15)
sfx(vf(wt(88, "o'ldirilgan")) - 2, "subdrop", 0.3)
sfx(vf(wt(104, "yigirmanchi")) - 20, "riser", 0.15); sfx(vf(wt(105, "ba'zi")), "boom", 0.25)
sfx(vf(wt(119, "vafot")) - 4, "subdrop", 0.35)
sfx(vf(wt(126, "qalbida")) - 2, "shimmer", 0.25)
for sid in (129, 130, 131): sfx(vf(st(sid, None, 0.25)), "whoosh", 0.18)
sfx(vf(wt(134, "qo'ng'iroqchani")), "tick", 0.3)
sfx(vf(wt(134, "qo'ng'iroqchani")) + 4, "shimmer", 0.2)
X.sort(key=lambda x: x["from"])

# ---------------- MUSIC PLAN (video seconds) ----------------
v = lambda a: a + OFF
T = TOTAL / FPS
sections = [
 dict(start=0, end=TITLE_START / FPS - 0.2, pad=.55, bright=.2, pulse=.9, bpm=72, drone=.8, bells=0, chords=["Dm", "Bb", "Dm", "A"], chordLen=3.2, mood="hook-tension"),
 dict(start=TITLE_START / FPS - 0.2, end=OFF, pad=.95, bright=.7, pulse=0, drone=.9, bells=.2, chords=["Dm"], chordLen=4, mood="title-swell"),
 dict(start=OFF, end=v(35.4), pad=.5, bright=.3, pulse=0, drone=.5, bells=.3, chords=["Dm", "Bb", "F", "C"], chordLen=7, mood="mystery-intro"),
 dict(start=v(35.4), end=v(63.9), pad=.6, bright=.25, pulse=.6, bpm=64, drone=.75, bells=0, chords=["Dm", "Gm", "Dm", "A"], chordLen=6, mood="reveal-tension"),
 dict(start=v(63.9), end=v(108), pad=.45, bright=.3, pulse=.15, bpm=60, drone=.5, bells=.1, chords=["F", "C", "Dm", "Bb"], chordLen=8, mood="chronicle"),
 dict(start=v(108), end=v(137), pad=.5, bright=.25, pulse=.2, bpm=56, drone=.6, bells=0, chords=["Dm", "Bb", "Gm", "A"], chordLen=7, mood="hunger"),
 dict(start=v(137), end=v(174), pad=.5, bright=.4, pulse=0, drone=.45, bells=.3, chords=["F", "C", "Bb", "F"], chordLen=7, mood="hope-beans"),
 dict(start=v(174), end=v(206), pad=.6, bright=.22, pulse=.1, bpm=52, drone=.6, bells=.05, chords=["Dm", "Bb", "Gm", "A"], chordLen=8, mood="melancholy"),
 dict(start=v(206), end=v(290), pad=.6, bright=.55, pulse=0, drone=.55, bells=.5, chords=["Fmaj7", "Bbmaj7", "Dsus", "Am"], chordLen=8, mood="wonder-land"),
 dict(start=v(290), end=v(317), pad=.45, bright=.35, pulse=0, drone=.45, bells=.15, chords=["Dm", "Bb", "F", "C"], chordLen=8, mood="afterlife"),
 dict(start=v(317), end=v(450), pad=.45, bright=.35, pulse=.35, bpm=70, drone=.55, bells=.1, chords=["Dm", "C", "Bb", "A"], chordLen=6, mood="investigation"),
 dict(start=v(450), end=v(514), pad=.55, bright=.45, pulse=.15, bpm=60, drone=.8, bells=.45, chords=["Ebmaj", "Dm", "Bbmaj7", "A"], chordLen=8, mood="supernatural"),
 dict(start=v(514), end=v(597), pad=.75, bright=.55, pulse=0, drone=.6, bells=.2, chords=["Bb", "F", "Gm", "Dm", "Bb", "F", "C", "A"], chordLen=6, mood="emotional-peak"),
 dict(start=v(597), end=T, pad=.6, bright=.45, pulse=.1, bpm=60, drone=.5, bells=.25, chords=["Dm", "Bb", "F", "A"], chordLen=6, mood="outro-resolve"),
]
music_plan = {"duration": T, "fadeIn": 0.3, "fadeOut": 5.0, "sections": sections}

# ---------------- DUCKING (per video frame) from voice RMS ----------------
w = wave.open(wavp); sr = w.getframerate()
a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
hop = sr // FPS
rms = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2) + 1e-12) for i in range(0, len(a) - hop, hop)])
act_main = (20 * np.log10(rms) > -40).astype(float)
act = np.zeros(TOTAL)
for c in HOOK_CLIPS:
    s0 = int(c["from"] * FPS); s1 = int(c["to"] * FPS); act[c["at"]:c["at"] + s1 - s0] = act_main[s0:s1]
act[HOOK_FRAMES:HOOK_FRAMES + len(act_main)] = act_main[:TOTAL - HOOK_FRAMES]
# hold speech for short gaps (< 0.5 s) so music doesn't pump between words
hold = np.zeros(TOTAL); last = -999
for i in range(TOTAL):
    if act[i]: last = i
    hold[i] = 1.0 if i - last < 15 else 0.0
# attack/release smoothing
g = np.zeros(TOTAL); y = 0
for i in range(TOTAL):
    tgt = hold[i]; y += (tgt - y) * (0.35 if tgt > y else 0.05); g[i] = y
UNDER, OPEN = 0.16, 0.42
vol = OPEN - (OPEN - UNDER) * g
vol[TITLE_START - 10:HOOK_FRAMES] = np.maximum(vol[TITLE_START - 10:HOOK_FRAMES], 0.55)
# swell a bit at the emotional peak pauses, softer under CTA
vol[vf(514):vf(597)] *= 1.12

# ---------------- SUBTITLE PAGES ----------------
KEY_GREEN = re.compile(r"^(yashil|yashil\w*|vulpit\w*|sir\w*|jumboq|loviya\w*|avliyo|martin|shom|g'or\w*|quyosh\w*|sayyora\w*|begona\w*|och-yashil|xloroz|flamand)$", re.I)
KEY_GOLD = re.compile(r"^(\d.*|sakkiz|yuz|uilyam|ralf|richard|agnes|stiven|xarris\w*|fordem|sent-martin|dahshat\w*|hech|vafot|ikki|bir)$", re.I)
def norm(s):  # proper Uzbek apostrophes for display
    s = re.sub(r"([oOgG])'", lambda m: m.group(1) + "ʻ", s)
    return s.replace("'", "ʼ")
pages = []
def paginate(words, offset_fn):
    cur = []; chars = 0
    def flush():
        nonlocal cur, chars
        if cur: pages.append(cur)
        cur = []; chars = 0
    for i, x in enumerate(words):
        if x["dis"] or not x["text"]: continue
        txt = x["text"]
        if cur and (chars + len(txt) > 20 or len(cur) >= 4 or (x["start"] - cur[-1]["e_audio"]) > 0.6): flush()
        f0 = offset_fn(x["start"]); f1 = offset_fn(x["end"])
        if f0 is None: continue
        clean = re.sub(r"[«»\"]", "", txt)
        bare = re.sub(r"[^\w'\-]", "", clean.lower())
        cur.append({"t": norm(clean), "s": int(round(f0)), "e": int(round(f1)), "e_audio": x["end"],
                    "k": "g" if KEY_GREEN.match(bare) else ("y" if KEY_GOLD.match(bare) and len(bare) > 3 else "")})
        chars += len(txt) + 1
        if re.search(r"[.?!,:;—]»?$", txt) and chars > 8: flush()
    flush()
# capitalize sentence starts after disfluency removal
for si, s in enumerate(S):
    if si and S[si - 1]["words"][-1]["text"].endswith("»") and s["words"][0]["text"][:1].islower(): continue
    for x in s["words"]:
        if not x["dis"] and x["text"]:
            x["text"] = x["text"][0].upper() + x["text"][1:]; break
hookwords = [x for x in W if any(c["from"] <= x["start"] and x["end"] <= c["to"] + 0.05 for c in HOOK_CLIPS)]
paginate(hookwords, lambda t: hookf(min(max(t, 0), 9999)) if hookf(t) is not None else None)
nh = len(pages)
paginate(W, lambda t: (t + OFF) * FPS)
subs = []
for i, p in enumerate(pages):
    nxt = pages[i + 1][0]["s"] if i + 1 < len(pages) else p[-1]["e"] + 30
    end = min(p[-1]["e"] + 18, nxt)
    for x in p: x.pop("e_audio", None)
    subs.append({"from": p[0]["s"], "to": max(end, p[0]["s"] + 12), "hook": i < nh, "words": p})

sb = {"fps": FPS, "width": 1080, "height": 1920, "durationInFrames": TOTAL, "hookFrames": HOOK_FRAMES, "titleStart": TITLE_START,
      "mainAudioOffsetFrames": HOOK_FRAMES, "voice": "audio/voice.wav", "music": "audio/music.wav",
      "hookClips": [{"fromSec": c["from"], "toSec": c["to"], "atFrame": c["at"]} for c in HOOK_CLIPS],
      "dramaturgy": {"HOOK": [0, TITLE_START], "TITLE": [TITLE_START, HOOK_FRAMES], "INTRIGUE": [HOOK_FRAMES, vf(63.9)],
                     "STORY_DEVELOPMENT": [vf(63.9), vf(317)], "THEORIES/TENSION": [vf(317), vf(514)], "EMOTIONAL_PEAK": [vf(514), vf(597)],
                     "PAYOFF": [vf(597), vf(617.8)], "CINEMATIC_ENDING": [vf(617.8), TOTAL]},
      "scenes": scenes, "overlays": sorted(K, key=lambda x: x["from"]), "sfx": X, "musicPlan": music_plan}
json.dump(sb, open(f"{out}/storyboard.json", "w"), ensure_ascii=False, indent=1)
json.dump({"subs": subs}, open(f"{out}/subtitles.json", "w"), ensure_ascii=False)
lvl = np.zeros(TOTAL); db = np.clip((20 * np.log10(rms) + 45) / 35, 0, 1)
for c in HOOK_CLIPS:
    s0 = int(c["from"] * FPS); s1 = int(c["to"] * FPS); lvl[c["at"]:c["at"] + s1 - s0] = db[s0:s1]
lvl[HOOK_FRAMES:HOOK_FRAMES + len(db)] = db[:TOTAL - HOOK_FRAMES]
json.dump({"music": [round(float(x), 4) for x in vol], "voice": [round(float(x), 3) for x in lvl]}, open(f"{out}/volume.json", "w"))
json.dump(music_plan, open(f"{out}/music_plan.json", "w"), indent=1)
print("TOTAL", TOTAL, "frames", TOTAL / FPS, "s; HOOK", HOOK_FRAMES, "scenes", len(scenes), "overlays", len(K), "sfx", len(X), "subpages", len(subs))
