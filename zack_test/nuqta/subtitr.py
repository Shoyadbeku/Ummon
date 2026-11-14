# So'zma-so'z subtitr (namuna videodagidek) -> ASS fayl. Vaqtlar Whisper (faster-whisper medium, language="uz") so'zlaridan,
# imlo qo'lda tuzatilgan. Ishga tushirish: python3 -I subtitr.py /tmp/claude-0/audio/nuqta.ass
import sys
CAP = [
    (0.00, "Bir o'qituvchi"), (0.88, "o'zining oppoq"), (1.84, "ko'ylagiga"), (2.54, "bitta qora"), (3.40, "nuqta chizdi."),
    (4.62, "Keyin"), (4.90, "sinfdan so'radi:"), (6.10, "nimani"), (6.46, "ko'ryapsizlar?"),
    (7.64, "Hamma"), (8.14, "nuqtani ko'rsatdi."),
    (9.56, "U esa"), (10.02, "sinfga"), (10.42, "bir qarab chiqib"), (11.14, "so'radi:"), (12.08, "ko'ylakning"), (12.72, "qolgan qismi-chi?"),
    (14.28, "Ko'ylak"), (14.78, "deyarli"), (15.36, "butunlay"), (16.10, "oppoq edi,"), (17.04, "lekin bunga"), (17.60, "hech kim"),
    (18.10, "e'tibor bermadi."),
    (19.52, "O'qituvchi"), (20.04, "tushuntirdi:"), (21.04, "kimdir sizga"), (21.82, "o'n marta"), (22.54, "yaxshilik qilishi,"),
    (23.62, "keyin"), (24.08, "bir marta"), (24.70, "ko'nglingizni"), (25.32, "qoldirishi"), (25.88, "mumkin"),
    (26.22, "va negadir"), (27.14, "aynan"), (27.66, "o'sha"), (28.08, "bir lahza"), (28.90, "esda qoladi."),
    (30.24, "Chunki"), (30.44, "miyamiz"), (30.92, "tabiatan"), (31.50, "noto'g'ri"), (32.16, "va salbiy"), (32.78, "tuyulgan"),
    (33.16, "narsalarga"), (34.02, "ko'proq"), (34.62, "e'tibor beradi."),
    (35.92, "Demak,"), (36.36, "bir gina"), (36.98, "nuqta"), (37.48, "shuncha"), (38.10, "oqlik"), (38.54, "doim"),
    (39.04, "bor bo'lganini"), (39.96, "unuttirib"), (40.58, "qo'yishi mumkin."),
]
ENDS = {4.40, 7.40, 9.40, 14.10, 19.30, 30.00, 35.70, 41.50}       # gap oxiridagi jimlik
def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"
hdr = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Z,Inter ExtraBold,74,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,0,0,0,0,100,100,0,0,1,5,3,2,60,60,430,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
lines = []
for i, (t, txt) in enumerate(CAP):
    nxt = CAP[i + 1][0] if i + 1 < len(CAP) else 41.5
    end = min([e for e in ENDS if e > t] + [nxt])
    # kichik "pop" (kattalashib kirish)
    lines.append(f"Dialogue: 0,{ts(t)},{ts(end)},Z,,0,0,0,,{{\\fscx80\\fscy80\\t(0,90,\\fscx100\\fscy100)}}{txt}")
open(sys.argv[1], "w").write(hdr + "\n".join(lines) + "\n")
print("ok", len(lines))
