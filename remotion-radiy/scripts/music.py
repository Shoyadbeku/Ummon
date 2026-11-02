import numpy as np, subprocess, json, wave
SR=48000; HOOK=3.0; TOTAL=62.0; N=int(SR*TOTAL)
t=np.arange(N)/SR
rng=np.random.default_rng(7)
def midi(m): return 440*2**((m-69)/12)
out=np.zeros((N,2))
def add(sig,start,gain=1.0,pan=0.0):
    i=int(start*SR); j=min(N,i+len(sig))
    if j<=i: return
    s=sig[:j-i]*gain
    out[i:j,0]+=s*np.sqrt(0.5*(1-pan)); out[i:j,1]+=s*np.sqrt(0.5*(1+pan))
def env(n,a,r):
    e=np.ones(n); A=int(a*SR); R=int(r*SR)
    e[:A]=np.linspace(0,1,A); e[-R:]*=np.linspace(1,0,R); return e
def lp(x,a):  # one-pole lowpass
    y=np.empty_like(x); acc=0.0
    import scipy.signal as ss
    return ss.lfilter([1-a],[1,-a],x)
def pad(notes,dur,bright=0.3):
    n=int(dur*SR); tt=np.arange(n)/SR; s=np.zeros(n)
    for m in notes:
        f=midi(m)
        for det in (-0.12,0,0.11):
            ff=f*2**(det/12)
            ph=rng.uniform(0,6.28)
            s+=np.sin(2*np.pi*ff*tt+ph)+bright*0.5*np.sin(4*np.pi*ff*tt+ph)+bright*0.25*np.sin(6*np.pi*ff*tt)
    s*=env(n,1.2,1.5)*(1+0.15*np.sin(2*np.pi*0.25*tt))
    return s/ (len(notes)*3)
def piano(m,dur=2.5):
    n=int(dur*SR); tt=np.arange(n)/SR; f=midi(m)
    s=sum((0.6**k)*np.sin(2*np.pi*f*(k+1)*tt)*np.exp(-tt*(2.2+k*1.5)) for k in range(5))
    s*=np.minimum(1,tt/0.005); return s*0.5
def kick(gain=1):
    n=int(0.5*SR); tt=np.arange(n)/SR
    f=50+90*np.exp(-tt*30); s=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*9); return s*gain
def boom(dur=3.0):
    n=int(dur*SR); tt=np.arange(n)/SR
    f=38+70*np.exp(-tt*8); s=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*1.6)
    nz=lp(rng.standard_normal(n),0.97)*np.exp(-tt*5)*0.6
    return (s+nz)*np.minimum(1,tt/0.003)
def whoosh(dur=0.7,rev=False):
    n=int(dur*SR); tt=np.arange(n)/SR; x=rng.standard_normal(n)
    import scipy.signal as ss
    out=np.zeros(n); seg=1024
    for i in range(0,n,seg):
        p=i/n; fc=300+4000*np.sin(np.pi*p)**2
        b,a=ss.butter(2,[max(80,fc*0.5)/(SR/2),min(0.95,fc*1.6/(SR/2))],'band')
        out[i:i+seg]=ss.lfilter(b,a,x[i:i+seg])
    e=np.sin(np.pi*tt/dur)**2
    return out*e*1.4
def riser(dur):
    n=int(dur*SR); tt=np.arange(n)/SR; p=tt/dur
    f=100*2**(p*3.5); s=np.sin(2*np.pi*np.cumsum(f)/SR)*0.4
    import scipy.signal as ss
    x=rng.standard_normal(n); b,a=ss.butter(2,0.3,'high'); nz=ss.lfilter(b,a,x)*0.25
    return (s+nz)*p**2.5
# ---- HOOK
add(boom(2.5),0.0,0.9)
add(riser(2.9),0.05,0.7)
add(piano(57,4),0.0,0.35); add(piano(64,4),0.0,0.25)
add(boom(3.5),2.92,1.0)
# ---- body: dark section
beat=60/72; bar=4*beat
dark=[[45,52,57,60],[41,48,53,57],[48,55,60,64],[40,47,52,56]]   # Am F C E
light=[[48,55,60,64],[43,50,55,59],[45,52,57,60],[41,48,53,57]]  # C G Am F
WIN=HOOK+39.2
tb=HOOK; k=0
while tb<TOTAL-1:
    ch=dark[k%4] if tb<WIN-0.1 else light[k%4]
    d=min(bar, (WIN-tb) if tb<WIN-0.1 else bar)
    if d<0.5: tb=WIN; k=0; continue
    br=0.25 if tb<WIN else 0.6
    add(pad(ch,d+1.5,br),tb,0.55)
    # arpeggio
    arp=[ch[1]+12,ch[2]+12,ch[3]+12,ch[2]+12] if tb<WIN else [ch[0]+24,ch[2]+12,ch[3]+12,ch[1]+24,ch[3]+12,ch[2]+12,ch[0]+24,ch[3]+12]
    step=beat if tb<WIN else beat/2
    for i,m in enumerate(arp):
        st=tb+i*step
        if st<tb+d-0.05: add(piano(m),st,0.22 if tb<WIN else 0.18,pan=(-0.4 if i%2 else 0.4))
    add(pad([ch[0]-12],d+1.5,0.1),tb,0.5)  # sub bass
    tb+=d; k+=1
    if abs(tb-WIN)<1e-6: k=0
# heartbeat in the dark middle
hb=HOOK+23.5
while hb<WIN-0.6:
    add(kick(0.55),hb); add(kick(0.35),hb+0.28); hb+=beat*1.25
# victory impact
add(boom(3.0),WIN-0.05,0.8)
add(riser(1.5),WIN-1.5,0.4)
# ---- transition whooshes
cuts=json.load(open('rv/public/cuts.json'))
for c in cuts: add(whoosh(0.6),c-0.3,0.18,pan=rng.uniform(-0.5,0.5))
# ---- ducking under voice
raw=subprocess.run(["ffmpeg","-v","quiet","-i","work/voice.wav","-ac","1","-ar",str(SR),"-f","f32le","-"],capture_output=True).stdout
v=np.frombuffer(raw,np.float32); vv=np.zeros(N); i=int(HOOK*SR); vv[i:i+len(v)]=np.abs(v[:N-i])
import scipy.signal as ss
envv=ss.lfilter([0.0005],[1,-0.9995],vv); envv/=envv.max()
duck=1-0.45*np.clip(envv*4,0,1)
out*=duck[:,None]
# master fade in/out
fo=np.ones(N); F=int(2.0*SR); fo[-F:]=np.linspace(1,0,F)
out*=fo[:,None]
out/=np.abs(out).max(); out*=0.5
pcm=(out*32767).astype('<i2')
w=wave.open('rv/public/music.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok')
