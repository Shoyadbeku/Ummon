import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, OffthreadVideo, random, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {ANTON, CYAN, f, FPS, GOLD, GREEN, MONT, RED, RetroBrowser, Scanlines, YELLOW} from './fx';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const eo = Easing.bezier(0.16, 1, 0.3, 1);
const sh = '0 6px 0 rgba(0,0,0,0.55), 0 0 40px rgba(0,0,0,0.6)';
const GOLD_GRAD = 'linear-gradient(180deg,#FFF6C8 0%,#FFD23F 45%,#E89B0C 100%)';
const ICE_GRAD = 'linear-gradient(180deg,#FFFFFF 0%,#BFF4FF 50%,#4FE3FF 100%)';
const gradText = (g: string, glow = 'rgba(255,200,60,0.6)'): React.CSSProperties => ({backgroundImage: g, WebkitBackgroundClip: 'text', backgroundClip: 'text', WebkitTextFillColor: 'transparent', filter: `drop-shadow(0 6px 0 rgba(0,0,0,0.6)) drop-shadow(0 0 30px ${glow})`});
const useSp = (delay = 0, cfg: any = {damping: 14, stiffness: 170}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - delay, fps, config: cfg});
};
const at = (sec: number, base: number) => Math.round((sec - base) * FPS); // absolute sec -> local frame

/** Dark animated backdrop with drifting particles and soft color blobs. */
export const BgDark: React.FC<{hue?: number; grid?: boolean}> = ({hue = 210, grid}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{background: `radial-gradient(ellipse at 50% 30%, hsl(${hue},45%,16%) 0%, hsl(${hue},40%,6%) 55%, #030407 100%)`}}>
      {grid && <AbsoluteFill style={{backgroundImage: 'linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)', backgroundSize: '90px 90px', backgroundPosition: `0 ${frame * 0.6}px`}} />}
      <svg width="1080" height="1920" style={{position: 'absolute'}}>
        {Array.from({length: 46}).map((_, i) => {
          const x = random(`px${i}`) * 1080;
          const y = (random(`py${i}`) * 1920 - frame * (0.4 + random(`ps${i}`) * 1.2) + 1920 * 4) % 1920;
          return <circle key={i} cx={x} cy={y} r={1 + random(`pr${i}`) * 2.6} fill="white" opacity={0.15 + random(`po${i}`) * 0.35} />;
        })}
      </svg>
    </AbsoluteFill>
  );
};

const Vid: React.FC<{src: string; sf?: number; style?: React.CSSProperties; filter?: string; pos?: string}> = ({src, sf = 0, style, filter, pos = 'center'}) => (
  <OffthreadVideo src={staticFile(src)} startFrom={Math.round(sf * FPS)} muted style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: pos, filter, ...style}} />
);

const Label: React.FC<{text: string; color?: string; size?: number; style?: React.CSSProperties; grad?: string}> = ({text, color = 'white', size = 120, style, grad}) => (
  <div style={{fontFamily: ANTON, fontSize: size, color, letterSpacing: 3, textShadow: grad ? undefined : sh, lineHeight: 1.02, textAlign: 'center', whiteSpace: 'pre-line', ...(grad ? gradText(grad) : {}), ...style}}>{text}</div>
);

// ------------------------------------------------------------------ scenes
/** Two brothers: photo panels slide in + idea bulb. base = scene start (s) */
export const Brothers: React.FC<{variant?: 1 | 2}> = ({variant = 1}) => {
  const frame = useCurrentFrame();
  const a = useSp(0);
  const b = useSp(6);
  const n = useSp(14);
  const panel = (left: boolean, s: number): React.CSSProperties => ({position: 'absolute', top: variant === 1 ? 0 : 260, height: variant === 1 ? 1920 : 1100, width: 540, [left ? 'left' : 'right']: 0, overflow: 'hidden', transform: `translateY(${(1 - s) * (left ? -1 : 1) * 1920}px)`});
  return (
    <AbsoluteFill>
      <BgDark hue={variant === 1 ? 35 : 210} />
      <div style={panel(true, a)}><Img src={staticFile('img/musk_young.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 20%', transform: `scale(${1.15 - frame * 0.0015})`, filter: variant === 1 ? 'sepia(0.35) contrast(1.1)' : 'contrast(1.1)'}} /></div>
      <div style={panel(false, b)}><Img src={staticFile('img/kimbal.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '45% 22%', transform: `scale(${1.1 + frame * 0.0015})`, filter: variant === 1 ? 'sepia(0.35) contrast(1.1)' : 'contrast(1.1)'}} /></div>
      <div style={{position: 'absolute', left: 537, top: variant === 1 ? 0 : 260, height: variant === 1 ? 1920 : 1100, width: 6, background: YELLOW, boxShadow: `0 0 30px ${YELLOW}`, transform: `scaleY(${b})`}} />
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0.25) 0%, rgba(0,0,0,0) 30%, rgba(0,0,0,0) 50%, rgba(0,0,0,0.75) 100%)'}} />
      <div style={{position: 'absolute', top: variant === 1 ? 1150 : 1400, left: 0, right: 0, display: 'flex', justifyContent: 'space-around', opacity: n, transform: `translateY(${(1 - n) * 40}px)`}}>
        <Label text={variant === 1 ? 'ILON' : 'ILON MASK'} size={variant === 1 ? 110 : 80} color={YELLOW} />
        <Label text={variant === 1 ? 'KIMBAL' : 'KIMBAL MASK'} size={variant === 1 ? 110 : 80} color={GREEN} />
      </div>
      {variant === 2 && <div style={{position: 'absolute', top: 1540, left: 0, right: 0, opacity: n}}><Label text="AKA-UKA" size={70} color="white" /></div>}
    </AbsoluteFill>
  );
};

