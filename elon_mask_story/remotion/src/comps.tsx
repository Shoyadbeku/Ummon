import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, OffthreadVideo, random, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {ANTON, CYAN, FPS, GOLD, GREEN, H, MONT, RED, RetroBrowser, Scanlines, W, YELLOW} from './fx';

// 16:9 (1920x1080) motion-graphics scenes.
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const eo = Easing.bezier(0.16, 1, 0.3, 1);
const sh = '0 5px 0 rgba(0,0,0,0.55), 0 0 36px rgba(0,0,0,0.6)';
const GOLD_GRAD = 'linear-gradient(180deg,#FFF6C8 0%,#FFD23F 45%,#E89B0C 100%)';
const ICE_GRAD = 'linear-gradient(180deg,#FFFFFF 0%,#BFF4FF 50%,#4FE3FF 100%)';
const gradText = (g: string, glow = 'rgba(255,200,60,0.6)'): React.CSSProperties => ({backgroundImage: g, WebkitBackgroundClip: 'text', backgroundClip: 'text', WebkitTextFillColor: 'transparent', filter: `drop-shadow(0 5px 0 rgba(0,0,0,0.6)) drop-shadow(0 0 26px ${glow})`});
const useSp = (delay = 0, cfg: any = {damping: 14, stiffness: 170}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - delay, fps, config: cfg});
};
const at = (sec: number, base: number) => Math.round((sec - base) * FPS);
const HALF_W = 955; // left/right split panels with a 10px divider

/** Dark animated backdrop with drifting particles. */
export const BgDark: React.FC<{hue?: number; grid?: boolean}> = ({hue = 210, grid}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{background: `radial-gradient(ellipse at 50% 40%, hsl(${hue},45%,16%) 0%, hsl(${hue},40%,6%) 60%, #030407 100%)`}}>
      {grid && <AbsoluteFill style={{backgroundImage: 'linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)', backgroundSize: '80px 80px', backgroundPosition: `${frame * 0.5}px 0`}} />}
      <svg width={W} height={H} style={{position: 'absolute'}}>
        {Array.from({length: 60}).map((_, i) => {
          const x = random(`px${i}`) * W;
          const y = (random(`py${i}`) * H - frame * (0.3 + random(`ps${i}`)) + H * 6) % H;
          return <circle key={i} cx={x} cy={y} r={1 + random(`pr${i}`) * 2.4} fill="white" opacity={0.15 + random(`po${i}`) * 0.35} />;
        })}
      </svg>
    </AbsoluteFill>
  );
};

const Vid: React.FC<{src: string; sf?: number; style?: React.CSSProperties; filter?: string; pos?: string}> = ({src, sf = 0, style, filter, pos = 'center'}) => (
  <OffthreadVideo src={staticFile(src)} startFrom={Math.round(sf * FPS)} muted style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: pos, filter, ...style}} />
);

const Label: React.FC<{text: string; color?: string; size?: number; style?: React.CSSProperties; grad?: string; align?: 'center' | 'left'}> = ({text, color = 'white', size = 100, style, grad, align = 'center'}) => (
  <div style={{fontFamily: ANTON, fontSize: size, color, letterSpacing: 3, textShadow: grad ? undefined : sh, lineHeight: 1.02, textAlign: align, whiteSpace: 'pre-line', ...(grad ? gradText(grad) : {}), ...style}}>{text}</div>
);

