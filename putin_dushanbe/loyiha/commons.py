import sys,re,json,time,urllib.parse,urllib.request,html,os
UA={'User-Agent':'Mozilla/5.0'}
def get(u):
    for i in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=60).read()
        except Exception as e:
            time.sleep(3*(i+1)); err=e
    raise err
def info(title):
    u='https://commons.wikimedia.org/wiki/'+urllib.parse.quote(title.replace(' ','_'))
    h=get(u).decode('utf8','ignore').replace('&#95;','_')
    orig=re.search(r'href="(https://upload\.wikimedia\.org/wikipedia/commons/[0-9a-f]/[0-9a-f]{2}/[^"]+)"[^>]*class="internal"',h) or re.search(r'class="fullMedia"[^>]*>\s*<p>\s*<a href="(https://upload[^"]+)"',h) or re.search(r'(https://upload\.wikimedia\.org/wikipedia/commons/[0-9a-f]/[0-9a-f]{2}/[^"?]+)',h)
    lic=re.findall(r'class="licensetpl_short"[^>]*>(.*?)</span>',h); attr=re.findall(r'class="licensetpl_attr"[^>]*>(.*?)</span>',h)
    auth=re.search(r'id="fileinfotpl_aut"[^>]*>.*?</td>\s*<td[^>]*>(.*?)</td>',h,re.S)
    src=re.search(r'id="fileinfotpl_src"[^>]*>.*?</td>\s*<td[^>]*>(.*?)</td>',h,re.S)
    date=re.search(r'id="fileinfotpl_date"[^>]*>.*?</td>\s*<td[^>]*>(.*?)</td>',h,re.S)
    desc=re.search(r'class="description[^"]*"[^>]*>(.*?)</div>',h,re.S)
    clean=lambda m: re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',m.group(1)))).strip()[:300] if m else ''
    return dict(title=title,page=u,url=html.unescape(orig.group(1)).split('?')[0] if orig else None,license=sorted(set(html.unescape(x).strip() for x in lic)),attr=sorted(set(re.sub(r'<[^>]+>','',html.unescape(x)).strip() for x in attr)),author=clean(auth),source=clean(src),date=clean(date),desc=clean(desc))
if __name__=='__main__':
    out=sys.argv[1]; titles=[l.strip() for l in open(sys.argv[2]) if l.strip()]
    res=json.load(open(out)) if os.path.exists(out) else {}
    for t in titles:
        if t in res: continue
        try: res[t]=info(t); print(t, res[t]['license'], res[t]['author'][:60], flush=True)
        except Exception as e: print('ERR',t,e)
        json.dump(res,open(out,'w'),ensure_ascii=False,indent=1); time.sleep(1.5)
