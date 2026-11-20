import json,os,time,subprocess,glob,sys
UA='UmmonNewsEditor/1.0 (educational news video); curl'
cat={}
for f in glob.glob('cat_*.json'): cat.update(json.load(open(f)))
sel=json.load(open('sel.json')); plan=json.load(open('vid_plan.json'))
low={'v_b2','v_trump_update','v_tehran_cars','v_iran_missile'}
meta={}; todo=[]
for key,title in sel.items():
    if title not in cat: title=[t for t in cat if t.startswith(title)][0]
    v=cat[title]; base=v['url'].split('?')[0]; parts=base.split('/commons/')[1]; name=parts.split('/')[-1]
    if key.startswith('v_'):
        url=base if key in low else plan[key]; ext='.webm'
    else:
        w=v['w'] or 0
        tw=3840 if w>3840 else (1920 if w>1920 else (1280 if w>1280 else 960))
        th=name+('.jpg' if name.lower().endswith(('.webp','.tif','.tiff')) else ('.png' if name.lower().endswith('.svg') else ''))
        url=f"https://thumb.wikimedia.org/wikipedia/commons/thumb/{parts}/{tw}px-{th}"
        if w<=960: url=base
        ext=os.path.splitext(th)[1].lower() if w>960 else os.path.splitext(name)[1].lower()
    out=f'assets/{key}{ext}'
    meta[key]=dict(title=title,**v,file=out,dl=url)
    if not (os.path.exists(out) and os.path.getsize(out)>1000): todo.append((key,url,out))
json.dump(meta,open('assets_meta.json','w'),ensure_ascii=False,indent=1)
wait=5
while todo:
    key,url,out=todo.pop(0)
    r=subprocess.run(['curl','-s','-m','900','-A',UA,'-o',out+'.part','-w','%{http_code}',url],capture_output=True,text=True)
    code=r.stdout.strip()
    if code=='200':
        os.replace(out+'.part',out); print('ok',key,os.path.getsize(out)//1024,'KB',flush=True); wait=max(5,wait//2)
    else:
        print('fail',key,code,flush=True)
        if code=='429': todo.append((key,url,out)); wait=min(90,wait*2)
        elif code=='404' and key in low:
            print('404 skip',key,flush=True)
    time.sleep(wait)
print('DONE',flush=True)