/** Left/right split panel helper */
const Half: React.FC<{side: 'l' | 'r'; s: number; filter?: string; children: React.ReactNode}> = ({side, s, filter, children}) => (
  <div style={{position: 'absolute', top: 0, bottom: 0, width: HALF_W, [side === 'l' ? 'left' : 'right']: 0, overflow: 'hidden', transform: `translateY(${(1 - s) * (side === 'l' ? -1 : 1) * H}px)`, filter}}>{children}</div>
);
const Divider: React.FC<{color?: string; s?: number}> = ({color = 'white', s = 1}) => (
  <div style={{position: 'absolute', left: HALF_W, top: 0, bottom: 0, width: 10, background: color, boxShadow: `0 0 30px ${color}`, transform: `scaleY(${s})`}} />
);
const CenterBadge: React.FC<{s: number; size?: number; bg: string; children: React.ReactNode; w?: number; h?: number}> = ({s, bg, children, w = 220, h = 220}) => (
  <div style={{position: 'absolute', left: W / 2 - w / 2, top: H / 2 - h / 2, width: w, height: h, borderRadius: Math.min(w, h) / 2, background: bg, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', transform: `scale(${s})`, boxShadow: `0 0 50px ${bg}`}}>{children}</div>
);

// ------------------------------------------------------------------ scenes
export const Brothers: React.FC<{variant?: 1 | 2}> = ({variant = 1}) => {
  const frame = useCurrentFrame();
  const a = useSp(0);
  const b = useSp(6);
  const n = useSp(14);
  const CW = variant === 1 ? 520 : 600;
  const L1 = variant === 1 ? 760 : 300; const R1 = variant === 1 ? 100 : 300;
  const card = (src: string, pos: string, s: number, dir: number, zoom: number): React.CSSProperties => ({position: 'absolute', top: variant === 1 ? 90 : 120, width: CW, height: variant === 1 ? 760 : 700, borderRadius: 28, overflow: 'hidden', boxShadow: '0 30px 80px rgba(0,0,0,0.6)', transform: `translateX(${(1 - s) * dir * 900}px) rotate(${(1 - s) * dir * 6}deg)`, border: '6px solid rgba(255,255,255,0.85)'});
  const filt = variant === 1 ? 'sepia(0.35) contrast(1.1)' : 'contrast(1.1)';
  return (
    <AbsoluteFill>
      <BgDark hue={variant === 1 ? 35 : 210} />
      <div style={{...card('', '', a, -1, 0), left: L1}}><Img src={staticFile('img/musk_young.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 20%', transform: `scale(${1.12 - frame * 0.0012})`, filter: filt}} /></div>
      <div style={{...card('', '', b, 1, 0), right: R1}}><Img src={staticFile('img/kimbal.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '45% 22%', transform: `scale(${1.08 + frame * 0.0012})`, filter: filt}} /></div>
      <div style={{position: 'absolute', top: variant === 1 ? 870 : 840, left: L1, width: CW, opacity: n}}><Label text={variant === 1 ? 'ILON' : 'ILON MASK'} size={80} color={YELLOW} /></div>
      <div style={{position: 'absolute', top: variant === 1 ? 870 : 840, right: R1, width: CW, opacity: n}}><Label text={variant === 1 ? 'KIMBAL' : 'KIMBAL MASK'} size={80} color={GREEN} /></div>
      {variant === 2 && <div style={{position: 'absolute', top: 470, left: 0, right: 0, opacity: n, transform: `scale(${n})`}}><Label text="AKA-UKA" size={70} color="white" style={{background: 'rgba(0,0,0,0.55)', display: 'inline-block', padding: '6px 30px', borderRadius: 16}} /></div>}
    </AbsoluteFill>
  );
};

export const NoApps: React.FC<{base: number}> = ({base}) => {
  const frame = useCurrentFrame();
  const items: [string, number][] = [['SMARTFONLAR', 53.34], ['IJTIMOIY TARMOQLAR', 55.14], ['GOOGLE XARITALARI', 56.32]];
  const yo = useSp(at(57.4, base), {damping: 9, stiffness: 260});
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{filter: 'blur(6px) brightness(0.35)', transform: 'scale(1.1)'}}><Vid src="v/mk_8766.mp4" /></AbsoluteFill>
      <div style={{position: 'absolute', top: 230, left: 200, width: 1000}}>
        {items.map(([t, s], i) => {
          const local = at(s, base);
          const p = spring({frame: frame - local, fps: FPS, config: {damping: 14}});
          const strike = interpolate(frame, [local + 12, local + 22], [0, 1], {...clamp, easing: eo});
          return (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 30, marginBottom: 60, opacity: p, transform: `translateX(${(1 - p) * -200}px)`}}>
              <div style={{width: 120, height: 120, borderRadius: 28, background: 'rgba(255,255,255,0.12)', border: '3px solid rgba(255,255,255,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
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
      <div style={{position: 'absolute', top: 330, right: 160, transform: `scale(${interpolate(yo, [0, 1], [2.5, 1])}) rotate(-8deg)`, opacity: Math.min(1, yo * 2)}}>
        <Label text="YO'Q" size={300} color={RED} style={{textShadow: `0 0 60px ${RED}, ${sh}`}} />
      </div>
    </AbsoluteFill>
  );
};

export const NameMorph: React.FC<{base: number}> = ({base}) => {
  const frame = useCurrentFrame();
  const full = 'GLOBAL LINK INFORMATION NETWORK';
  const typed = full.slice(0, Math.floor(interpolate(frame, [at(98.4, base), at(100.4, base)], [0, full.length], clamp)));
  const swap = at(100.7, base);
  const out = interpolate(frame, [swap, swap + 8], [1, 0], clamp);
  const z = spring({frame: frame - swap - 4, fps: FPS, config: {damping: 9, stiffness: 200}});
  const intro = useSp(0);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{filter: 'brightness(0.45) saturate(1.3)'}}><Vid src="v/mk_31771.mp4" /></AbsoluteFill>
      <div style={{position: 'absolute', top: 200, left: 0, right: 0, opacity: intro * out}}><Label text="DASTLABKI NOMI" size={64} color={CYAN} /></div>
      <div style={{position: 'absolute', top: 440, left: 80, right: 80, opacity: out, transform: `scale(${1 - (1 - out) * 0.3})`, filter: `blur(${(1 - out) * 20}px)`}}>
        <div style={{fontFamily: 'monospace', fontWeight: 700, fontSize: 84, color: 'white', textAlign: 'center', textShadow: '0 0 20px rgba(79,227,255,0.7)'}}>{typed}<span style={{opacity: frame % 16 < 8 ? 1 : 0}}>_</span></div>
      </div>
      {frame >= swap && (
        <div style={{position: 'absolute', top: 220, left: 0, right: 0, transform: `scale(${z})`}}>
          <div style={{fontFamily: ANTON, fontSize: 380, textAlign: 'center', lineHeight: 1.05, ...gradText('linear-gradient(180deg,#ffffff,#9fdcff)', 'rgba(79,227,255,0.9)')}}>Zip2</div>
          <Label text="KEYINCHALIK" size={64} color={YELLOW} />
        </div>
      )}
    </AbsoluteFill>
  );
};

export const CityMap: React.FC = () => {
  const frame = useCurrentFrame();
  const pins: [number, number, string, string][] = [[420, 380, '#FF5A5F', 'R'], [760, 300, '#4FE3FF', 'D'], [1040, 520, '#3DFF8A', 'K'], [1380, 330, '#FF5A5F', 'R'], [1560, 640, '#FFD23F', 'M'], [620, 700, '#4FE3FF', 'D'], [1220, 800, '#3DFF8A', 'K'], [300, 860, '#FF5A5F', 'R']];
  const cam = interpolate(frame, [0, 90], [1.25, 1.0], {...clamp, easing: eo});
  return (
    <AbsoluteFill style={{background: '#0b1626'}}>
      <AbsoluteFill style={{transform: `scale(${cam}) rotate(${-3 + frame * 0.02}deg)`}}>
        <svg width={W} height={H}>
          {Array.from({length: 9}).map((_, i) => <rect key={`h${i}`} x={-100} y={i * 140 + 30} width={2200} height={i % 3 === 0 ? 24 : 11} fill={i % 3 === 0 ? '#2b4a6f' : '#1b2f48'} />)}
          {Array.from({length: 15}).map((_, i) => <rect key={`v${i}`} x={i * 140 + 20} y={-100} width={i % 4 === 0 ? 24 : 11} height={1400} fill={i % 4 === 0 ? '#2b4a6f' : '#1b2f48'} />)}
          <path d="M-50 1000 C 500 800, 900 950, 2000 600" stroke="#1f6fb2" strokeWidth="55" fill="none" opacity="0.6" />
          {Array.from({length: 60}).map((_, i) => <rect key={`b${i}`} x={Math.floor(random(`bx${i}`) * 14) * 140 + 45} y={Math.floor(random(`by${i}`) * 8) * 140 + 52} width={88} height={100} rx={8} fill="#15263b" />)}
        </svg>
      </AbsoluteFill>
      {pins.map(([x, y, c, l], i) => {
        const s = spring({frame: frame - 6 - i * 5, fps: FPS, config: {damping: 8, stiffness: 220}});
        return (
          <div key={i} style={{position: 'absolute', left: x - 40, top: y - 100, width: 80, height: 100, transform: `scale(${s})`, transformOrigin: '50% 100%'}}>
            <svg width="80" height="100" viewBox="0 0 24 30"><path d="M12 29s10-9 10-17A10 10 0 0 0 2 12c0 8 10 17 10 17z" fill={c} stroke="white" strokeWidth="1.2" /><text x="12" y="15.5" textAnchor="middle" fontFamily="Montserrat" fontWeight="900" fontSize="9" fill="#0b1626">{l}</text></svg>
          </div>
        );
      })}
      <div style={{position: 'absolute', top: 60, left: 0, right: 0}}><Label text="INTERNET XARITASI" size={96} grad={ICE_GRAD} /></div>
      <div style={{position: 'absolute', bottom: 50, left: 0, right: 0, display: 'flex', justifyContent: 'center', gap: 40, fontFamily: MONT, fontWeight: 900, fontSize: 34, color: 'white'}}>
        {[['#FF5A5F', 'RESTORAN'], ['#4FE3FF', "DO'KON"], ['#3DFF8A', 'KORXONA']].map(([c, t]) => <span key={t} style={{display: 'flex', alignItems: 'center', gap: 10, background: 'rgba(0,0,0,0.5)', padding: '6px 18px', borderRadius: 30}}><span style={{width: 24, height: 24, borderRadius: 12, background: c}} />{t}</span>)}
      </div>
    </AbsoluteFill>
  );
};

export const Needs: React.FC<{base: number}> = ({base}) => {
  const frame = useCurrentFrame();
  const items: [string, number][] = [['DASTURCHILAR', 135.92], ['KOMPYUTERLAR', 136.8], ['INTERNET ALOQASI', 137.84], ['MIJOZLAR', 139.0]];
  const bg = frame < at(137.84, base) ? 'v/mk_41639.mp4' : 'v/mk_23216.mp4';
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{filter: 'brightness(0.35) blur(3px)', transform: 'scale(1.08)'}}><Vid src={bg} /></AbsoluteFill>
      <div style={{position: 'absolute', top: 110, left: 0, right: 0}}><Label text="KERAK EDI:" size={100} color={YELLOW} /></div>
      <div style={{position: 'absolute', top: 330, left: 260, right: 260, display: 'grid', gridTemplateColumns: '1fr 1fr', rowGap: 90, columnGap: 60}}>
        {items.map(([t, s], i) => {
          const p = spring({frame: frame - at(s, base), fps: FPS, config: {damping: 12, stiffness: 200}});
          return (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 28, opacity: p, transform: `translateY(${(1 - p) * 60}px)`}}>
              <div style={{width: 92, height: 92, borderRadius: 22, background: GREEN, display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${p})`, boxShadow: `0 0 30px ${GREEN}88`, flexShrink: 0}}>
                <svg width="58" height="58" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7" stroke="#0a0a0a" strokeWidth="3.4" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
              </div>
              <div style={{fontFamily: ANTON, fontSize: 76, color: 'white', letterSpacing: 2, textShadow: sh}}>{t}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const DayNight: React.FC<{base: number}> = ({base}) => {
  const frame = useCurrentFrame();
  const a = useSp(0);
  const b = useSp(4);
  const nightAt = at(164.82, base);
  const lit = interpolate(frame, [nightAt - 2, nightAt + 6], [0, 1], clamp);
  return (
    <AbsoluteFill style={{background: '#05060a'}}>
      <Half side="l" s={a} filter={frame >= nightAt ? 'brightness(0.5)' : 'none'}>
        <Vid src="v/mk_13906.mp4" filter="contrast(1.1) saturate(1.2) sepia(0.2) brightness(1.05)" />
        <div style={{position: 'absolute', top: 80, left: 0, right: 0}}><Label text={'☀ KUNDUZI'} size={76} color={YELLOW} /></div>
        <div style={{position: 'absolute', bottom: 90, left: 0, right: 0}}><Label text="VEB-SAYT" size={110} /></div>
      </Half>
      <Half side="r" s={b} filter={`brightness(${0.35 + 0.65 * lit}) grayscale(${1 - lit})`}>
        <Vid src="v/mk_9757.mp4" filter="contrast(1.2) saturate(1.1) hue-rotate(-15deg) brightness(0.8)" />
        <div style={{position: 'absolute', top: 80, left: 0, right: 0}}><Label text={'☾ KECHASI'} size={76} color={CYAN} /></div>
        <div style={{position: 'absolute', bottom: 90, left: 0, right: 0}}><Label text="DASTUR YOZISH" size={110} /></div>
      </Half>
      <Divider />
      <CenterBadge s={a} bg="#111" w={240} h={150}><div style={{fontFamily: ANTON, fontSize: 64, color: 'white'}}>1 PC</div></CenterBadge>
    </AbsoluteFill>
  );
};

export const InternetChart: React.FC = () => {
  const frame = useCurrentFrame();
  const data: [string, number][] = [['1995', 16], ['1996', 36], ['1997', 70], ['1998', 147], ['1999', 248]];
  const max = 260;
  return (
    <AbsoluteFill>
      <BgDark hue={200} grid />
      <div style={{position: 'absolute', top: 150, left: 140, width: 620}}>
        <Label text={'INTERNET\nTEZ\nO‘SMOQDA'} size={130} grad={ICE_GRAD} align="left" />
        <div style={{fontFamily: MONT, fontWeight: 800, fontSize: 34, color: 'rgba(255,255,255,0.75)', marginTop: 30}}>Dunyo bo‘yicha internet<br />foydalanuvchilari, mln</div>
        <div style={{fontFamily: MONT, fontWeight: 700, fontSize: 22, color: 'rgba(255,255,255,0.45)', marginTop: 40}}>Manba: Internet World Stats</div>
      </div>
      <div style={{position: 'absolute', left: 860, right: 140, top: 160, height: 760, display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', borderBottom: '4px solid rgba(255,255,255,0.6)'}}>
        {data.map(([y, v], i) => {
          const p = interpolate(frame, [4 + i * 9, 24 + i * 9], [0, 1], {...clamp, easing: eo});
          const h = (v / max) * 680 * p;
          const last = i === data.length - 1;
          return (
            <div key={y} style={{width: 150, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-end', height: '100%', position: 'relative'}}>
              <div style={{fontFamily: ANTON, fontSize: 56, color: last ? GREEN : 'white', opacity: p, marginBottom: 10}}>{Math.round(v * p)}</div>
              <div style={{width: '100%', height: h, borderRadius: '16px 16px 0 0', background: last ? `linear-gradient(180deg, ${GREEN}, #129a4b)` : `linear-gradient(180deg, ${CYAN}, #1a5f8a)`, boxShadow: last ? `0 0 40px ${GREEN}88` : 'none'}} />
              <div style={{position: 'absolute', bottom: -64, fontFamily: MONT, fontWeight: 900, fontSize: 38, color: 'white'}}>{y}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const BrowserScene: React.FC<{base: number}> = () => (
  <AbsoluteFill>
    <AbsoluteFill style={{filter: 'brightness(0.4) saturate(1.1)'}}><Vid src="v/mk_14043.mp4" /></AbsoluteFill>
    <Scanlines opacity={0.15} />
    <div style={{position: 'absolute', top: 70, left: 0, right: 0}}><Label text="GAZETALAR UCHUN" size={84} color={YELLOW} /></div>
    <RetroBrowser at={0} until={2.9} y={230} stampAt={99} />
  </AbsoluteFill>
);

export const PrintWeb: React.FC = () => {
  const a = useSp(0);
  const b = useSp(5);
  const q = useSp(40, {damping: 8, stiffness: 220});
  return (
    <AbsoluteFill style={{background: '#05060a'}}>
      <Half side="l" s={a}><Vid src="v/mk_41192.mp4" filter="contrast(1.1) sepia(0.25)" />
        <div style={{position: 'absolute', bottom: 90, left: 0, right: 0}}><Label text="BOSMA GAZETA" size={110} /></div></Half>
      <Half side="r" s={b}><Vid src="v/mk_41201.mp4" filter="contrast(1.1) saturate(1.1)" />
        <div style={{position: 'absolute', bottom: 90, left: 0, right: 0}}><Label text="INTERNET" size={120} grad={ICE_GRAD} /></div></Half>
      <Divider color={YELLOW} />
      <CenterBadge s={q} bg={YELLOW} w={260} h={260}><div style={{fontFamily: ANTON, fontSize: 200, color: '#111', marginTop: -10}}>?</div></CenterBadge>
    </AbsoluteFill>
  );
};

export const OrgChart: React.FC<{year?: string; label: string; base: number; strikeAt: number}> = ({year, label, base, strikeAt}) => {
  const frame = useCurrentFrame();
  const intro = useSp(0);
  const st = at(strikeAt, base);
  const strike = interpolate(frame, [st, st + 10], [0, 1], {...clamp, easing: eo});
  const nw = spring({frame: frame - st - 14, fps: FPS, config: {damping: 11}});
  const box: React.CSSProperties = {width: 680, height: 230, borderRadius: 28, border: '4px solid rgba(255,255,255,0.6)', background: 'rgba(255,255,255,0.07)', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative'};
  return (
    <AbsoluteFill>
      <BgDark hue={0} />
      <div style={{position: 'absolute', top: 90, left: 0, right: 0, opacity: intro}}>
        {year && <Label text={year} size={110} grad={GOLD_GRAD} />}
        <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 48, color: YELLOW, letterSpacing: 4, textAlign: 'center', marginTop: 10}}>BOSH DIREKTOR</div>
      </div>
      <div style={{position: 'absolute', top: year ? 440 : 400, left: 0, right: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 50}}>
        <div style={{...box, opacity: intro, transform: `translateY(${(1 - intro) * 80}px)`}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 28}}>
            <Img src={staticFile('img/musk_2015.jpg')} style={{width: 140, height: 140, borderRadius: 70, objectFit: 'cover', objectPosition: '50% 20%', filter: strike > 0.5 ? 'grayscale(1) brightness(0.6)' : 'none'}} />
            <div style={{fontFamily: ANTON, fontSize: 88, color: 'white'}}>ILON MASK</div>
          </div>
          <svg width="680" height="230" style={{position: 'absolute', left: 0, top: 0}} viewBox="0 0 680 230"><line x1="40" y1="40" x2={40 + 600 * strike} y2={40 + 150 * strike} stroke={RED} strokeWidth="16" strokeLinecap="round" /><line x1="640" y1="40" x2={640 - 600 * strike} y2={40 + 150 * strike} stroke={RED} strokeWidth="16" strokeLinecap="round" /></svg>
        </div>
        <svg width="120" height="40" style={{opacity: nw}}><path d="M0 20h100m-20-14l20 14-20 14" stroke="white" strokeWidth="6" fill="none" /></svg>
        <div style={{...box, borderColor: GREEN, transform: `scale(${nw})`, boxShadow: `0 0 50px ${GREEN}55`}}>
          <div style={{fontFamily: ANTON, fontSize: 76, color: GREEN, textAlign: 'center'}}>{label}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const Control: React.FC = () => {
  const a = useSp(4);
  const b = useSp(20);
  const c = useSp(36, {damping: 9, stiffness: 220});
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{filter: 'brightness(0.35)'}}><Vid src="v/mk_49725.mp4" /></AbsoluteFill>
      <div style={{position: 'absolute', top: 0, bottom: 0, left: 0, right: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 50}}>
        <div style={{opacity: a, transform: `translateX(${(1 - a) * -300}px)`}}><Label text={'ASOS\nSOLISH'} size={150} grad={GOLD_GRAD} /></div>
        <div style={{transform: `scale(${c})`}}><Label text="≠" size={280} color={RED} /></div>
        <div style={{opacity: b, transform: `translateX(${(1 - b) * 300}px)`}}><Label text={"TO'LIQ\nNAZORAT"} size={150} grad={ICE_GRAD} /></div>
      </div>
    </AbsoluteFill>
  );
};

export const WordMark: React.FC<{text: string; sub?: string; color?: string; bgVid?: string}> = ({text, sub, color = CYAN, bgVid}) => {
  const frame = useCurrentFrame();
  const s = useSp(0, {damping: 10, stiffness: 160});
  return (
    <AbsoluteFill>
      {bgVid ? <AbsoluteFill style={{filter: 'brightness(0.3) blur(4px)'}}><Vid src={bgVid} /></AbsoluteFill> : <BgDark hue={220} grid />}
      <AbsoluteFill style={{background: `radial-gradient(circle at 50% 48%, ${color}55 0%, rgba(0,0,0,0) ${25 + s * 25}%)`}} />
      <div style={{position: 'absolute', top: 290, left: 0, right: 0, transform: `scale(${0.6 + 0.4 * s})`, opacity: s}}>
        <div style={{fontFamily: ANTON, fontSize: 340, textAlign: 'center', letterSpacing: 6, color: 'white', lineHeight: 1.05, textShadow: `0 0 ${40 + Math.sin(frame / 6) * 10}px ${color}, 0 8px 0 rgba(0,0,0,0.6)`}}>{text}</div>
        {sub && <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 48, color, textAlign: 'center', letterSpacing: 6, marginTop: 10}}>{sub}</div>}
      </div>
    </AbsoluteFill>
  );
};

export const Transfer: React.FC = () => {
  const frame = useCurrentFrame();
  const a = useSp(0);
  const phone = (x: number, label: string) => (
    <div style={{position: 'absolute', left: x, top: 300, width: 250, height: 460, borderRadius: 40, border: '8px solid white', background: '#0d1b2e', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', transform: `scale(${a})`}}>
      <div style={{fontFamily: ANTON, fontSize: 100, color: GREEN}}>$</div>
      <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 28, color: 'white'}}>{label}</div>
    </div>
  );
  return (
    <AbsoluteFill>
      <BgDark hue={150} />
      <div style={{position: 'absolute', top: 90, left: 0, right: 0}}><Label text={"PUL O'TKAZISH"} size={110} grad={GOLD_GRAD} /></div>
      {phone(420, 'YUBORUVCHI')}{phone(1250, 'OLUVCHI')}
      {Array.from({length: 7}).map((_, i) => {
        if (frame < 8 + i * 6) return null;
        const t = ((frame - 8 - i * 6) % 30) / 30;
        const x = 700 + t * 520; const y = 500 - Math.sin(t * Math.PI) * 260;
        return <div key={i} style={{position: 'absolute', left: x, top: y, width: 70, height: 70, borderRadius: 35, background: GOLD, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: ANTON, fontSize: 46, color: '#5a3d00', opacity: interpolate(t, [0, 0.1, 0.9, 1], [0, 1, 1, 0]), boxShadow: `0 0 20px ${GOLD}`}}>$</div>;
      })}
    </AbsoluteFill>
  );
};

export const Merge: React.FC = () => {
  const frame = useCurrentFrame();
  const m = interpolate(frame, [10, 34], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const p = spring({frame: frame - 36, fps: FPS, config: {damping: 9, stiffness: 200}});
  const ball = (txt: string, dir: number, c: string) => (
    <div style={{position: 'absolute', top: 330, left: W / 2 - 180 + dir * (480 * (1 - m)), width: 360, height: 360, borderRadius: 180, background: `${c}33`, border: `6px solid ${c}`, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: 1 - p, fontFamily: ANTON, fontSize: 66, color: 'white', textShadow: sh}}>{txt}</div>
  );
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{filter: 'brightness(0.3) blur(3px)'}}><Vid src="v/mk_30013.mp4" /></AbsoluteFill>
      <div style={{position: 'absolute', top: 90, left: 0, right: 0}}><Label text="BIRLASHUV" size={100} color={YELLOW} /></div>
      {ball('X.com', -1, CYAN)}{ball('Confinity', 1, GREEN)}
      <div style={{position: 'absolute', top: 340, left: 0, right: 0, transform: `scale(${p})`}}><Label text="PayPal" size={260} grad={'linear-gradient(180deg,#ffffff,#8ecbff)'} /></div>
    </AbsoluteFill>
  );
};

export const Stake: React.FC = () => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [6, 40], [0, 1], {...clamp, easing: eo});
  const r = 210; const c = 2 * Math.PI * r;
  return (
    <AbsoluteFill>
      <BgDark hue={140} />
      <div style={{position: 'absolute', top: 260, left: 160, width: 760}}>
        <Label text={'ULUSH\nSAQLANADI'} size={140} grad={GOLD_GRAD} align="left" />
        <div style={{marginTop: 30}}><Label text="KOMPANIYADA QOLADI" size={60} align="left" /></div>
      </div>
      <svg width="560" height="560" viewBox="-280 -280 560 560" style={{position: 'absolute', left: 1180, top: 260}}>
        <circle r={r} fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="76" />
        <circle r={r} fill="none" stroke={GREEN} strokeWidth="76" strokeDasharray={`${c * 0.12 * p} ${c}`} transform="rotate(-90)" style={{filter: `drop-shadow(0 0 20px ${GREEN})`}} />
        <text y="30" textAnchor="middle" fontFamily="Anton" fontSize="100" fill="white">MASK</text>
      </svg>
    </AbsoluteFill>
  );
};

export const Ebay: React.FC = () => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [4, 52], [0, 1.5], {...clamp, easing: Easing.bezier(0.2, 0.7, 0.2, 1)});
  const s = useSp(0);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{filter: 'brightness(0.3)'}}><Vid src="v/mk_45702.mp4" sf={2} /></AbsoluteFill>
      <div style={{position: 'absolute', top: 120, left: 0, right: 0, opacity: s}}><Label text={'eBay → PayPal'} size={110} color="white" /></div>
      <div style={{position: 'absolute', top: 340, left: 0, right: 0}}>
        <div style={{fontFamily: ANTON, fontSize: 280, textAlign: 'center', lineHeight: 1.05, ...gradText('linear-gradient(180deg,#FFFFFF 0%,#B9FFCB 45%,#2EE66E 100%)', 'rgba(61,255,138,0.6)')}}>${p.toFixed(1)} MLRD</div>
        <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 48, color: YELLOW, textAlign: 'center', letterSpacing: 4}}>BIR YARIM MILLIARD DOLLAR</div>
      </div>
    </AbsoluteFill>
  );
};

