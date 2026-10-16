#!/usr/bin/env bash
# Kadrlar + ovoz + subtitr -> final.mp4 (1080x1920, 30fps)
set -euo pipefail
cd "$(dirname "$0")"

# 1) subtitrlar (ASS), har 2-3 so'z bitta bo'lak, vaqt so'z uzunligiga mutanosib
python3 - <<'EOF'
sent = [
    (0.3, 8.43, "Ular yerga oq chiziqlar chizib, yon tomonlariga to'q soyalar qo'shishdi va yangi turdagi piyodalar o'tish joyini yaratishdi."),
    (8.7, 16.74, "Yaqinlashib kelayotgan avtomobil nuqtai nazaridan esa, u yerdan tepada suzib yuruvchi haqiqiy bloklarga o'xshaydi."),
    (17.0, 23.19, "Ko'rib turganingizdek, bu ixtiro piyodalar yo'lagida hech kim to'xtamagani uchun yaratilgan."),
    (23.4, 28.28, "Shunday qilib, odam chizmaga yaqinlashganda, albatta to'xtaydi."),
]
def ts(t):
    h, m = int(t // 3600), int(t % 3600 // 60)
    return f"{h}:{m:02d}:{t % 60:05.2f}"
out = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Cap,DejaVu Sans,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,3,2,60,60,560,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for a, b, text in sent:
    words = text.split()
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) == 3 or w[-1] in ",." or len(" ".join(cur)) > 18:
            chunks.append(cur); cur = []
    if cur:
        chunks.append(cur)
    total = sum(len(" ".join(c)) + 2 for c in chunks)
    t = a
    for c in chunks:
        d = (b - a) * (len(" ".join(c)) + 2) / total
        txt = " ".join(c).upper()
        # birinchi so'z sariq rangda (Shorts uslubi)
        first, *rest = txt.split(" ", 1)
        txt = "{\\c&H00D7FF&}" + first + "{\\c&HFFFFFF&}" + (" " + rest[0] if rest else "")
        out.append(f"Dialogue: 0,{ts(t)},{ts(t + d)},Cap,,0,0,0,,{{\\fad(40,40)}}{txt}")
        t += d
open("subs.ass", "w").write("\n".join(out) + "\n")
EOF

# 2) diktor: gaplarni o'z vaqtiga joylab, ovozni biroz "qalinlashtirish"
ffmpeg -v error -y \
  -i audio/s1.wav -i audio/s2.wav -i audio/s3.wav -i audio/s4.wav \
  -i audio/sfx.wav -i audio/music.wav \
  -filter_complex "\
[0]adelay=300|300[a0];[1]adelay=8700|8700[a1];[2]adelay=17000|17000[a2];[3]adelay=23400|23400[a3];\
[a0][a1][a2][a3]amix=inputs=4:normalize=0,aresample=44100,asetrate=44100*0.94,aresample=44100,atempo=1.0638,\
equalizer=f=180:t=q:w=1:g=4,equalizer=f=3000:t=q:w=1:g=3,acompressor=threshold=-20dB:ratio=4,volume=1.6[voice];\
[4]volume=0.9[fx];[5]volume=0.16[mus];\
[voice]asplit[v1][v2];[mus][v2]sidechaincompress=threshold=0.05:ratio=6:release=400[duck];\
[v1][fx][duck]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,apad,atrim=0:29.5[out]" \
  -map "[out]" -ar 44100 -ac 2 audio/mix.wav

# 3) video
ffmpeg -v error -y -framerate 30 -i frames/f_%04d.png -i audio/mix.wav \
  -vf "scale=1080:1920:flags=lanczos,unsharp=5:5:0.6,eq=saturation=1.12:contrast=1.04,ass=subs.ass" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest final.mp4
echo "final.mp4 tayyor"
