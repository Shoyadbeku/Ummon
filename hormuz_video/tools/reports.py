# -*- coding: utf-8 -*-
import json, csv, os, glob, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from storyboard import SRC
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sb=json.load(open(f"{ROOT}/src/data/storyboard.json"))
OUT=f"{ROOT}/deliverables"
def tc(t): return f"{int(t//60):02d}:{t%60:05.2f}"
use={}
for s in sb["shots"]:
    if s["src"]=="GFX": continue
    use.setdefault(s["src"],[]).append(s)
def probe(p):
    o=subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height","-of","csv=p=0",p]).decode().strip()
    return o.replace(",","x")
# --- YouTube ---
YT_META={  # sarlavha, kanal (YouTube qidiruv natijasidan)
 "y01":("Iran says two oil tankers hit naval mines in Strait of Hormuz","Al Jazeera English"),
 "y02":("Iran says three oil tankers hit by naval mines in Strait of Hormuz","Al Jazeera English"),
 "y03":("Iran Claims Two 'Violating' Tankers Met Explosive Fate in Hormuz","New York Post"),
 "y04":("How the Strait of Hormuz works and why it matters to global oil supplies","Al Jazeera English"),
 "y05":("US and Israel carry out joint attack on Iran as Tehran launches retaliatory strikes","BBC News"),
 "y06":("How the US naval blockade of Iranian ports in the Strait of Hormuz works","Al Jazeera English"),
 "y07":("14-point draft U.S.-Iran MOU includes blockade lift, oil export waivers, and recovery fund","Arirang News"),
 "y08":("Iran says it will use all means to end U.S. naval blockade","CBS News"),
 "y09":("Kuwait drone strike kills two Italian nationals","BBC News"),
 "y11":("Kuwait: Two Italians killed in drone attack","FRANCE 24 English"),
 "y13":("Qatar steps up mediation as US and Iran face renewed confrontation","Al Jazeera English"),
 "y14":("Trump on Iran: victory is 'whenever I want it'","Jordan Rachel"),
 "y15":("Israel Says It's Ready to Strike Iran - Without the US #shorts","Viral Desk"),
 "y16":("Explosions in Iran's Bandar Abbas port as the US launches strikes","AFP News Agency"),
 "y17":("Uzbekistan expands transport network with new rail and air corridors","euronews"),
 "y18":("Oil prices surge as US, Iran trade strikes over Strait of Hormuz","Al Jazeera English"),
 "y21":("U.S. naval blockade of Iranian ports goes into effect","NBC News"),
 "y22":("Iran denies involvement in Kuwait strike that killed two Italians","africanews"),
 "y24":("Iran Foreign Minister Abbas Araghchi holds press conference","Al Jazeera English"),
}
UNUSED_YT={"Y10_DW_two_italians_killed_kuwait":("5amHuZ3k6Ck","Two Italians killed in drone attack in Kuwait","DW News","Ishlatilmadi (vertikal, takroriy mazmun)"),
 "Y12_TRT_Araghchi_Kuwait":("RGlh7O0akzQ","Araghchi tells Kuwait Iran had no involvement in drone incident","TRT World","Ishlatilmadi: videoda Araqchining o‘zi yo‘q, kadrlarni tasdiqlab bo‘lmadi"),
 "Y19_DW_who_struck_Kuwait":("kFtVyg_Ftq0","Who launched the first fatal strike on Kuwait in months?","DW News","Ishlatilmadi (boshqa kliplar bilan qoplangan)"),
 "Y20_Trump_victory_offers_deal":("fKd4yeKtzVs","Trump Says Victory at Hand in Iran War, Offers Tehran a Deal","NewsCircuit","RAD ETILDI: AI-yaratilgan boshlovchi, ishonchsiz manba"),
 "Y23_DailyGlobeDrop_precooked_recipe":("PzkwDToaMLI","Iran on the Kuwait Drone Strike: 'A Precooked Recipe for War'","Daily Globe Drop","Ishlatilmadi (past sifat, arxiv kadr afzal ko‘rildi)")}