export const SafeRisky: React.FC<{base: number}> = ({base}) => {
  const frame = useCurrentFrame();
  const a = useSp(0);
  const b = useSp(5);
  const lit = interpolate(frame, [at(336.62, base) - 2, at(336.62, base) + 6], [0, 1], clamp);
  const pick = at(342.3, base);
  const chosen = frame >= pick;
  const ps = spring({frame: frame - pick, fps: FPS, config: {damping: 10, stiffness: 200}});
  return (
    <AbsoluteFill style={{background: '#05060a'}}>
      <Half side="l" s={a} filter={chosen ? 'grayscale(1) brightness(0.35)' : 'none'}>
        <Vid src="v/mk_47012.mp4" filter="contrast(1.1) saturate(1.2)" />
        <div style={{position: 'absolute', top: 120, left: 0, right: 0}}><Label text="XAVFSIZ" size={140} color={GREEN} /></div>
        <div style={{position: 'absolute', top: 290, left: 0, right: 0}}><Label text="INVESTITSIYALAR" size={70} /></div>
      </Half>
      <Half side="r" s={b} filter={`brightness(${0.35 + 0.65 * lit}) grayscale(${1 - lit})`}>
        <Vid src="v/mk_52304.mp4" filter="contrast(1.2) saturate(1.3)" />
        <div style={{position: 'absolute', top: 120, left: 0, right: 0}}><Label text="XAVFLI" size={140} color={RED} /></div>
        <div style={{position: 'absolute', top: 290, left: 0, right: 0}}><Label text="YANGI SOHALAR" size={70} /></div>
      </Half>
      <Divider />
      <div style={{position: 'absolute', right: 300, bottom: 110, padding: '18px 50px', borderRadius: 80, background: YELLOW, fontFamily: ANTON, fontSize: 84, color: '#111', transform: `scale(${chosen ? ps : 0})`, boxShadow: `0 0 50px ${YELLOW}`}}>2-YO'L ✓</div>
    </AbsoluteFill>
  );
};

