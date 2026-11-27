"""Original (o'zimiz sintez qilgan) fon musiqasi va SFX — litsenziya muammosi yo'q."""
import numpy as np, wave, sys
SR=48000
def save(name,x):
    x=np.asarray(x,dtype=np.float64)
    if x.ndim==1: x=np.stack([x,x],1)
    x=x/ (np.max(np.abs(x))+1e-9)*0.89
    w=wave.open(name,'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x*32767).astype('<i2').tobytes()); w.close()
def t_(d): return np.arange(int(SR*d))/SR
def lp(x,a):  # one-pole lowpass, a in (0,1)
    y=np.empty_like(x); s=0.0
    for i in range(len(x)): s+=a*(x[i]-s); y[i]=s
    return y
def lp_fast(x,cut):
    # FFT brickwall-ish smooth lowpass
    X=np.fft.rfft(x); f=np.fft.rfftfreq(len(x),1/SR); X*=1/(1+(f/cut)**4); return np.fft.irfft(X,len(x))
def hp_fast(x,cut):
    X=np.fft.rfft(x); f=np.fft.rfftfreq(len(x),1/SR); X*=1-1/(1+(f/cut)**4); return np.fft.irfft(X,len(x))
rng=np.random.default_rng(7)
# ---------- SFX ----------
d=1.2; t=t_(d); n=rng.standard_normal(len(t))
sweep=np.exp(-((t-0.55)/0.28)**2)
wh=hp_fast(n,300)*sweep; wh=lp_fast(wh,5000); save('public/sfx/whoosh.wav',wh)
d=2.5; t=t_(d)
boom=np.sin(2*np.pi*(38+50*np.exp(-t*8))*t)*np.exp(-t*2.2)+0.4*lp_fast(rng.standard_normal(len(t)),900)*np.exp(-t*6)
save('public/sfx/impact.wav',np.tanh(boom*1.8))
d=4.0; t=t_(d); n=rng.standard_normal(len(t))
ris=hp_fast(n,500)*(t/d)**2.2; ris+=0.3*np.sin(2*np.pi*(200+600*(t/d)**2)*t)*(t/d)**2
ris[-int(0.05*SR):]*=np.linspace(1,0,int(0.05*SR)); save('public/sfx/riser.wav',ris)
d=0.12; t=t_(d); tick=np.sin(2*np.pi*2400*t)*np.exp(-t*60); save('public/sfx/tick.wav',tick)
d=0.6; t=t_(d); n=rng.standard_normal(len(t)); gl=np.sign(np.sin(2*np.pi*90*t))*0.3+hp_fast(n,2000)*((t*40%1)>0.5); gl*=np.exp(-t*5); save('public/sfx/glitch.wav',gl)
d=1.6; t=t_(d); hit=np.sin(2*np.pi*55*t)*np.exp(-t*3)+0.5*np.sin(2*np.pi*110*t)*np.exp(-t*4)+0.25*hp_fast(rng.standard_normal(len(t)),3000)*np.exp(-t*25)
save('public/sfx/hit.wav',hit)
# ---------- MUSIC BED ----------
DUR=float(sys.argv[1]) if len(sys.argv)>1 else 340.0
N=int(SR*DUR); t=np.arange(N)/SR
bpm=96; beat=60/bpm; e8=beat/2
# chord roots (D minor - Bb - F - C ) per 4 bars
prog=[(73.42,[146.83,174.61,220.0]),(58.27,[116.54,146.83,174.61]),(87.31,[174.61,220.0,261.63]),(65.41,[130.81,164.81,196.0])]
bar=4*beat; music=np.zeros(N)
# intensity envelope by section (seconds)
def env_points(pts):
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; return np.interp(t,xs,ys)
inten=env_points([(0,1.0),(16,1.0),(18,0.55),(77,0.55),(79,0.75),(126,0.75),(128,0.9),(167,0.9),(169,0.6),(245,0.6),(247,0.85),(305,0.85),(308,0.7),(DUR-6,0.7),(DUR,0.0)])
# drone
ci=((t//(4*bar)).astype(int))%4
root=np.array([p[0] for p in prog])[ci]
phase=2*np.pi*np.cumsum(root)/SR
drone=0.5*np.sin(phase)+0.25*np.sin(2*phase)+0.15*np.sin(0.5*phase)
drone*=0.8+0.2*np.sin(2*np.pi*0.07*t)
music+=drone*0.55
# pad (detuned saw-ish via additive) slow
pad=np.zeros(N)
for k in range(3):
    fr=np.array([p[1][k] for p in prog])[ci]
    ph=2*np.pi*np.cumsum(fr)/SR
    for h,a in [(1,1),(2,.35),(3,.18)]:
        pad+=a*(np.sin(h*ph)+np.sin(h*ph*1.004))
pad=lp_fast(pad,1800)*0.07
music+=pad
# pulse arpeggio 8th notes
pulse=np.zeros(N); step=int(e8*SR); env=np.exp(-np.arange(step)/SR*14)
for i,s0 in enumerate(range(0,N-step,step)):
    tt=s0/SR; c=int(tt//(4*bar))%4; notes=prog[c][1]
    f=notes[[0,1,2,1][i%4]]*2
    seg=np.arange(step)/SR
    pulse[s0:s0+step]+=np.sign(np.sin(2*np.pi*f*seg))*0.5*env+np.sin(2*np.pi*f*seg)*env
pulse=lp_fast(pulse,2500)*0.11
music+=pulse*np.clip((inten-0.5)*2.2,0.15,1)
# ticking hats (16ths)
hat=np.zeros(N); s16=int(beat/4*SR); hn=hp_fast(rng.standard_normal(s16),6000)*np.exp(-np.arange(s16)/SR*120)
for i,s0 in enumerate(range(0,N-s16,s16)): hat[s0:s0+s16]+=hn*(1.0 if i%4==2 else 0.45)
music+=hat*0.05*np.clip((inten-0.55)*3,0,1)
# kick on beats in intense parts
kk=int(0.4*SR); kt=np.arange(kk)/SR; kick=np.sin(2*np.pi*(45+90*np.exp(-kt*30))*kt)*np.exp(-kt*9)
for i,s0 in enumerate(range(0,N-kk,int(beat*SR))):
    if i%2==0: music[s0:s0+kk]+=kick*0.55*max(0,(inten[s0]-0.7)*3.3)
music*=inten
fade=int(3*SR); music[-fade:]*=np.linspace(1,0,fade); music[:int(0.3*SR)]*=np.linspace(0,1,int(0.3*SR))
L=music; R=np.roll(music,int(0.011*SR))*0.96+0.04*music
save('public/music/news_bed_original.wav',np.stack([L,R],1))
print('done')
