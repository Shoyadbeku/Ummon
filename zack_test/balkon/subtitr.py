# Zack D. uslubidagi subtitr (ASS): oq qalin yozuv, qora chegara, 2–4 so'zlik bo'laklar.
# Vaqtlar Whisper (faster-whisper medium, language="uz", word_timestamps) so'z boshlanishidan olingan,
# matn o'zbek imlosiga to'g'rilangan. Ishga tushirish: python3 -I subtitr.py chiqish.ass
import sys

CHUNKS = [  # (boshlanish, tugash yoki None = keyingisigacha, matn)
    (0.00, None, "U o'rnidan turdi,"), (1.62, None, "panjara orasidan"), (2.42, None, "o'tib ketdi"),
    (2.98, None, "va 18 metr"), (4.40, None, "balandlikdan"), (5.12, None, "pastdagi ko'chaga"), (6.00, 6.70, "quladi."),
    (6.80, None, "Lekin pastdagi"), (7.60, None, "kafening ayvoni"), (8.44, 9.20, "ochiq edi,"),
    (9.24, None, "bola unga urilib,"), (10.10, None, "yana havoga"), (10.76, 11.35, "otildi."),
    (11.42, None, "Demak, u baribir"), (12.22, None, "asfaltga"), (12.72, 13.70, "tushar edi."),
    (13.80, None, "Biroq ko'chaning"), (14.66, None, "narigi tomonida"), (15.44, None, "bir shifokor"),
    (16.14, None, "bu voqeani"), (16.82, 17.65, "ko'rib qoldi."),
    (17.72, None, "U bolani"), (18.26, None, "ilib olish uchun"), (19.02, None, "yugurdi"),
    (19.60, None, "va bola"), (20.32, None, "to'g'ri uning"), (20.96, 22.20, "quchog'iga tushdi."),
    (22.28, None, "Bola yig'ladi,"), (23.06, None, "lekin unga"), (23.62, 24.70, "hech narsa qilmadi."),
    (24.78, None, "Shifokor uni"), (25.40, None, "tebratgan edi,"), (26.34, None, "tez orada"), (26.84, 27.80, "uxlab qoldi."),
    (27.88, None, "Uni uyda"), (28.58, None, "yolg'iz qoldirib"), (29.40, None, "ketgan ota-onasi esa"),
    (30.46, None, "keyinroq"), (31.10, None, "qarovsiz qoldirgani"), (32.24, 34.0, "uchun hibsga olindi."),
]


def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Zack,Inter ExtraBold,82,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,6,2,2,60,60,470,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

out = [HEAD]
for i, (a, b, txt) in enumerate(CHUNKS):
    if b is None: b = CHUNKS[i + 1][0] - 0.02
    # kichik "pop" animatsiya: 90% -> 100% masshtab
    out.append(f"Dialogue: 0,{ts(a)},{ts(b)},Zack,,0,0,0,,{{\\fscx88\\fscy88\\t(0,90,\\fscx100\\fscy100)}}{txt}\n")
open(sys.argv[1] if len(sys.argv) > 1 else "subtitr.ass", "w").write("".join(out))
