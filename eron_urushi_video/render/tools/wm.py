import json,sys,time,urllib.request,urllib.parse
UA='UmmonNewsEditor/1.0 (educational news video; contact via repo)'
def api(params,host="commons.wikimedia.org"):
    params={**params,"format":"json","formatversion":"2"}
    u=f"https://{host}/w/api.php?"+urllib.parse.urlencode(params)
    for i in range(8):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":UA}),timeout=60)
            return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code==429:
                ra=int(e.headers.get("retry-after") or 20); time.sleep(ra+2); continue
            raise
    raise SystemExit("rate limited")
if __name__=="__main__":
    print(json.dumps(api(dict(a.split("=",1) for a in sys.argv[1:])),ensure_ascii=False,indent=1)[:20000])
