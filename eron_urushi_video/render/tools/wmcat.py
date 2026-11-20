import json,sys,re,html
import os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from wm import api
out=sys.argv[1]; depth=int(sys.argv[2]); cats=sys.argv[3:]
seen=set(); files={}
def strip(s): return html.unescape(re.sub('<[^>]+>','',s or '')).strip()
def walk(cat,d):
    if cat in seen: return
    seen.add(cat)
    cont={}
    while True:
        r=api({"action":"query","generator":"categorymembers","gcmtitle":cat,"gcmlimit":"200","gcmtype":"file|subcat",
               "prop":"imageinfo","iiprop":"url|size|mime|extmetadata|mediatype","iiurlwidth":"1920",
               "iiextmetadatafilter":"LicenseShortName|Artist|ImageDescription|DateTimeOriginal|Credit|UsageTerms|LicenseUrl",**cont})
        for p in r.get("query",{}).get("pages",[]):
            if p["ns"]==14:
                if d>0: walk(p["title"],d-1)
            elif "imageinfo" in p:
                ii=p["imageinfo"][0]; m=ii.get("extmetadata",{})
                g=lambda k:strip(m.get(k,{}).get("value"))
                files[p["title"]]=dict(cat=cat,url=ii["url"],thumb=ii.get("thumburl"),w=ii.get("width"),h=ii.get("height"),
                    mime=ii.get("mime"),dur=ii.get("duration"),size=ii.get("size"),page=ii.get("descriptionurl"),
                    license=g("LicenseShortName"),artist=g("Artist")[:150],credit=g("Credit")[:150],date=g("DateTimeOriginal")[:40],desc=g("ImageDescription")[:300])
        if "continue" in r: cont=r["continue"]
        else: break
for c in cats: walk(c,depth)
json.dump(files,open(out,"w"),ensure_ascii=False,indent=0)
print(len(seen),"cats",len(files),"files")