/** No smartphones / social networks / Google maps — items struck out on cue */
export const NoApps: React.FC<{base: number}> = ({base}) => {
  const frame = useCurrentFrame();
  const items: [string, number, string][] = [['SMARTFONLAR', 53.34, '📱'], ['IJTIMOIY TARMOQLAR', 55.14, '💬'], ['GOOGLE XARITALARI', 56.32, '📍']];
  const yo = useSp(at(57.4, base), {damping: 9, stiffness: 260});
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{filter: 'blur(6px) brightness(0.35)', transform: 'scale(1.1)'}}><Vid src="v/mk_8766.mp4" /></AbsoluteFill>
      <div style={{position: 'absolute', top: 360, left: 90, right: 90}}>
        {items.map(([t, s, icon], i) => {
          const local = at(s, base);
          const p = spring({frame: frame - local, fps: FPS, config: {damping: 14}});
          const strike = interpolate(frame, [local + 12, local + 22], [0, 1], {...clamp, easing: eo});
          return (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 30, marginBottom: 70, opacity: p, transform: `translateX(${(1 - p) * -200}px)`}}>
              <div style={{width: 130, height: 130, borderRadius: 30, background: 'rgba(255,255,255,0.12)', border: '3px solid rgba(255,255,255,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 70}}>
                <svg width="70" height="70" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  {i === 0 && <><rect x="6" y="2" width="12" height="20" rx="2.5" /><line x1="11" y1="18.5" x2="13" y2="18.5" /></>}
                  {i === 1 && <><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1.1-4.6A8 8 0 1 1 21 12z" /><circle cx="9" cy="12" r=".6" fill="white" /><circle cx="12.5" cy="12" r=".6" fill="white" /><circle cx="16" cy="12" r=".6" fill="white" /></>}
                  {i === 2 && <><path d="M12 22s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12z" /><circle cx="12" cy="10" r="2.6" /></>}
                </svg>
              </div>
              <div style={{position: 'relative'}}>
                <div style={{fontFamily: ANTON, fontSize: 84, color: 'white', letterSpacing: 2, textShadow: sh}}>{t}</div>
                <div style={{position: 'absolute', left: -10, top: '52%', height: 12, width: `${strike * 105}%`, background: RED, borderRadius: 6, boxShadow: `0 0 20px ${RED}`}} />
              </div>
            </div>
          );
        })}
      </div>
      <div style={{position: 'absolute', top: 1060, left: 0, right: 0, transform: `scale(${interpolate(yo, [0, 1], [2.5, 1])})`, opacity: Math.min(1, yo * 2)}}>
        <Label text="YO'Q" size={260} color={RED} style={{textShadow: `0 0 60px ${RED}, ${sh}`}} />
      </div>
    </AbsoluteFill>
  );
};

/** Global Link Information Network -> Zip2 */
export const NameMorph: React.FC<{base: number}> = ({base}) => {
  const frame = useCurrentFrame();
  const full = 'GLOBAL LINK\nINFORMATION\nNETWORK';
  const typed = full.slice(0, Math.floor(interpolate(frame, [at(98.4, base), at(100.4, base)], [0, full.length], clamp)));
  const swap = at(100.7, base);
  const out = interpolate(frame, [swap, swap + 8], [1, 0], clamp);
  const z = spring({frame: frame - swap - 4, fps: FPS, config: {damping: 9, stiffness: 200}});
  const intro = useSp(0);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{filter: 'brightness(0.45) saturate(1.3)'}}><Vid src="v/mk_31771.mp4" /></AbsoluteFill>
      <div style={{position: 'absolute', top: 330, left: 0, right: 0, opacity: intro}}><Label text="DASTLABKI NOMI" size={70} color={CYAN} /></div>
      <div style={{position: 'absolute', top: 620, left: 60, right: 60, opacity: out, transform: `scale(${1 - (1 - out) * 0.3})`, filter: `blur(${(1 - out) * 20}px)`}}>
        <div style={{fontFamily: 'monospace', fontWeight: 700, fontSize: 92, color: 'white', whiteSpace: 'pre-line', textAlign: 'center', lineHeight: 1.15, textShadow: '0 0 20px rgba(79,227,255,0.7)'}}>{typed}<span style={{opacity: frame % 16 < 8 ? 1 : 0}}>_</span></div>
      </div>
      {frame >= swap && (
        <div style={{position: 'absolute', top: 560, left: 0, right: 0, transform: `scale(${z})`}}>
          <div style={{fontFamily: ANTON, fontSize: 400, textAlign: 'center', ...gradText('linear-gradient(180deg,#ffffff,#9fdcff)', 'rgba(79,227,255,0.9)')}}>Zip2</div>
          <Label text="KEYINCHALIK" size={70} color={YELLOW} />
        </div>
      )}
    </AbsoluteFill>
  );
};

/** Stylised city map with pins popping (restaurants, shops, businesses) */
export const CityMap: React.FC = () => {
  const frame = useCurrentFrame();
  const pins: [number, number, string, string][] = [[300, 650, '#FF5A5F', 'R'], [720, 560, '#4FE3FF', 'D'], [520, 900, '#3DFF8A', 'K'], [220, 1130, '#FF5A5F', 'R'], [820, 1050, '#FFD23F', 'M'], [610, 1320, '#4FE3FF', 'D'], [380, 1450, '#3DFF8A', 'K'], [870, 1420, '#FF5A5F', 'R']];
  const cam = interpolate(frame, [0, 90], [1.25, 1.0], {...clamp, easing: eo});
  return (
    <AbsoluteFill style={{background: '#0b1626'}}>
      <AbsoluteFill style={{transform: `scale(${cam}) rotate(${-4 + frame * 0.03}deg)`}}>
        <svg width="1080" height="1920">
          {Array.from({length: 14}).map((_, i) => <rect key={`h${i}`} x={-100} y={i * 150 + 40} width={1300} height={i % 4 === 0 ? 26 : 12} fill={i % 4 === 0 ? '#2b4a6f' : '#1b2f48'} />)}
          {Array.from({length: 9}).map((_, i) => <rect key={`v${i}`} x={i * 140 + 20} y={-100} width={i % 3 === 0 ? 26 : 12} height={2200} fill={i % 3 === 0 ? '#2b4a6f' : '#1b2f48'} />)}
          <path d="M-50 1700 C 300 1500, 500 1650, 1150 1300" stroke="#1f6fb2" strokeWidth="60" fill="none" opacity="0.6" />
          {Array.from({length: 40}).map((_, i) => <rect key={`b${i}`} x={Math.floor(random(`bx${i}`) * 8) * 140 + 45} y={Math.floor(random(`by${i}`) * 13) * 150 + 62} width={90} height={110} rx={8} fill="#15263b" />)}
        </svg>
      </AbsoluteFill>
      {pins.map(([x, y, c, l], i) => {
        const s = spring({frame: frame - 6 - i * 5, fps: FPS, config: {damping: 8, stiffness: 220}});
        return (
          <div key={i} style={{position: 'absolute', left: x - 45, top: y - 110, width: 90, height: 110, transform: `scale(${s})`, transformOrigin: '50% 100%'}}>
            <svg width="90" height="110" viewBox="0 0 24 30"><path d="M12 29s10-9 10-17A10 10 0 0 0 2 12c0 8 10 17 10 17z" fill={c} stroke="white" strokeWidth="1.2" /><text x="12" y="15.5" textAnchor="middle" fontFamily="Montserrat" fontWeight="900" fontSize="9" fill="#0b1626">{l}</text></svg>
            <div style={{position: 'absolute', left: 25, top: 100, width: 40, height: 12, borderRadius: '50%', background: c, opacity: 0.35 * s, filter: 'blur(4px)'}} />
          </div>
        );
      })}
      <div style={{position: 'absolute', top: 240, left: 0, right: 0}}><Label text="INTERNET XARITASI" size={110} grad={ICE_GRAD} /></div>
      <div style={{position: 'absolute', top: 1620, left: 0, right: 0, display: 'flex', justifyContent: 'center', gap: 26, fontFamily: MONT, fontWeight: 900, fontSize: 34, color: 'white'}}>
        {[['#FF5A5F', 'RESTORAN'], ['#4FE3FF', "DO'KON"], ['#3DFF8A', 'KORXONA']].map(([c, t]) => <span key={t} style={{display: 'flex', alignItems: 'center', gap: 10}}><span style={{width: 26, height: 26, borderRadius: 13, background: c}} />{t}</span>)}
      </div>
    </AbsoluteFill>
  );
};