export const RocketVsCode: React.FC = () => {
  const a = useSp(0);
  const b = useSp(6);
  const n = useSp(26, {damping: 9, stiffness: 220});
  return (
    <AbsoluteFill style={{background: '#05060a'}}>
      <Half side="l" s={a}><Vid src="v/n_c5_liftoff.mp4" sf={1} />
        <div style={{position: 'absolute', bottom: 90, left: 0, right: 0}}><Label text="RAKETA" size={130} grad={ICE_GRAD} /></div></Half>
      <Half side="r" s={b}><Vid src="v/mk_46634.mp4" filter="brightness(0.8)" />
        <div style={{position: 'absolute', bottom: 90, left: 0, right: 0}}><Label text="INTERNET DASTUR" size={100} /></div></Half>
      <Divider color={YELLOW} />
      <CenterBadge s={n} bg={RED} w={230} h={230}><div style={{fontFamily: ANTON, fontSize: 180, color: 'white'}}>≠</div></CenterBadge>
    </AbsoluteFill>
  );
};

export const Attempts: React.FC<{win?: boolean; base: number}> = ({win, base}) => {
  const frame = useCurrentFrame();
  const years = ['2006', '2007', '2008', '2008'];
  return (
    <AbsoluteFill>
      {win ? <AbsoluteFill style={{filter: 'brightness(0.4) blur(2px)'}}><Img src={staticFile('img/falcon1.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 40%', transform: `scale(${1.1 + frame * 0.001})`}} /></AbsoluteFill>
        : <AbsoluteFill style={{filter: 'brightness(0.45) saturate(1.2)'}}><Vid src="v/mk_48305.mp4" /></AbsoluteFill>}
      <div style={{position: 'absolute', top: 90, left: 0, right: 0}}><Label text={win ? '4-URINISH' : 'FALCON 1'} size={120} grad={win ? GOLD_GRAD : undefined} /></div>
      <div style={{position: 'absolute', top: 330, left: 120, right: 120, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 36}}>
        {years.map((y, i) => {
          const isWin = i === 3;
          if (isWin && !win) return <div key={i} style={{height: 460, borderRadius: 30, border: '5px dashed rgba(255,255,255,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: ANTON, fontSize: 160, color: 'rgba(255,255,255,0.3)'}}>?</div>;
          const appear = win ? (isWin ? at(374.4, base) : 0) : i * 24;
          const s = spring({frame: frame - appear, fps: FPS, config: {damping: 9, stiffness: 240}});
          const c = isWin ? GREEN : RED;
          return (
            <div key={i} style={{height: 460, borderRadius: 30, background: `${c}22`, border: `6px solid ${c}`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', transform: `scale(${win && !isWin ? 0.92 : s})`, opacity: win && !isWin ? 0.55 : 1, boxShadow: isWin ? `0 0 70px ${GREEN}` : 'none'}}>
              <div style={{fontFamily: ANTON, fontSize: 190, color: c, lineHeight: 1}}>{isWin ? '✓' : '✕'}</div>
              <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 40, color: 'white', marginTop: 20}}>{i + 1}-URINISH</div>
              <div style={{fontFamily: ANTON, fontSize: 60, color: 'white'}}>{y}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const Founders: React.FC<{base: number}> = ({base}) => {
  const a = useSp(at(392.26, base));
  const b = useSp(at(394.42, base));
  const t = useSp(0);
  const card = (s: number, name: string, img: string | null, dir: number) => (
    <div style={{width: 400, borderRadius: 30, overflow: 'hidden', background: 'rgba(255,255,255,0.08)', border: '4px solid rgba(255,255,255,0.5)', transform: `translateY(${(1 - s) * 500 * dir}px)`, opacity: s}}>
      <div style={{height: 470, background: '#1b2533', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        {img ? <Img src={staticFile(img)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 25%'}} />
          : <svg width="220" height="220" viewBox="0 0 24 24" fill="rgba(255,255,255,0.35)"><circle cx="12" cy="8" r="4.5" /><path d="M3 22c0-5 4-8 9-8s9 3 9 8z" /></svg>}
      </div>
      <div style={{padding: '16px 10px', fontFamily: ANTON, fontSize: 50, color: 'white', textAlign: 'center', lineHeight: 1.05, whiteSpace: 'pre-line'}}>{name}</div>
    </div>
  );
  return (
    <AbsoluteFill>
      <BgDark hue={0} />
      <div style={{position: 'absolute', top: 260, left: 130, width: 640, opacity: t}}>
        <Label text={'TESLA\nASOSCHILARI'} size={110} color={RED} align="left" />
        <div style={{marginTop: 20}}><Label text="2003" size={150} grad={GOLD_GRAD} align="left" /></div>
      </div>
      <div style={{position: 'absolute', top: 160, left: 840, display: 'flex', gap: 50}}>
        {card(a, 'MARTIN\nEBERHARD', 'img/eberhard.jpg', 1)}
        {card(b, 'MARK\nTARPENNING', null, -1)}
      </div>
    </AbsoluteFill>
  );
};

export const SplitSxTesla: React.FC = () => {
  const frame = useCurrentFrame();
  const a = useSp(0);
  const b = useSp(5);
  const lit = interpolate(frame, [at(414.0, 411.88) - 2, at(414.0, 411.88) + 6], [0, 1], clamp);
  return (
    <AbsoluteFill style={{background: '#05060a'}}>
      <Half side="l" s={a}><Vid src="v/n_fh_ignite.mp4" sf={1} />
        <div style={{position: 'absolute', bottom: 90, left: 0, right: 0}}><Label text="SPACEX" size={150} grad={ICE_GRAD} /></div></Half>
      <Half side="r" s={b} filter={`brightness(${0.35 + 0.65 * lit}) grayscale(${1 - lit})`}>
        <Img src={staticFile('img/tesla_factory.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '60% 60%'}} />
        <div style={{position: 'absolute', bottom: 90, left: 0, right: 0}}><Label text="TESLA" size={150} color={RED} /></div></Half>
      <Divider />
    </AbsoluteFill>
  );
};

export const CareerTimeline: React.FC<{base: number}> = ({base}) => {
  const frame = useCurrentFrame();
  const items: [string, string, number, string][] = [['1995', 'ZIP2\ninternet xaritalar', 455.4, CYAN], ['1999', 'X.com\n→ PayPal', 457.6, '#8ecbff'], ['2002', 'SPACEX\nraketalar', 459.5, 'white'], ['2004', 'TESLA\nelektromobillar', 460.3, RED]];
  const line = interpolate(frame, [6, at(461.0, base)], [0, 1], {...clamp, easing: eo});
  return (
    <AbsoluteFill>
      <BgDark hue={230} grid />
      <div style={{position: 'absolute', top: 100, left: 0, right: 0}}><Label text="1995 → BUGUN" size={110} grad={GOLD_GRAD} /></div>
      <div style={{position: 'absolute', left: 200, top: 540, width: 1520 * line, height: 8, background: `linear-gradient(90deg, ${CYAN}, ${RED})`, borderRadius: 4}} />
      {items.map(([y, t, s, c], i) => {
        const p = spring({frame: frame - at(s, base), fps: FPS, config: {damping: 12, stiffness: 200}});
        const x = 220 + i * 450;
        return (
          <div key={i} style={{position: 'absolute', left: x - 44, top: 500, opacity: p, transform: `translateY(${(1 - p) * 60}px)`}}>
            <div style={{width: 88, height: 88, borderRadius: 44, background: c, boxShadow: `0 0 30px ${c}`, border: '6px solid #0b0f18'}} />
            <div style={{position: 'absolute', top: -150, left: -40, width: 300, fontFamily: ANTON, fontSize: 100, color: c, lineHeight: 1}}>{y}</div>
            <div style={{position: 'absolute', top: 120, left: -40, width: 380, fontFamily: MONT, fontWeight: 900, fontSize: 40, color: 'white', whiteSpace: 'pre-line', lineHeight: 1.15}}>{t}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

export const Recap: React.FC<{base: number}> = ({base}) => {
  const frame = useCurrentFrame();
  const words: [string, number, string][] = [['KICHKINA OFIS', 465.9, 'v/mk_3112.mp4'], ['BITTA KOMPYUTER', 467.38, 'v/mk_41656.mp4'], ['KATTA TAVAKKAL', 468.5, 'v/mk_49906.mp4']];
  const idx = words.reduce((acc, w, i) => (frame >= at(w[1], base) ? i : acc), 0);
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <AbsoluteFill style={{filter: 'grayscale(1) contrast(1.3) brightness(0.55)'}}><Vid src={words[idx][2]} sf={2} /></AbsoluteFill>
      <Scanlines opacity={0.2} />
      <div style={{position: 'absolute', top: 250, left: 0, right: 0}}>
        {words.map(([w, s], i) => {
          const p = spring({frame: frame - at(s, base), fps: FPS, config: {damping: 11, stiffness: 220}});
          return <div key={i} style={{opacity: frame >= at(s, base) ? 1 : 0, transform: `scale(${0.6 + 0.4 * p})`, marginBottom: 20}}><Label text={w} size={130} color={i === idx ? YELLOW : 'white'} /></div>;
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
      <div style={{position: 'absolute', top: 60, left: 0, right: 0, transform: `scale(${s}) rotate(${Math.sin(frame / 10) * 3}deg)`}}><Label text="?" size={620} grad={GOLD_GRAD} /></div>
      <div style={{position: 'absolute', bottom: 110, left: 0, right: 0, opacity: s}}><Label text="SIZGA SAVOL" size={110} /></div>
    </AbsoluteFill>
  );
};

export const FinalSplit: React.FC<{base: number}> = ({base}) => {
  const frame = useCurrentFrame();
  const a = useSp(0);
  const b = useSp(6);
  const cues: [number, string][] = [[471.34, 'both'], [473.66, 'u'], [476.78, 'b'], [479.12, 'both'], [481.22, 'u'], [483.34, 'b']];
  const state = cues.reduce((acc, c) => (frame >= at(c[0], base) ? c[1] : acc), 'both');
  const dim = (on: boolean) => (on ? 'none' : 'grayscale(0.8) brightness(0.45)');
  const lab = (on: boolean, c: string): React.CSSProperties => ({transform: `scale(${on ? 1.1 : 0.9})`, color: on ? c : 'white', textShadow: on ? `0 0 50px ${c}, ${sh}` : sh});
  const age = useSp(at(471.34, base) + 8);
  return (
    <AbsoluteFill style={{background: '#05060a'}}>
      <Half side="l" s={a} filter={dim(state !== 'b')}>
        <Img src={staticFile('img/hoover.jpg')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 35%', transform: `scale(${1.1 + frame * 0.0006})`}} />
        <AbsoluteFill style={{background: 'linear-gradient(0deg, rgba(0,0,0,0.65) 0%, rgba(0,0,0,0) 55%)'}} />
        <div style={{position: 'absolute', bottom: 150, left: 0, right: 0}}><Label text="UNIVERSITET" size={120} style={lab(state === 'u', YELLOW)} /></div>
        <div style={{position: 'absolute', bottom: 80, left: 0, right: 0}}><Label text="Nufuzli · ishonchli" size={46} style={{fontFamily: MONT, fontWeight: 900}} /></div>
      </Half>
      <Half side="r" s={b} filter={dim(state !== 'u')}>
        <OffthreadVideo src={staticFile('v/mk_23043.mp4')} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
        <AbsoluteFill style={{background: 'linear-gradient(0deg, rgba(0,0,0,0.65) 0%, rgba(0,0,0,0) 55%)'}} />
        <div style={{position: 'absolute', bottom: 150, left: 0, right: 0}}><Label text="BIZNES" size={140} style={lab(state === 'b', GREEN)} /></div>
        <div style={{position: 'absolute', bottom: 80, left: 0, right: 0}}><Label text="Kelajagi noma'lum · tavakkal" size={46} style={{fontFamily: MONT, fontWeight: 900}} /></div>
      </Half>
      <Divider />
      <CenterBadge s={age} bg={YELLOW} w={220} h={220}>
        <div style={{fontFamily: ANTON, fontSize: 96, color: '#111', lineHeight: 1}}>24</div>
        <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 28, color: '#111'}}>YOSHDA</div>
      </CenterBadge>
    </AbsoluteFill>
  );
};

export const Comment: React.FC = () => {
  const frame = useCurrentFrame();
  const s = useSp(0, {damping: 11, stiffness: 180});
  const text = 'Men tanlagan bo‘lardim...';
  const typed = text.slice(0, Math.floor(interpolate(frame, [8, 34], [0, text.length], clamp)));
  return (
    <AbsoluteFill>
      <BgDark hue={45} />
      <div style={{position: 'absolute', top: 120, left: 0, right: 0}}><Label text={'JAVOBINGIZNI IZOHLARDA YOZING'} size={100} grad={GOLD_GRAD} /></div>
      <div style={{position: 'absolute', top: 470, left: 360, right: 360, borderRadius: 40, background: 'white', padding: '40px 44px', transform: `scale(${s})`, boxShadow: '0 20px 60px rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', gap: 26}}>
        <svg width="80" height="80" viewBox="0 0 24 24"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1.1-4.6A8 8 0 1 1 21 12z" fill="#111" /></svg>
        <div style={{fontFamily: MONT, fontWeight: 800, fontSize: 56, color: '#111'}}>{typed}<span style={{opacity: frame % 16 < 8 ? 1 : 0}}>|</span></div>
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ overlays (y already mapped to 1080 by Main)
export const AgeBadge: React.FC<{n: number; y: number}> = ({n, y}) => {
  const frame = useCurrentFrame();
  const v = Math.round(interpolate(frame, [0, 20], [0, n], {...clamp, easing: eo}));
  const s = useSp(0, {damping: 10, stiffness: 200});
  return (
    <AbsoluteFill style={{top: y, height: 'auto', alignItems: 'center'}}>
      <div style={{display: 'flex', alignItems: 'baseline', gap: 18, transform: `scale(${s})`, background: 'rgba(0,0,0,0.55)', padding: '6px 44px', borderRadius: 26, border: `5px solid ${YELLOW}`}}>
        <div style={{fontFamily: ANTON, fontSize: 170, color: YELLOW, lineHeight: 1, fontVariantNumeric: 'tabular-nums'}}>{v}</div>
        <div style={{fontFamily: ANTON, fontSize: 86, color: 'white'}}>YOSH</div>
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
      {label && <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 38, color: YELLOW, letterSpacing: 3, textShadow: sh, marginBottom: 4}}>{label}</div>}
      <div style={{fontFamily: ANTON, fontSize: 170, lineHeight: 1.1, fontVariantNumeric: 'tabular-nums', transform: `scale(${1 + 0.1 * (1 - pop) * (p >= 1 ? 1 : 0)})`, ...gradText('linear-gradient(180deg,#FFFFFF 0%,#B9FFCB 45%,#2EE66E 100%)', 'rgba(61,255,138,0.55)')}}>{str}</div>
    </AbsoluteFill>
  );
};

export const List3: React.FC<{items: [string, number][]; y: number; base: number}> = ({items, y, base}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{position: 'absolute', top: y, left: 90}}>
      {items.map(([t, s], i) => {
        const p = spring({frame: frame - at(s, base), fps: FPS, config: {damping: 13, stiffness: 200}});
        const active = frame >= at(s, base) && (i === items.length - 1 || frame < at(items[i + 1][1], base));
        return <div key={i} style={{display: 'table', fontFamily: MONT, fontWeight: 900, fontSize: active ? 50 : 42, color: active ? '#111' : 'white', background: active ? YELLOW : 'rgba(0,0,0,0.6)', padding: '8px 26px', borderRadius: 14, marginBottom: 14, opacity: p, transform: `translateX(${(1 - p) * -300}px)`}}>{i + 1}. {t}</div>;
      })}
    </div>
  );
};

export const Quote: React.FC<{text: string; by: string; y: number}> = ({text, by, y}) => {
  const s = useSp(0);
  return (
    <AbsoluteFill style={{top: y, height: 'auto', alignItems: 'center'}}>
      <div style={{background: 'rgba(0,0,0,0.6)', borderLeft: `12px solid ${YELLOW}`, padding: '24px 40px', borderRadius: 20, transform: `translateY(${(1 - s) * 60}px)`, opacity: s}}>
        <div style={{fontFamily: ANTON, fontSize: 90, color: 'white', lineHeight: 1.05}}>{text}</div>
        <div style={{fontFamily: MONT, fontWeight: 800, fontSize: 32, color: YELLOW, marginTop: 10}}>— {by}</div>
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
    <div style={{position: 'absolute', top: y, right: 120}}>
      <svg width="700" height="300" viewBox="-20 0 800 340" style={{filter: `drop-shadow(0 0 16px ${GREEN})`}}>
        <path d={d} stroke={GREEN} strokeWidth="14" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="1200" strokeDashoffset={1200 * (1 - p)} />
        <polygon points="750,40 700,60 735,90" fill={GREEN} opacity={p > 0.95 ? 1 : 0} />
      </svg>
    </div>
  );
};

export const Drain: React.FC<{y: number}> = ({y}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, 45], [1, 0.12], {...clamp, easing: eo});
  return (
    <AbsoluteFill style={{top: y, height: 'auto', alignItems: 'center'}}>
      <div style={{fontFamily: MONT, fontWeight: 900, fontSize: 46, color: 'white', marginBottom: 14, textShadow: sh}}>KOMPANIYA MABLAG‘I</div>
      <div style={{width: 900, height: 80, borderRadius: 40, border: '6px solid white', overflow: 'hidden', background: 'rgba(0,0,0,0.5)'}}>
        <div style={{width: `${p * 100}%`, height: '100%', background: p < 0.35 ? RED : p < 0.6 ? GOLD : GREEN}} />
      </div>
    </AbsoluteFill>
  );
};
