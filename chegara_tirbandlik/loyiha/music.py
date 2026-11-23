# Original synthesized underscore + SFX (no third-party samples)
import numpy as np, wave, sys
SR=48000; DUR=383.25; OUT=sys.argv[1]
N=int(SR*DUR); t=np.arange(N)/SR
rng=np.random.default_rng(7)
def note(f): return 440*2**((f-69)/12)
def pad(freqs, env):
    s=np.zeros(N)
    for i,f in enumerate(freqs):
        for det in (-0.15,0.0,0.15):
            fr=note(f+det/1.0)
            s+=np.sin(2*np.pi*fr*t+rng.uniform(0,6.28))*(0.6 if det==0 else 0.3)
    return s*env
# chord progression (A minor news-tension): Am - F - C - G (slow, 8 s each)
prog=[(45,57,60,64),(41,57,60,65),(48,55,60,64),(43,55,59,62)]
L=8.0; mus=np.zeros(N)
for i in range(int(DUR/L)+1):
    a=int(i*L*SR); b=min(N,int((i+1)*L*SR)+SR*2)
    if a>=N: break
    tt=np.arange(b-a)/SR
    env=np.minimum(1,tt/2.0)*np.minimum(1,np.maximum(0,(L+2-tt)/2.0))
    seg=np.zeros(b-a)
    for f in prog[i%4]:
        for det in (-0.08,0,0.08):
            seg+=np.sin(2*np.pi*note(f+det)*tt+rng.uniform(0,6.28))*(0.5 if det==0 else 0.25)
    mus[a:b]+=seg*env
# soft low-pass via moving average
k=np.ones(24)/24; mus=np.convolve(mus,k,mode="same")
# pulse: soft kick + ticking hat at 96 bpm during body sections
bpm=96; beat=60/bpm
pulse=np.zeros(N)
kick_len=int(0.35*SR); kt=np.arange(kick_len)/SR
kick=np.sin(2*np.pi*(50+60*np.exp(-kt*25))*kt)*np.exp(-kt*9)
hat_len=int(0.05*SR); hat=rng.normal(0,1,hat_len)*np.exp(-np.arange(hat_len)/SR*90); hat=np.diff(np.concatenate([[0],hat]))
def active(x): return (6<x<95) or (100<x<266) or (270<x<351)
nb=int(DUR/beat)
for i in range(nb):
    x=i*beat; a=int(x*SR)
    if not active(x): continue
    if i%2==0 and a+kick_len<N: pulse[a:a+kick_len]+=kick*0.9
    h=int((x+beat/2)*SR)
    if h+hat_len<N: pulse[h:h+hat_len]+=hat*0.12
mus=mus/np.max(np.abs(mus))*0.5+pulse*0.35
# global dynamics: fade in/out, swell in hook and ending
g=np.ones(N)
g*=np.minimum(1,t/1.5); g*=np.minimum(1,(DUR-t)/4)
mus*=g
st=np.stack([mus*0.97,np.roll(mus,240)],axis=1)
st=st/np.max(np.abs(st))*0.8
def wr(name,x):
    x=np.clip(x,-1,1); w=wave.open(name,"wb"); w.setnchannels(2 if x.ndim==2 else 1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x*32767).astype(np.int16).tobytes()); w.close()
wr(OUT+"/music.wav",st)
# SFX track
sfx=np.zeros(N)
def whoosh(at,dur=0.7,amp=0.5):
    n=int(dur*SR); x=rng.normal(0,1,n); env=np.sin(np.pi*np.linspace(0,1,n))**2
    # sweeping one-pole lowpass
    y=np.zeros(n); a=0.0
    for j in range(0,n):
        c=0.02+0.25*(j/n); a+= c*(x[j]-a); y[j]=a
    s=int(at*SR); sfx[s:s+n]+=y*env*amp*4
def impact(at,amp=0.9):
    n=int(1.6*SR); tt=np.arange(n)/SR
    y=np.sin(2*np.pi*(38+70*np.exp(-tt*12))*tt)*np.exp(-tt*2.8)+rng.normal(0,1,n)*np.exp(-tt*30)*0.3
    s=int(at*SR); sfx[s:s+n]+=y*amp
for at in (0.0,95.0,266.6,351.0): impact(at)
for at in (19.9,36.0,48.4,78.2,99.6,111.0,128.0,134.4,152.8,167.4,178.2,199.2,209.8,225.4,242.4,250.8,269.9,301.4,324.6,371.4): whoosh(max(0,at-0.25),amp=0.35)
wr(OUT+"/sfx.wav",sfx/np.max(np.abs(sfx))*0.7)
print("done")