/** Needs checklist: developers, computers, internet, clients */
export const Needs: React.FC<{base: number}> = ({base}) => {
  const frame = useCurrentFrame();
  const items: [string, number][] = [['DASTURCHILAR', 135.92], ['KOMPYUTERLAR', 136.8], ['INTERNET ALOQASI', 137.84], ['MIJOZLAR', 139.0]];
  const bg = frame < at(137.84, base) ? 'v/mk_41639.mp4' : 'v/mk_23216.mp4';
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{filter: 'brightness(0.35) blur(3px)', transform: 'scale(1.08)'}}><Vid src={bg} /></AbsoluteFill>
      <div style={{position: 'absolute', top: 300, left: 0, right: 0}}><Label text="KERAK EDI:" size={110} color={YELLOW} /></div>
      <div style={{position: 'absolute', top: 520, left: 120, right: 120}}>
        {items.map(([t, s], i) => {
          const p = spring({frame: frame - at(s, base), fps: FPS, config: {damping: 12, stiffness: 200}});
          return (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 34, marginBottom: 56, opacity: p, transform: `translateY(${(1 - p) * 60}px)`}}>
              <div style={{width: 96, height: 96, borderRadius: 22, background: GREEN, display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${p})`, boxShadow: `0 0 30px ${GREEN}88`}}>
                <svg width="60" height="60" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7" stroke="#0a0a0a" strokeWidth="3.4" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
              </div>
              <div style={{fontFamily: ANTON, fontSize: 92, color: 'white', letterSpacing: 2, textShadow: sh}}>{t}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/** Day (website) / night (coding) split on the single computer */
export const DayNight: React.FC<{base: number}> = ({base}) => {
  const a = useSp(0);
  const frame = useCurrentFrame();
  const nightAt = at(164.82, base);
  const b = spring({frame: frame - nightAt, fps: FPS, config: {damping: 15}});
  const half: React.CSSProperties = {position: 'absolute', left: 0, right: 0, height: 955, overflow: 'hidden'};
  return (
    <AbsoluteFill style={{background: '#05060a'}}>
      <div style={{...half, top: 0, transform: `translateX(${(1 - a) * -1080}px)`, filter: frame >= nightAt ? 'brightness(0.5)' : 'none'}}>
        <Vid src="v/mk_13906.mp4" filter="contrast(1.1) saturate(1.2) sepia(0.2) brightness(1.05)" />
        <div style={{position: 'absolute', top: 70, left: 0, right: 0}}><Label text={'☀ KUNDUZI'} size={90} color={YELLOW} /></div>
        <div style={{position: 'absolute', bottom: 70, left: 0, right: 0}}><Label text="VEB-SAYT" size={120} /></div>
      </div>
      <div style={{...half, top: 965, transform: `translateX(${(1 - b) * 1080}px)`}}>
        <Vid src="v/mk_9757.mp4" filter="contrast(1.2) saturate(1.1) hue-rotate(-15deg) brightness(0.8)" />
        <div style={{position: 'absolute', top: 70, left: 0, right: 0}}><Label text={'☾ KECHASI'} size={90} color={CYAN} /></div>
        <div style={{position: 'absolute', bottom: 70, left: 0, right: 0}}><Label text="DASTUR YOZISH" size={120} /></div>
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 952, height: 16, background: 'white', boxShadow: '0 0 30px white'}} />
      <div style={{position: 'absolute', left: 390, top: 860, width: 300, height: 200, borderRadius: 30, background: '#111', border: '6px solid white', display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${a})`}}>
        <div style={{fontFamily: ANTON, fontSize: 70, color: 'white'}}>1 PC</div>
      </div>
    </AbsoluteFill>
  );
};

