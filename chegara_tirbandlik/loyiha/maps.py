import shapefile, math, sys, json
from PIL import Image, ImageDraw, ImageFilter
NE=sys.argv[1]; OUT=sys.argv[2]
BG=(9,16,28); LAND=(24,36,54); FOCUS=(32,50,76); BORDER=(120,160,210); HL=(196,60,48)
def proj(view,W):
    lon0,lon1,lat0,lat1=view; latc=(lat0+lat1)/2; c=math.cos(math.radians(latc))
    k=W/((lon1-lon0)*c); H=int((lat1-lat0)*k)
    return (lambda lon,lat: ((lon-lon0)*c*k,(lat1-lat)*k)), W, H
def polys(shp):
    for s in shp.shapes():
        pts=s.points; parts=list(s.parts)+[len(pts)]
        yield s.bbox,[pts[parts[i]:parts[i+1]] for i in range(len(parts)-1)]
def render(name,view,W,hl_regions=(),focus=("KAZ","UZB")):
    P,W,H=proj(view,W)
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    c=shapefile.Reader(NE+"/ne_10m_admin_0_countries.shp")
    fn=[f[0] for f in c.fields[1:]]; ia=fn.index("ADM0_A3")
    lon0,lon1,lat0,lat1=view
    recs=c.records()
    for rec,(bb,parts) in zip(recs,polys(c)):
        if bb[2]<lon0-2 or bb[0]>lon1+2 or bb[3]<lat0-2 or bb[1]>lat1+2: continue
        col={"UZB":(40,62,96),"KAZ":(28,43,66)}.get(rec[ia],LAND)
        for p in parts: d.polygon([P(*q) for q in p],fill=col)
    a=shapefile.Reader(NE+"/ne_10m_admin_1_states_provinces.shp")
    fa=[f[0] for f in a.fields[1:]]; inm=fa.index("name"); i0=fa.index("adm0_a3")
    hl=Image.new("L",(W,H),0); dh=ImageDraw.Draw(hl)
    for rec,(bb,parts) in zip(a.records(),polys(a)):
        if bb[2]<lon0-2 or bb[0]>lon1+2 or bb[3]<lat0-2 or bb[1]>lat1+2: continue
        if (rec[i0],rec[inm]) in hl_regions:
            for p in parts: dh.polygon([P(*q) for q in p],fill=255)
        for p in parts: d.line([P(*q) for q in p]+[P(*p[0])],fill=(44,62,88),width=max(1,W//4000))
    # lakes & rivers
    l=shapefile.Reader(NE+"/ne_10m_lakes.shp")
    for bb,parts in polys(l):
        if bb[2]<lon0 or bb[0]>lon1 or bb[3]<lat0 or bb[1]>lat1: continue
        for p in parts: d.polygon([P(*q) for q in p],fill=(18,40,66))
    r=shapefile.Reader(NE+"/ne_10m_rivers_lake_centerlines.shp")
    for bb,parts in polys(r):
        if bb[2]<lon0 or bb[0]>lon1 or bb[3]<lat0 or bb[1]>lat1: continue
        for p in parts: d.line([P(*q) for q in p],fill=(52,110,170),width=max(3,W//1800))
    for rec,(bb,parts) in zip(recs,polys(c)):
        if bb[2]<lon0-2 or bb[0]>lon1+2 or bb[3]<lat0-2 or bb[1]>lat1+2: continue
        w=max(2,W//1400) if rec[ia] in focus else max(1,W//2500)
        for p in parts: d.line([P(*q) for q in p]+[P(*p[0])],fill=BORDER,width=w)
    im.save(f"{OUT}/{name}.png"); hl.save(f"{OUT}/{name}_hl.png")
    json.dump({"view":view,"W":W,"H":H},open(f"{OUT}/{name}.json","w"))
    print(name,W,H)
render("wide",(28,98,24,60),8000,focus=("KAZ","UZB"))
render("close",(65.0,72.5,39.6,43.6),8000,hl_regions=(("KAZ","South Kazakhstan"),("UZB","Tashkent")))