with open(f"{OUT}/YouTube_Footage_Download_Report.csv","w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f)
    w.writerow(["YouTube video nomi","Original YouTube URL","YouTube kanal","Audiodagi tegishli voqea/shaxs","Original videodan tanlangan oraliq(lar)","Yuklab olish usuli","Yuklab olish holati","Video sifati","Autentiklik tekshiruvi","Litsenziya / foydalanish ruxsati","Yakuniy videodagi timestamp(lar)"])
    for k in sorted(YT_META):
        f_,cred,url=SRC[k]; title,ch=YT_META[k]
        meta=json.load(open(f"{ROOT}/public/{f_[:-4]}.snapyt.json"))
        shots=use.get(k,[])
        src_rng="; ".join(f"{tc(s['ss'])}–{tc(s['ss']+s['end']-s['start'])}" for s in shots)
        fin="; ".join(f"{tc(s['start'])}–{tc(s['end'])}" for s in shots)
        topics=" / ".join(dict.fromkeys(s['note'][:60] for s in shots))
        auth="Rasmiy kanal; kadr mazmuni audio bilan solishtirildi" if k not in("y14","y15") else "Qayta joylovchi kanal; shaxs va iqtibos boshqa nashrlar bilan mos, asl manba aniqlanmagan"
        w.writerow([title,url,ch,topics,src_rng,"snapyt.app (1080p/720p/480p MP4, faqat video)","Yuklandi",f"{meta['quality']} ({probe(f'{ROOT}/public/'+f_)})",auth,"Ruxsat olinmagan. Yangilik/sharh maqsadida qisqa parchalar (Fair Use daʼvosi; kafolat emas). Asl ovoz ishlatilmagan.",fin])
    for name,(vid,title,ch,why) in UNUSED_YT.items():
        p=f"{ROOT}/public/youtube_footage/{name}.mp4"
        q=json.load(open(p[:-4]+".snapyt.json"))["quality"] if os.path.exists(p[:-4]+".snapyt.json") else ""
        w.writerow([title,f"https://www.youtube.com/watch?v={vid}",ch,"—","—","snapyt.app","Yuklandi",q,why,"—","Ishlatilmagan"])
# --- X ---
idx=json.load(open(f"{ROOT}/x_footage_index.json"))
with open(f"{OUT}/X_Footage_Report.csv","w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f)
    w.writerow(["Fayl","Asl X post URL","Akkaunt","Post sanasi","Davomiylik (s)","Sifat","Takror (md5)","Post matni (qisqa)","Yakuniy videoda ishlatilgan timestamp(lar)","Autentiklik izohi"])
    fmap={v[0].split('/')[-1]:k for k,v in SRC.items() if k.startswith('x')}
    for r in idx:
        k=fmap.get(r["file"]); shots=use.get(k,[]) if k else []
        fin="; ".join(f"{tc(s['start'])}–{tc(s['end'])} (asl: {tc(s['ss'])})" for s in shots) or "Ishlatilmagan"
        note="IRGC tarqatgan kadr / qayta joylangan; mustaqil tasdiq yo‘q" if "IRGC" in r["text"] or "Revolutionary" in r["text"] or "IRGC" in (SRC[k][1] if k else "") else "Ikkilamchi akkaunt; asl manba ko‘rsatilgan joyda keltirildi"
        w.writerow([r["file"],r["post"],"@"+(r["handle"] or ""),r["date"],r["dur"],r["res"],r["dup_of"] or "",r["text"][:200],fin,note])
# --- Sahnalar ro'yxati ---
with open(f"{OUT}/Scene_Timecodes.csv","w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f); w.writerow(["Kadr","Boshlanish","Tugash","Audio matni / maqsad","Vizual manba","Manba ichidagi boshlanish","Rejim","Ekrandagi kredit","Asl havola"])
    for s in sb["shots"]:
        w.writerow([s["id"],tc(s["start"]),tc(s["end"]),s["note"],s.get("file","Grafika: "+s["mode"]),tc(s["ss"]) if s["src"]!="GFX" else "",s["mode"],s.get("credit","XARITA/GRAFIKA: original (Natural Earth)"),s.get("url","")])
print("ok")