/** Internet users growth chart 1995–1999 (source: Internet World Stats) */
export const InternetChart: React.FC = () => {
  const frame = useCurrentFrame();
  const data: [string, number][] = [['1995', 16], ['1996', 36], ['1997', 70], ['1998', 147], ['1999', 248]];
  const max = 260;
  return (
    <AbsoluteFill>
      <BgDark hue={200} grid />
      <div style={{position: 'absolute', top: 260, left: 0, right: 0}}><Label text={'INTERNET\nTEZ O‘SMOQDA'} size={120} grad={ICE_GRAD} /></div>
      <div style={{position: 'absolute', top: 600, left: 0, right: 0}}><div style={{fontFamily: MONT, fontWeight: 800, fontSize: 36, color: 'rgba(255,255,255,0.75)', textAlign: 'center'}}>Dunyo bo‘yicha foydalanuvchilar, mln</div></div>
      <div style={{position: 'absolute', left: 90, right: 90, top: 700, height: 760, display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', borderBottom: '4px solid rgba(255,255,255,0.6)'}}>
        {data.map(([y, v], i) => {
          const p = interpolate(frame, [4 + i * 9, 24 + i * 9], [0, 1], {...clamp, easing: eo});
          const h = (v / max) * 700 * p;
          return (
            <div key={y} style={{width: 150, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-end', height: '100%'}}>
              <div style={{fontFamily: ANTON, fontSize: 58, color: i === data.length - 1 ? GREEN : 'white', opacity: p, marginBottom: 10}}>{Math.round(v * p)}</div>
              <div style={{width: '100%', height: h, borderRadius: '16px 16px 0 0', background: i === data.length - 1 ? `linear-gradient(180deg, ${GREEN}, #129a4b)` : `linear-gradient(180deg, ${CYAN}, #1a5f8a)`, boxShadow: i === data.length - 1 ? `0 0 40px ${GREEN}88` : 'none'}} />
              <div style={{position: 'absolute', bottom: -70, fontFamily: MONT, fontWeight: 900, fontSize: 40, color: 'white'}}>{y}</div>
            </div>
          );
        })}
      </div>
      <div style={{position: 'absolute', bottom: 250, left: 0, right: 0, fontFamily: MONT, fontWeight: 700, fontSize: 26, color: 'rgba(255,255,255,0.5)', textAlign: 'center'}}>Manba: Internet World Stats</div>
    </AbsoluteFill>
  );
};

export const BrowserScene: React.FC<{base: number}> = ({base}) => (
  <AbsoluteFill>
    <AbsoluteFill style={{filter: 'brightness(0.4) saturate(1.1)'}}><Vid src="v/mk_14043.mp4" /></AbsoluteFill>
    <Scanlines opacity={0.15} />
    <RetroBrowser at={0} until={2.6 + 0.3} y={560} stampAt={99} />
    <div style={{position: 'absolute', top: 330, left: 0, right: 0}}><Label text="GAZETALAR UCHUN" size={100} color={YELLOW} /></div>
  </AbsoluteFill>
);

/** Print vs internet split with big question mark */
export const PrintWeb: React.FC = () => {
  const a = useSp(0);
  const b = useSp(5);
  const q = useSp(40, {damping: 8, stiffness: 220});
  const half: React.CSSProperties = {position: 'absolute', left: 0, right: 0, height: 955, overflow: 'hidden'};
  return (
    <AbsoluteFill style={{background: '#05060a'}}>
      <div style={{...half, top: 0, transform: `translateY(${(1 - a) * -960}px)`}}>
        <Vid src="v/mk_41192.mp4" filter="contrast(1.1) sepia(0.25)" />
        <div style={{position: 'absolute', top: 230, left: 0, right: 0}}><Label text="BOSMA GAZETA" size={120} /></div>
      </div>
      <div style={{...half, top: 965, transform: `translateY(${(1 - b) * 960}px)`}}>
        <Vid src="v/mk_41201.mp4" filter="contrast(1.1) saturate(1.1)" />
        <div style={{position: 'absolute', bottom: 260, left: 0, right: 0}}><Label text="INTERNET" size={130} grad={ICE_GRAD} /></div>
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 952, height: 16, background: YELLOW}} />
      <div style={{position: 'absolute', left: 390, top: 810, width: 300, height: 300, borderRadius: 150, background: YELLOW, display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${q}) rotate(${(1 - q) * -90}deg)`, boxShadow: `0 0 60px ${YELLOW}`}}>
        <div style={{fontFamily: ANTON, fontSize: 230, color: '#111', marginTop: -10}}>?</div>
      </div>
    </AbsoluteFill>
  );
};

/** Org chart: CEO box, Musk struck out, replaced */
export const OrgChart: React.FC<{year?: string; label: string; base: number; strikeAt: number}> = ({year, label, base, strikeAt}) => {
  const frame = useCurrentFrame();
  const intro = useSp(0);
  const st = at(strikeAt, base);
  const strike = interpolate(frame, [st, st + 10], [0, 1], {...clamp, easing: eo});
  const nw = spring({frame: frame - st - 14, fps: FPS, config: {damping: 11}});
  const box: React.CSSProperties = {width: 760, padding: '34px 30px', borderRadius: 28, border: '4px solid rgba(255,255,255,0.6)', background: 'rgba(255,255,255,0.07)', textAlign: 'center'};
  return (
    <AbsoluteFill>
      <BgDark hue={0} />
      {year && <div style={{position: 'absolute', top: 230, left: 0, right: 0}}><Label text={year} size={150} grad={GOLD_GRAD} /></div>}
      <div style={{position: 'absolute', top: year ? 460 : 330, left: 0, right: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 40, opacity: intro, transform: `translateY(${(1 - intro) * 80}px)`}}>
        <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 52, color: YELLOW, letterSpacing: 4}}>BOSH DIREKTOR</div>
        <div style={{...box, position: 'relative'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 30, justifyContent: 'center'}}>
            <Img src={staticFile('img/musk_2015.jpg')} style={{width: 150, height: 150, borderRadius: 75, objectFit: 'cover', objectPosition: '50% 20%', filter: strike > 0.5 ? 'grayscale(1) brightness(0.6)' : 'none'}} />
            <div style={{fontFamily: ANTON, fontSize: 96, color: 'white'}}>ILON MASK</div>
          </div>
          <svg width="760" height="230" style={{position: 'absolute', left: 0, top: 0}} viewBox="0 0 760 230"><line x1="40" y1="40" x2={40 + 680 * strike} y2={40 + 150 * strike} stroke={RED} strokeWidth="16" strokeLinecap="round" /><line x1="720" y1="40" x2={720 - 680 * strike} y2={40 + 150 * strike} stroke={RED} strokeWidth="16" strokeLinecap="round" /></svg>
        </div>
        <svg width="20" height="90" style={{opacity: nw}}><line x1="10" y1="0" x2="10" y2="90" stroke="white" strokeWidth="6" strokeDasharray="10 10" /></svg>
        <div style={{...box, borderColor: GREEN, transform: `scale(${nw})`, boxShadow: `0 0 50px ${GREEN}55`}}>
          <div style={{fontFamily: ANTON, fontSize: 84, color: GREEN}}>{label}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** "Founding != control" equation */
export const Control: React.FC = () => {
  const a = useSp(4);
  const b = useSp(20);
  const c = useSp(36, {damping: 9, stiffness: 220});
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{filter: 'brightness(0.35)'}}><Vid src="v/mk_49725.mp4" /></AbsoluteFill>
      <div style={{position: 'absolute', top: 480, left: 0, right: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 30}}>
        <div style={{opacity: a, transform: `translateX(${(1 - a) * -300}px)`}}><Label text="ASOS SOLISH" size={150} grad={GOLD_GRAD} /></div>
        <div style={{transform: `scale(${c})`}}><Label text="≠" size={260} color={RED} /></div>
        <div style={{opacity: b, transform: `translateX(${(1 - b) * 300}px)`}}><Label text="TO'LIQ NAZORAT" size={150} grad={ICE_GRAD} /></div>
      </div>
    </AbsoluteFill>
  );
};

/** Big glowing brand-like word (X.com etc.) - original typography, no logos */
export const WordMark: React.FC<{text: string; sub?: string; color?: string; bgVid?: string}> = ({text, sub, color = CYAN, bgVid}) => {
  const frame = useCurrentFrame();
  const s = useSp(0, {damping: 10, stiffness: 160});
  return (
    <AbsoluteFill>
      {bgVid ? <AbsoluteFill style={{filter: 'brightness(0.3) blur(4px)'}}><Vid src={bgVid} /></AbsoluteFill> : <BgDark hue={220} grid />}
      <AbsoluteFill style={{background: `radial-gradient(circle at 50% 45%, ${color}55 0%, rgba(0,0,0,0) ${30 + s * 25}%)`}} />
      <div style={{position: 'absolute', top: 700, left: 0, right: 0, transform: `scale(${0.6 + 0.4 * s})`, opacity: s}}>
        <div style={{fontFamily: ANTON, fontSize: 300, textAlign: 'center', letterSpacing: 6, color: 'white', textShadow: `0 0 ${40 + Math.sin(frame / 6) * 10}px ${color}, 0 8px 0 rgba(0,0,0,0.6)`}}>{text}</div>
        {sub && <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 50, color, textAlign: 'center', letterSpacing: 6, marginTop: 10}}>{sub}</div>}
      </div>
    </AbsoluteFill>
  );
};

/** Money transfer: $ coins flying between two phones */
export const Transfer: React.FC = () => {
  const frame = useCurrentFrame();
  const a = useSp(0);
  const phone = (x: number, label: string) => (
    <div style={{position: 'absolute', left: x, top: 720, width: 260, height: 480, borderRadius: 40, border: '8px solid white', background: '#0d1b2e', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', transform: `scale(${a})`}}>
      <div style={{fontFamily: ANTON, fontSize: 100, color: GREEN}}>$</div>
      <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 30, color: 'white'}}>{label}</div>
    </div>
  );
  return (
    <AbsoluteFill>
      <BgDark hue={150} />
      <div style={{position: 'absolute', top: 330, left: 0, right: 0}}><Label text={"PUL O'TKAZISH"} size={120} grad={GOLD_GRAD} /></div>
      {phone(90, 'YUBORUVCHI')}{phone(730, 'OLUVCHI')}
      {Array.from({length: 6}).map((_, i) => {
        const t = ((frame - 8 - i * 6) % 30) / 30;
        if (frame < 8 + i * 6) return null;
        const x = 350 + t * 380; const y = 940 - Math.sin(t * Math.PI) * 260;
        return <div key={i} style={{position: 'absolute', left: x, top: y, width: 70, height: 70, borderRadius: 35, background: GOLD, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: ANTON, fontSize: 46, color: '#5a3d00', opacity: interpolate(t, [0, 0.1, 0.9, 1], [0, 1, 1, 0]), boxShadow: `0 0 20px ${GOLD}`}}>$</div>;
      })}
    </AbsoluteFill>
  );
};

/** X.com + Confinity -> PayPal */
export const Merge: React.FC = () => {
  const frame = useCurrentFrame();
  const m = interpolate(frame, [10, 34], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const p = spring({frame: frame - 36, fps: FPS, config: {damping: 9, stiffness: 200}});
  const ball = (txt: string, dir: number, c: string) => (
    <div style={{position: 'absolute', top: 760, left: 540 - 190 + dir * (330 * (1 - m)), width: 380, height: 380, borderRadius: 190, background: `${c}33`, border: `6px solid ${c}`, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: 1 - p, fontFamily: ANTON, fontSize: 70, color: 'white', textShadow: sh}}>{txt}</div>
  );
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{filter: 'brightness(0.3) blur(3px)'}}><Vid src="v/mk_30013.mp4" /></AbsoluteFill>
      <div style={{position: 'absolute', top: 330, left: 0, right: 0}}><Label text="BIRLASHUV" size={130} color={YELLOW} /></div>
      {ball('X.com', -1, CYAN)}{ball('Confinity', 1, GREEN)}
      <div style={{position: 'absolute', top: 780, left: 0, right: 0, transform: `scale(${p})`}}><Label text="PayPal" size={240} grad={'linear-gradient(180deg,#ffffff,#8ecbff)'} /></div>
    </AbsoluteFill>
  );
};

/** Stake kept: donut */
export const Stake: React.FC = () => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [6, 40], [0, 1], {...clamp, easing: eo});
  const r = 230; const c = 2 * Math.PI * r;
  return (
    <AbsoluteFill>
      <BgDark hue={140} />
      <div style={{position: 'absolute', top: 300, left: 0, right: 0}}><Label text={'ULUSH\nSAQLANADI'} size={130} grad={GOLD_GRAD} /></div>
      <svg width="600" height="600" viewBox="-300 -300 600 600" style={{position: 'absolute', left: 240, top: 720}}>
        <circle r={r} fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="80" />
        <circle r={r} fill="none" stroke={GREEN} strokeWidth="80" strokeDasharray={`${c * 0.12 * p} ${c}`} transform="rotate(-90)" style={{filter: `drop-shadow(0 0 20px ${GREEN})`}} />
        <text y="30" textAnchor="middle" fontFamily="Anton" fontSize="110" fill="white">MASK</text>
      </svg>
      <div style={{position: 'absolute', top: 1380, left: 0, right: 0}}><Label text="KOMPANIYADA QOLADI" size={70} color="white" /></div>
    </AbsoluteFill>
  );
};

/** eBay buys PayPal for $1.5B */
export const Ebay: React.FC = () => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [4, 52], [0, 1.5], {...clamp, easing: Easing.bezier(0.2, 0.7, 0.2, 1)});
  const s = useSp(0);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{filter: 'brightness(0.3)'}}><Vid src="v/mk_45702.mp4" sf={2} /></AbsoluteFill>
      <div style={{position: 'absolute', top: 330, left: 0, right: 0, opacity: s}}><Label text={'eBay → PayPal'} size={130} color="white" /></div>
      <div style={{position: 'absolute', top: 700, left: 0, right: 0}}>
        <div style={{fontFamily: ANTON, fontSize: 260, textAlign: 'center', ...gradText('linear-gradient(180deg,#FFFFFF 0%,#B9FFCB 45%,#2EE66E 100%)', 'rgba(61,255,138,0.6)')}}>${p.toFixed(1)} MLRD</div>
        <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 52, color: YELLOW, textAlign: 'center', letterSpacing: 4}}>BIR YARIM MILLIARD DOLLAR</div>
      </div>
    </AbsoluteFill>
  );
};

/** Safe investments vs risky new fields split */
export const SafeRisky: React.FC<{base: number}> = ({base}) => {
  const frame = useCurrentFrame();
  const a = useSp(0);
  const b = useSp(at(336.62, base));
  const pick = at(342.3, base);
  const chosen = frame >= pick;
  const ps = spring({frame: frame - pick, fps: FPS, config: {damping: 10, stiffness: 200}});
  const half: React.CSSProperties = {position: 'absolute', left: 0, right: 0, height: 955, overflow: 'hidden'};
  return (
    <AbsoluteFill style={{background: '#05060a'}}>
      <div style={{...half, top: 0, transform: `translateX(${(1 - a) * -1080}px)`, filter: chosen ? 'grayscale(1) brightness(0.35)' : 'none'}}>
        <Vid src="v/mk_47012.mp4" filter="contrast(1.1) saturate(1.2)" />
        <div style={{position: 'absolute', top: 260, left: 0, right: 0}}><Label text="XAVFSIZ" size={150} color={GREEN} /></div>
        <div style={{position: 'absolute', top: 440, left: 0, right: 0}}><Label text="INVESTITSIYALAR" size={80} color="white" /></div>
      </div>
      <div style={{...half, top: 965, transform: `translateX(${(1 - b) * 1080}px) scale(${chosen ? 1 + 0.03 * ps : 1})`}}>
        <Vid src="v/mk_52304.mp4" filter="contrast(1.2) saturate(1.3)" />
        <div style={{position: 'absolute', top: 300, left: 0, right: 0}}><Label text="XAVFLI" size={150} color={RED} /></div>
        <div style={{position: 'absolute', top: 480, left: 0, right: 0}}><Label text="YANGI SOHALAR" size={80} color="white" /></div>
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 952, height: 16, background: 'white'}} />
      <div style={{position: 'absolute', left: 340, top: 880, width: 400, height: 160, borderRadius: 80, background: YELLOW, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: ANTON, fontSize: 90, color: '#111', transform: `scale(${chosen ? ps : 0})`, boxShadow: `0 0 50px ${YELLOW}`}}>2-YO'L ✓</div>
    </AbsoluteFill>
  );
};

/** Rocket vs software split with ≠ */
export const RocketVsCode: React.FC = () => {
  const a = useSp(0);
  const b = useSp(6);
  const n = useSp(26, {damping: 9, stiffness: 220});
  const half: React.CSSProperties = {position: 'absolute', left: 0, right: 0, height: 955, overflow: 'hidden'};
  return (
    <AbsoluteFill style={{background: '#05060a'}}>
      <div style={{...half, top: 0, transform: `translateY(${(1 - a) * -960}px)`}}><Vid src="v/n_c5_liftoff.mp4" sf={1} />
        <div style={{position: 'absolute', top: 230, left: 0, right: 0}}><Label text="RAKETA" size={150} grad={ICE_GRAD} /></div></div>
      <div style={{...half, top: 965, transform: `translateY(${(1 - b) * 960}px)`}}><Vid src="v/mk_46634.mp4" filter="brightness(0.8)" />
        <div style={{position: 'absolute', bottom: 260, left: 0, right: 0}}><Label text="INTERNET DASTUR" size={110} /></div></div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 952, height: 16, background: YELLOW}} />
      <div style={{position: 'absolute', left: 410, top: 830, width: 260, height: 260, borderRadius: 130, background: RED, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: ANTON, fontSize: 200, color: 'white', transform: `scale(${n})`, boxShadow: `0 0 60px ${RED}`}}>≠</div>
    </AbsoluteFill>
  );
};

/** Falcon 1 attempts scoreboard */
export const Attempts: React.FC<{win?: boolean; base: number}> = ({win, base}) => {
  const frame = useCurrentFrame();
  const years = ['2006', '2007', '2008', '2008'];
  return (
    <AbsoluteFill>
      {win ? <AbsoluteFill style={{filter: 'brightness(0.4)'}}><Img src={staticFile('img/falcon1.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 40%', transform: `scale(${1.1 + frame * 0.001})`}} /></AbsoluteFill>
        : <AbsoluteFill style={{filter: 'brightness(0.45) saturate(1.2)'}}><Vid src="v/mk_48305.mp4" /></AbsoluteFill>}
      <div style={{position: 'absolute', top: 300, left: 0, right: 0}}><Label text={win ? "4-URINISH" : 'FALCON 1'} size={140} grad={win ? GOLD_GRAD : undefined} /></div>
      <div style={{position: 'absolute', top: 640, left: 70, right: 70, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 40}}>
        {years.map((y, i) => {
          const isWin = i === 3;
          if (isWin && !win) return <div key={i} style={{height: 330, borderRadius: 30, border: '5px dashed rgba(255,255,255,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: ANTON, fontSize: 160, color: 'rgba(255,255,255,0.3)'}}>?</div>;
          const appear = win ? (isWin ? at(374.4, base) : 0) : i * 24;
          const s = spring({frame: frame - appear, fps: FPS, config: {damping: 9, stiffness: 240}});
          const c = isWin ? GREEN : RED;
          return (
            <div key={i} style={{height: 330, borderRadius: 30, background: `${c}22`, border: `6px solid ${c}`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', transform: `scale(${win && !isWin ? 0.92 : s})`, opacity: win && !isWin ? 0.55 : 1, boxShadow: isWin ? `0 0 70px ${GREEN}` : 'none'}}>
              <div style={{fontFamily: ANTON, fontSize: 170, color: c, lineHeight: 1}}>{isWin ? '✓' : '✕'}</div>
              <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 46, color: 'white'}}>{i + 1}-URINISH · {y}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/** Tesla founders cards */
export const Founders: React.FC<{base: number}> = ({base}) => {
  const frame = useCurrentFrame();
  const a = useSp(at(392.26, base));
  const b = useSp(at(394.42, base));
  const t = useSp(0);
  const card = (s: number, name: string, img: string | null, dir: number) => (
    <div style={{width: 440, borderRadius: 30, overflow: 'hidden', background: 'rgba(255,255,255,0.08)', border: '4px solid rgba(255,255,255,0.5)', transform: `translateY(${(1 - s) * 400 * dir}px)`, opacity: s}}>
      <div style={{height: 520, background: '#1b2533', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        {img ? <Img src={staticFile(img)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 25%'}} />
          : <svg width="240" height="240" viewBox="0 0 24 24" fill="rgba(255,255,255,0.35)"><circle cx="12" cy="8" r="4.5" /><path d="M3 22c0-5 4-8 9-8s9 3 9 8z" /></svg>}
      </div>
      <div style={{padding: '22px 10px', fontFamily: ANTON, fontSize: 58, color: 'white', textAlign: 'center', lineHeight: 1.05}}>{name}</div>
    </div>
  );
  return (
    <AbsoluteFill>
      <BgDark hue={0} />
      <div style={{position: 'absolute', top: 250, left: 0, right: 0, opacity: t}}><Label text="TESLA ASOSCHILARI" size={100} color={RED} /></div>
      <div style={{position: 'absolute', top: 420, left: 0, right: 0}}><Label text="2003" size={120} grad={GOLD_GRAD} /></div>
      <div style={{position: 'absolute', top: 640, left: 0, right: 0, display: 'flex', justifyContent: 'center', gap: 50}}>
        {card(a, 'MARTIN\nEBERHARD', 'img/eberhard.jpg', 1)}
        {card(b, 'MARK\nTARPENNING', null, -1)}
      </div>
    </AbsoluteFill>
  );
};

/** SpaceX | Tesla split */
export const SplitSxTesla: React.FC = () => {
  const a = useSp(0);
  const b = useSp(at(414.0, 411.88));
  const half: React.CSSProperties = {position: 'absolute', left: 0, right: 0, height: 955, overflow: 'hidden'};
  return (
    <AbsoluteFill style={{background: '#05060a'}}>
      <div style={{...half, top: 0, transform: `translateX(${(1 - a) * -1080}px)`}}><Vid src="v/n_fh_ignite.mp4" sf={1} />
        <div style={{position: 'absolute', top: 230, left: 0, right: 0}}><Label text="SPACEX" size={170} grad={ICE_GRAD} /></div></div>
      <div style={{...half, top: 965, transform: `translateX(${(1 - b) * 1080}px)`}}>
        <Img src={staticFile('img/tesla_factory.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '60% 60%'}} />
        <div style={{position: 'absolute', bottom: 260, left: 0, right: 0}}><Label text="TESLA" size={170} color={RED} /></div></div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 952, height: 16, background: 'white'}} />
    </AbsoluteFill>
  );
};

/** Animated career timeline 1995 Zip2 -> 1999 X.com -> 2002 SpaceX -> 2004 Tesla */
export const CareerTimeline: React.FC<{base: number}> = ({base}) => {
  const frame = useCurrentFrame();
  const items: [string, string, number, string][] = [['1995', 'ZIP2 · internet xaritalar', 455.4, CYAN], ['1999', 'X.com → PayPal', 457.6, '#8ecbff'], ['2002', 'SPACEX · raketalar', 459.5, 'white'], ['2004', 'TESLA · elektromobillar', 460.3, RED]];
  const line = interpolate(frame, [6, at(461.0, base)], [0, 1], {...clamp, easing: eo});
  return (
    <AbsoluteFill>
      <BgDark hue={230} grid />
      <div style={{position: 'absolute', top: 230, left: 0, right: 0}}><Label text="1995 → BUGUN" size={110} grad={GOLD_GRAD} /></div>
      <div style={{position: 'absolute', left: 170, top: 470, width: 8, height: 1120 * line, background: `linear-gradient(180deg, ${CYAN}, ${RED})`, borderRadius: 4}} />
      {items.map(([y, t, s, c], i) => {
        const p = spring({frame: frame - at(s, base), fps: FPS, config: {damping: 12, stiffness: 200}});
        return (
          <div key={i} style={{position: 'absolute', left: 130, top: 470 + i * 280, display: 'flex', alignItems: 'center', gap: 40, opacity: p, transform: `translateX(${(1 - p) * 120}px)`}}>
            <div style={{width: 88, height: 88, borderRadius: 44, background: c, boxShadow: `0 0 30px ${c}`, border: '6px solid #0b0f18'}} />
            <div>
              <div style={{fontFamily: ANTON, fontSize: 110, color: c, lineHeight: 1}}>{y}</div>
              <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 48, color: 'white'}}>{t}</div>
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

/** Recap: small office, one computer, big risk (B&W callbacks) */
export const Recap: React.FC<{base: number}> = ({base}) => {
  const frame = useCurrentFrame();
  const words: [string, number, string][] = [['KICHKINA OFIS', 465.9, 'v/mk_3112.mp4'], ['BITTA KOMPYUTER', 467.38, 'v/mk_41656.mp4'], ['KATTA TAVAKKAL', 468.5, 'v/mk_49906.mp4']];
  const idx = words.reduce((acc, w, i) => (frame >= at(w[1], base) ? i : acc), 0);
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <AbsoluteFill style={{filter: 'grayscale(1) contrast(1.3) brightness(0.55)'}}><Vid src={words[idx][2]} sf={2} /></AbsoluteFill>
      <Scanlines opacity={0.2} />
      <div style={{position: 'absolute', top: 560, left: 0, right: 0}}>
        {words.map(([w, s], i) => {
          const p = spring({frame: frame - at(s, base), fps: FPS, config: {damping: 11, stiffness: 220}});
          return <div key={i} style={{opacity: frame >= at(s, base) ? 1 : 0, transform: `scale(${0.6 + 0.4 * p})`, marginBottom: 40}}><Label text={w} size={130} color={i === idx ? YELLOW : 'white'} /></div>;
        })}
      </div>
    </AbsoluteFill>
  );
};

export const Question: React.FC = () => {
  const s = useSp(0, {damping: 8, stiffness: 200});
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <BgDark hue={45} />
      <div style={{position: 'absolute', top: 560, left: 0, right: 0, transform: `scale(${s}) rotate(${Math.sin(frame / 10) * 3}deg)`}}><Label text="?" size={600} grad={GOLD_GRAD} /></div>
      <div style={{position: 'absolute', top: 1260, left: 0, right: 0, opacity: s}}><Label text="SIZGA SAVOL" size={120} color="white" /></div>
    </AbsoluteFill>
  );
};

/** Final choice split: university vs business */
export const FinalSplit: React.FC<{base: number}> = ({base}) => {
  const frame = useCurrentFrame();
  const a = useSp(0);
  const b = useSp(6);
  const cues: [number, 'u' | 'b' | 'both'][] = [[471.34, 'both'], [473.66, 'u'], [476.78, 'b'], [479.12, 'both'], [481.22, 'u'], [483.34, 'b']];
  const state = cues.reduce((acc, c) => (frame >= at(c[0], base) ? c[1] : acc), 'both' as string);
  const half: React.CSSProperties = {position: 'absolute', left: 0, right: 0, height: 955, overflow: 'hidden'};
  const dim = (on: boolean) => (on ? 'none' : 'grayscale(0.8) brightness(0.45)');
  const lab = (on: boolean, c: string): React.CSSProperties => ({transform: `scale(${on ? 1.1 : 0.9})`, color: on ? c : 'white', textShadow: on ? `0 0 50px ${c}, ${sh}` : sh});
  const age = useSp(at(471.34, base) + 8);
  return (
    <AbsoluteFill style={{background: '#05060a'}}>
      <div style={{...half, top: 0, transform: `translateY(${(1 - a) * -960}px)`, filter: dim(state !== 'b')}}>
        <Img src={staticFile('img/hoover.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 35%', transform: `scale(${1.1 + frame * 0.0006})`}} />
        <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0) 50%)'}} />
        <div style={{position: 'absolute', top: 250, left: 0, right: 0}}><Label text="UNIVERSITET" size={140} style={lab(state === 'u', YELLOW)} /></div>
        <div style={{position: 'absolute', top: 420, left: 0, right: 0}}><Label text="Nufuzli · ishonchli" size={56} color="white" style={{fontFamily: MONT, fontWeight: 900}} /></div>
      </div>
      <div style={{...half, top: 965, transform: `translateY(${(1 - b) * 960}px)`, filter: dim(state !== 'u')}}>
        <OffthreadVideo src={staticFile('v/mk_23043.mp4')} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
        <AbsoluteFill style={{background: 'linear-gradient(0deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0) 50%)'}} />
        <div style={{position: 'absolute', bottom: 380, left: 0, right: 0}}><Label text="BIZNES" size={160} style={lab(state === 'b', GREEN)} /></div>
        <div style={{position: 'absolute', bottom: 300, left: 0, right: 0}}><Label text="Kelajagi noma'lum · tavakkal" size={52} color="white" style={{fontFamily: MONT, fontWeight: 900}} /></div>
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 952, height: 16, background: 'white', boxShadow: '0 0 30px white'}} />
      <div style={{position: 'absolute', left: 400, top: 860, width: 280, height: 200, borderRadius: 100, background: YELLOW, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', transform: `scale(${age})`, boxShadow: `0 0 40px ${YELLOW}`}}>
        <div style={{fontFamily: ANTON, fontSize: 96, color: '#111', lineHeight: 1}}>24</div>
        <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 30, color: '#111'}}>YOSHDA</div>
      </div>
    </AbsoluteFill>
  );
};

/** Comment CTA */
export const Comment: React.FC = () => {
  const frame = useCurrentFrame();
  const s = useSp(0, {damping: 11, stiffness: 180});
  const text = 'Men tanlagan bo‘lardim...';
  const typed = text.slice(0, Math.floor(interpolate(frame, [8, 34], [0, text.length], clamp)));
  return (
    <AbsoluteFill>
      <BgDark hue={45} />
      <div style={{position: 'absolute', top: 360, left: 0, right: 0}}><Label text={'JAVOBINGIZNI\nIZOHLARDA\nYOZING'} size={130} grad={GOLD_GRAD} /></div>
      <div style={{position: 'absolute', top: 1000, left: 90, right: 90, borderRadius: 40, background: 'white', padding: '40px 44px', transform: `scale(${s})`, boxShadow: '0 20px 60px rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', gap: 26}}>
        <svg width="80" height="80" viewBox="0 0 24 24"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1.1-4.6A8 8 0 1 1 21 12z" fill="#111" /></svg>
        <div style={{fontFamily: MONT, fontWeight: 800, fontSize: 52, color: '#111'}}>{typed}<span style={{opacity: frame % 16 < 8 ? 1 : 0}}>|</span></div>
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ overlays
export const AgeBadge: React.FC<{n: number; y: number}> = ({n, y}) => {
  const frame = useCurrentFrame();
  const v = Math.round(interpolate(frame, [0, 20], [0, n], {...clamp, easing: eo}));
  const s = useSp(0, {damping: 10, stiffness: 200});
  return (
    <AbsoluteFill style={{top: y, height: 'auto', alignItems: 'center'}}>
      <div style={{display: 'flex', alignItems: 'baseline', gap: 20, transform: `scale(${s})`, background: 'rgba(0,0,0,0.55)', padding: '10px 50px', borderRadius: 30, border: `5px solid ${YELLOW}`}}>
        <div style={{fontFamily: ANTON, fontSize: 220, color: YELLOW, lineHeight: 1, fontVariantNumeric: 'tabular-nums'}}>{v}</div>
        <div style={{fontFamily: ANTON, fontSize: 110, color: 'white'}}>YOSH</div>
      </div>
    </AbsoluteFill>
  );
};

export const BigCount: React.FC<{to: number; prefix: string; suffix: string; y: number; label?: string; dur?: number; textOnly?: string}> = ({to, prefix, suffix, y, label, dur = 1.1, textOnly}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, Math.round(dur * FPS)], [0, 1], {...clamp, easing: Easing.bezier(0.2, 0.7, 0.2, 1)});
  const v = Math.round(to * p);
  const str = textOnly && p >= 1 ? textOnly : prefix + v.toLocaleString('en-US').replace(/,/g, ' ') + suffix;
  const pop = spring({frame: frame - Math.round(dur * FPS), fps: FPS, config: {damping: 8, stiffness: 300}});
  return (
    <AbsoluteFill style={{top: y, height: 'auto', alignItems: 'center'}}>
      {label && <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 44, color: YELLOW, letterSpacing: 3, textShadow: sh, marginBottom: 6}}>{label}</div>}
      <div style={{fontFamily: ANTON, fontSize: str.length > 12 ? 140 : 190, fontVariantNumeric: 'tabular-nums', transform: `scale(${1 + 0.1 * (1 - pop) * (p >= 1 ? 1 : 0)})`, ...gradText('linear-gradient(180deg,#FFFFFF 0%,#B9FFCB 45%,#2EE66E 100%)', 'rgba(61,255,138,0.55)')}}>{str}</div>
    </AbsoluteFill>
  );
};

export const List3: React.FC<{items: [string, number][]; y: number; base: number}> = ({items, y, base}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{top: y, height: 'auto', alignItems: 'center'}}>
      {items.map(([t, s], i) => {
        const p = spring({frame: frame - at(s, base), fps: FPS, config: {damping: 13, stiffness: 200}});
        const active = frame >= at(s, base) && (i === items.length - 1 || frame < at(items[i + 1][1], base));
        return <div key={i} style={{fontFamily: MONT, fontWeight: 900, fontSize: active ? 64 : 52, color: active ? '#111' : 'white', background: active ? YELLOW : 'rgba(0,0,0,0.55)', padding: '10px 30px', borderRadius: 16, marginBottom: 18, opacity: p, transform: `translateX(${(1 - p) * -300}px)`}}>{i + 1}. {t}</div>;
      })}
    </AbsoluteFill>
  );
};

export const Quote: React.FC<{text: string; by: string; y: number}> = ({text, by, y}) => {
  const s = useSp(0);
  return (
    <AbsoluteFill style={{top: y, height: 'auto', alignItems: 'center', paddingLeft: 80, paddingRight: 80}}>
      <div style={{background: 'rgba(0,0,0,0.6)', borderLeft: `12px solid ${YELLOW}`, padding: '30px 40px', borderRadius: 20, transform: `translateY(${(1 - s) * 60}px)`, opacity: s}}>
        <div style={{fontFamily: ANTON, fontSize: 100, color: 'white', lineHeight: 1.05}}>{text}</div>
        <div style={{fontFamily: MONT, fontWeight: 800, fontSize: 36, color: YELLOW, marginTop: 12}}>— {by}</div>
      </div>
    </AbsoluteFill>
  );
};

export const Growth: React.FC<{y: number}> = ({y}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, 40], [0, 1], {...clamp, easing: eo});
  const pts = [[0, 300], [150, 260], [300, 270], [450, 180], [600, 140], [750, 40]];
  const d = pts.map((q, i) => `${i ? 'L' : 'M'}${q[0]} ${q[1]}`).join(' ');
  return (
    <AbsoluteFill style={{top: y, height: 'auto', alignItems: 'center'}}>
      <svg width="800" height="340" viewBox="-20 0 800 340" style={{filter: `drop-shadow(0 0 16px ${GREEN})`}}>
        <path d={d} stroke={GREEN} strokeWidth="14" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="1200" strokeDashoffset={1200 * (1 - p)} />
        <polygon points="750,40 700,60 735,90" fill={GREEN} opacity={p > 0.95 ? 1 : 0} />
      </svg>
    </AbsoluteFill>
  );
};

export const Drain: React.FC<{y: number}> = ({y}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, 45], [1, 0.12], {...clamp, easing: eo});
  return (
    <AbsoluteFill style={{top: y, height: 'auto', alignItems: 'center'}}>
      <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 52, color: 'white', marginBottom: 16, textShadow: sh}}>KOMPANIYA MABLAG‘I</div>
      <div style={{width: 860, height: 90, borderRadius: 45, border: '6px solid white', overflow: 'hidden', background: 'rgba(0,0,0,0.5)'}}>
        <div style={{width: `${p * 100}%`, height: '100%', background: p < 0.35 ? RED : p < 0.6 ? GOLD : GREEN}} />
      </div>
    </AbsoluteFill>
  );
};
