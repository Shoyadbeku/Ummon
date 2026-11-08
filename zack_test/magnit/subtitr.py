# Whisper so'z vaqtlari (words.json) + to'g'rilangan o'zbekcha matn -> Zack D. uslubidagi ASS subtitr
# (2–3 so'zdan bo'lak, katta oq harf, aytilayotgan so'z sariq). Ishlatish: python3 -I subtitr.py words.json out.ass
import json, sys
W = json.load(open(sys.argv[1]))
# Whisper tokenlari bilan 1:1 to'g'rilangan so'zlar ("" = oldingi so'zga qo'shiladi)
FIX = ("Agar sen tasodifan ikkita kichkina + magnitni yutib yuborsang, nima bo'lishini bilasanmi? "
       "Avvaliga hech narsa sezmaysan. Magnitlar oshqozoningdan o'tib ichaklaringga tushadi. "
       "Lekin muammo shundaki, ular ichakning ikki_xil joyiga borib qoladi, va shu_yerda dahshat boshlanadi. "
       "Ikki magnit bir-birini + ichak devori orqali tortadi. Ular orasida + qolgan to'qima qattiq qisiladi. "
       "Unga qon bormay qoladi va asta sekin o'la boshlaydi. Bir necha kundan keyin ichak devorida teshik paydo bo'ladi. "
       "Ichidagi narsalar + qorin bo'shlig'iga oqib chiqadi va kuchli yallig'lanish boshlanadi. "
       "Shifokorlar bunday holatda faqat bitta yo'lini biladi. Zudlik bilan operatsiya. "
       "Shuning uchun bitta magnit unchalik xavfli bo'lmasa ham, ikkitasi hayotingni xavf ostiga qo'yishi mumkin. "
       "Ayniqsa bolalar + buni o'yinchoq deb o'ylaydi.").split()
FIX = [("" if w == "+" else w) for w in FIX]
assert len(FIX) == len(W), (len(FIX), len(W))
words = []
for (a, b, _), w in zip(W, FIX):
    if w == "": words[-1][1] = b
    else: words.append([a, b, w.replace("'", "‘")])
# bo'laklar: 3 so'zgacha, tinish belgisida yoki 0.45 s pauzada uziladi
chunks, cur = [], []
for i, w in enumerate(words):
    cur.append(w)
    gap = words[i + 1][0] - w[1] if i + 1 < len(words) else 9
    if len(cur) >= 3 or w[2][-1] in ",.?" or gap > 0.45 or sum(len(x[2]) for x in cur) > 16:
        chunks.append(cur); cur = []
if cur: chunks.append(cur)
def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"
hdr = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Z,Inter ExtraBold,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,3,2,60,60,560,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ev = []
for ci, ch in enumerate(chunks):
    end_chunk = min(ch[-1][1] + 0.25, chunks[ci + 1][0][0] if ci + 1 < len(chunks) else 99)
    for k, w in enumerate(ch):
        a = w[0]; b = ch[k + 1][0] if k + 1 < len(ch) else end_chunk
        txt = " ".join(("{\\c&H00E5FF&}" + x[2].upper() + "{\\c&HFFFFFF&}") if j == k else x[2].upper() for j, x in enumerate(ch))
        pop = "{\\fscx112\\fscy112\\t(0,90,\\fscx100\\fscy100)}" if k == 0 else ""
        ev.append(f"Dialogue: 0,{ts(a)},{ts(b)},Z,,0,0,0,,{pop}{txt}")
open(sys.argv[2], "w").write(hdr + "\n".join(ev) + "\n")
print(len(chunks), "bo'lak,", len(words), "so'z")
