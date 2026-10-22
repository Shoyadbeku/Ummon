import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {CalloutKind} from './data';

const YELLOW = '#FFD84D';
const RED = '#FF3B45';
const GREEN = '#3BD16F';

const useAnim = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 11, stiffness: 180}});
  const exit = interpolate(frame, [durationInFrames - 6, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return {frame, fps, enter, exit};
};

const big: React.CSSProperties = {
  fontWeight: 900,
  textTransform: 'uppercase',
  letterSpacing: -2,
  lineHeight: 1,
  WebkitTextStroke: '12px #0b0b10',
  paintOrder: 'stroke fill',
};

const Card: React.FC<{children: React.ReactNode; top?: number; tilt?: number}> = ({children, top = 230, tilt = -3}) => {
  const {enter, exit} = useAnim();
  return (
    <div
      style={{
        position: 'absolute',
        top,
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'center',
        transform: `scale(${0.4 + 0.6 * enter}) rotate(${tilt * enter}deg)`,
        opacity: Math.min(enter * 2, exit),
      }}
    >
      {children}
    </div>
  );
};

const Check: React.FC<{size: number; color?: string}> = ({size, color = GREEN}) => (
  <svg width={size} height={size} viewBox="0 0 100 100">
    <circle cx="50" cy="50" r="46" fill={color} stroke="#0b0b10" strokeWidth="6" />
    <path d="M28 52 L44 68 L74 36" fill="none" stroke="#fff" strokeWidth="11" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const Cross: React.FC<{size: number; progress?: number}> = ({size, progress = 1}) => (
  <svg width={size} height={size} viewBox="0 0 100 100">
    <circle cx="50" cy="50" r="46" fill={RED} stroke="#0b0b10" strokeWidth="6" />
    <path d="M32 32 L68 68" stroke="#fff" strokeWidth="12" strokeLinecap="round" strokeDasharray="52" strokeDashoffset={52 * (1 - Math.min(1, progress * 2))} />
    <path d="M68 32 L32 68" stroke="#fff" strokeWidth="12" strokeLinecap="round" strokeDasharray="52" strokeDashoffset={52 * (1 - Math.max(0, progress * 2 - 1))} />
  </svg>
);

const Hook: React.FC<{title: string; sub: string}> = ({title, sub}) => {
  const {frame, fps, enter, exit} = useAnim();
  const subIn = spring({frame: frame - 8, fps, config: {damping: 12}});
  const letters = title.split('');
  return (
    <div style={{position: 'absolute', top: 200, left: 0, right: 0, textAlign: 'center', opacity: exit}}>
      <div style={{display: 'inline-block', background: RED, color: '#fff', fontWeight: 900, fontSize: 40, padding: '10px 26px', borderRadius: 14, transform: `scale(${enter})`, letterSpacing: 2}}>
        BILASIZMI?
      </div>
      <div style={{marginTop: 18}}>
        {letters.map((ch, i) => {
          const s = spring({frame: frame - 3 - i * 1.2, fps, config: {damping: 9, stiffness: 260}});
          return (
            <span key={i} style={{...big, fontSize: 128, color: '#fff', display: 'inline-block', whiteSpace: 'pre', transform: `translateY(${(1 - s) * -80}px) scale(${s})`}}>
              {ch}
            </span>
          );
        })}
      </div>
      <div style={{...big, fontSize: 78, color: YELLOW, transform: `scale(${subIn})`, marginTop: 6}}>{sub}</div>
    </div>
  );
};

const Tag: React.FC<{title: string; sub?: string; top?: number}> = ({title, sub, top}) => (
  <Card top={top}>
    <div style={{display: 'flex', alignItems: 'center', background: 'rgba(12,12,18,0.82)', borderRadius: 30, padding: '20px 34px', border: `5px solid ${YELLOW}`, gap: 24, boxShadow: '0 20px 50px rgba(0,0,0,0.5)'}}>
      <span style={{background: YELLOW, color: '#111', fontWeight: 900, fontSize: 54, padding: '6px 20px', borderRadius: 16}}>{title}</span>
      {sub ? <span style={{color: '#fff', fontWeight: 800, fontSize: 56}}>{sub}</span> : null}
    </div>
  </Card>
);

const Badge: React.FC<{title: string; sub?: string}> = ({title, sub}) => {
  const {frame} = useAnim();
  const bob = Math.sin(frame / 8) * 6;
  return (
    <Card tilt={2}>
      <div style={{display: 'flex', alignItems: 'center', gap: 22, background: '#fff', borderRadius: 34, padding: '18px 36px 18px 22px', boxShadow: '0 20px 50px rgba(0,0,0,0.5)', transform: `translateY(${bob}px)`}}>
        <svg width="110" height="110" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="48" fill="#2E8BFF" />
          <path d="M30 30 C30 18 45 20 50 26 C55 20 70 18 70 30 C70 44 66 52 64 70 C62 80 56 80 55 70 L52 56 L48 56 L45 70 C44 80 38 80 36 70 C34 52 30 44 30 30 Z" fill="#fff" />
        </svg>
        <div>
          <div style={{fontWeight: 900, fontSize: 64, color: '#111', letterSpacing: -1}}>{title}</div>
          <div style={{fontWeight: 800, fontSize: 44, color: '#2E8BFF'}}>{sub}</div>
        </div>
      </div>
    </Card>
  );
};

const Question: React.FC<{title: string}> = ({title}) => {
  const {frame, enter, exit} = useAnim();
  const wob = Math.sin(frame / 2.5) * 4 * Math.max(0, 1 - frame / 30);
  return (
    <div style={{position: 'absolute', top: 260, left: 0, right: 0, textAlign: 'center', opacity: exit}}>
      <span style={{...big, fontSize: 170, color: RED, display: 'inline-block', transform: `scale(${enter}) rotate(${wob - 4}deg)`}}>{title}</span>
    </div>
  );
};

const Pea: React.FC<{title: string; sub?: string}> = ({title, sub}) => {
  const {frame, fps} = useAnim();
  const ball = spring({frame: frame - 4, fps, config: {damping: 7, stiffness: 200}});
  const ok = spring({frame: frame - 14, fps, config: {damping: 9}});
  return (
    <Card top={220} tilt={0}>
      <div style={{display: 'flex', alignItems: 'center', gap: 26, background: 'rgba(12,12,18,0.82)', borderRadius: 40, padding: '24px 40px', border: `5px solid ${GREEN}`}}>
        <svg width="120" height="120" viewBox="0 0 100 100" style={{transform: `scale(${ball})`}}>
          <defs>
            <radialGradient id="pea" cx="35%" cy="35%" r="70%">
              <stop offset="0%" stopColor="#B9F27C" />
              <stop offset="100%" stopColor="#3E9A2A" />
            </radialGradient>
          </defs>
          <circle cx="50" cy="50" r="40" fill="url(#pea)" stroke="#0b0b10" strokeWidth="5" />
          <circle cx="36" cy="36" r="9" fill="rgba(255,255,255,0.7)" />
        </svg>
        <div>
          <div style={{fontWeight: 900, fontSize: 76, color: '#fff', letterSpacing: -1}}>{title}</div>
          <div style={{display: 'flex', alignItems: 'center', gap: 12, transform: `scale(${ok})`, transformOrigin: 'left center'}}>
            <span style={{fontWeight: 900, fontSize: 56, color: GREEN, textTransform: 'uppercase'}}>{sub}</span>
            <Check size={60} />
          </div>
        </div>
      </div>
    </Card>
  );
};

const Month: React.FC<{title: string; sub?: string}> = ({title, sub}) => {
  const {frame, fps} = useAnim();
  const strike = interpolate(frame, [10, 20], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const second = spring({frame: frame - 18, fps, config: {damping: 8, stiffness: 220}});
  return (
    <Card tilt={0}>
      <div style={{display: 'flex', alignItems: 'center', gap: 30}}>
        <div style={{position: 'relative'}}>
          <span style={{...big, fontSize: 104, color: '#fff', wordSpacing: 18}}>{title}</span>
          <div style={{position: 'absolute', left: -10, top: '48%', height: 16, width: `${strike * 110}%`, background: RED, borderRadius: 8, transform: 'rotate(-8deg)'}} />
        </div>
        <span style={{...big, fontSize: 100, color: YELLOW, opacity: strike}}>→</span>
        <span style={{...big, fontSize: 104, color: RED, wordSpacing: 18, display: 'inline-block', transform: `scale(${second})`}}>{sub}</span>
      </div>
    </Card>
  );
};

const Stamp: React.FC<{title: string}> = ({title}) => {
  const {frame, fps, exit} = useAnim();
  const slam = spring({frame, fps, config: {damping: 14, stiffness: 400}});
  const scale = interpolate(slam, [0, 1], [2.6, 1]);
  return (
    <div style={{position: 'absolute', top: 250, left: 0, right: 0, display: 'flex', justifyContent: 'center', opacity: Math.min(slam * 3, exit)}}>
      <div style={{transform: `scale(${scale}) rotate(-9deg)`, border: `12px solid ${RED}`, borderRadius: 24, padding: '14px 34px', background: 'rgba(255,59,69,0.12)', boxShadow: '0 0 0 6px rgba(0,0,0,0.25)'}}>
        <span style={{fontWeight: 900, fontSize: 78, color: RED, letterSpacing: 2, whiteSpace: 'nowrap', textShadow: '0 4px 0 rgba(0,0,0,0.35)'}}>{title}</span>
      </div>
    </div>
  );
};

const Sls: React.FC<{title: string; sub?: string}> = ({title, sub}) => {
  const {frame, fps, exit} = useAnim();
  const slam = spring({frame, fps, config: {damping: 10, stiffness: 320}});
  const scale = interpolate(slam, [0, 1], [3.2, 1]);
  const shake = frame < 10 ? Math.sin(frame * 3) * (10 - frame) * 2 : 0;
  const ring = interpolate(frame, [0, 18], [0.3, 2.4], {extrapolateRight: 'clamp'});
  const ringO = interpolate(frame, [0, 18], [0.9, 0], {extrapolateRight: 'clamp'});
  return (
    <div style={{position: 'absolute', inset: 0, opacity: exit}}>
      <div style={{position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.35)'}} />
      <div style={{position: 'absolute', top: 640, left: 540, width: 400, height: 400, marginLeft: -200, marginTop: -200, borderRadius: '50%', border: `14px solid ${YELLOW}`, transform: `scale(${ring})`, opacity: ringO}} />
      <div style={{position: 'absolute', top: 470, left: 0, right: 0, textAlign: 'center', transform: `translateX(${shake}px)`}}>
        <div style={{...big, fontSize: 300, color: YELLOW, transform: `scale(${scale})`, WebkitTextStroke: '18px #0b0b10'}}>{title}</div>
        <div style={{display: 'inline-block', marginTop: 20, background: '#fff', color: '#111', fontWeight: 900, fontSize: 50, padding: '10px 28px', borderRadius: 16, opacity: slam}}>{sub}</div>
      </div>
    </div>
  );
};

const CrossOut: React.FC<{title: string}> = ({title}) => {
  const {frame} = useAnim();
  const p = interpolate(frame, [2, 14], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <Card tilt={-2}>
      <div style={{display: 'flex', alignItems: 'center', gap: 20, background: 'rgba(12,12,18,0.85)', borderRadius: 30, padding: '18px 32px', border: `5px solid ${RED}`}}>
        <Cross size={96} progress={p} />
        <span style={{fontWeight: 900, fontSize: 80, color: '#fff', letterSpacing: -1}}>{title}</span>
      </div>
    </Card>
  );
};

const Illusion: React.FC<{title: string; sub?: string}> = ({title, sub}) => {
  const {frame, enter, exit} = useAnim();
  const shimmer = (frame * 9) % 260;
  const glitch = frame % 23 < 2 ? 8 : 0;
  return (
    <div style={{position: 'absolute', top: 210, left: 0, right: 0, textAlign: 'center', opacity: Math.min(enter, exit), transform: `scale(${0.6 + 0.4 * enter})`}}>
      <div style={{position: 'relative', display: 'inline-block'}}>
        <span style={{...big, fontSize: 140, position: 'absolute', left: glitch, top: 0, color: 'rgba(0,229,255,0.6)', WebkitTextStroke: '0px'}}>{title}</span>
        <span
          style={{
            ...big,
            fontSize: 140,
            position: 'relative',
            color: 'transparent',
            backgroundImage: `linear-gradient(100deg, #fff 0%, #fff ${shimmer - 60}%, #9ff3ff ${shimmer - 30}%, #fff ${shimmer}%, #fff 100%)`,
            WebkitBackgroundClip: 'text',
            backgroundClip: 'text',
            WebkitTextStroke: '0px',
            filter: 'drop-shadow(0 6px 0 #0b0b10) drop-shadow(0 0 22px rgba(0,229,255,0.55))',
          }}
        >
          {title}
        </span>
      </div>
      <div style={{fontWeight: 900, fontSize: 84, color: YELLOW, fontStyle: 'italic', marginTop: 4, WebkitTextStroke: '10px #0b0b10', paintOrder: 'stroke fill'}}>{sub}</div>
    </div>
  );
};

const Outro: React.FC<{title: string; sub?: string}> = ({title, sub}) => {
  const {frame, fps} = useAnim();
  const a = spring({frame, fps, config: {damping: 12}});
  const b = spring({frame: frame - 8, fps, config: {damping: 8, stiffness: 200}});
  const pulse = 1 + Math.sin(frame / 4) * 0.04;
  return (
    <div style={{position: 'absolute', top: 1180, left: 0, right: 0, textAlign: 'center'}}>
      <div style={{...big, fontSize: 82, color: '#fff', textTransform: 'none', letterSpacing: -1, transform: `translateY(${(1 - a) * 60}px)`, opacity: a}}>{title}</div>
      <div style={{display: 'inline-block', marginTop: 34, background: RED, color: '#fff', fontWeight: 900, fontSize: 64, padding: '20px 54px', borderRadius: 999, boxShadow: '0 16px 40px rgba(255,59,69,0.55)', transform: `scale(${b * pulse})`}}>
        {sub}
      </div>
    </div>
  );
};

export const Callout: React.FC<{kind: CalloutKind; title?: string; sub?: string; top?: number}> = ({kind, title = '', sub = '', top}) => {
  switch (kind) {
    case 'hook':
      return <Hook title={title} sub={sub} />;
    case 'tag':
      return <Tag title={title} sub={sub} top={top} />;
    case 'badge':
      return <Badge title={title} sub={sub} />;
    case 'question':
      return <Question title={title} />;
    case 'pea':
      return <Pea title={title} sub={sub} />;
    case 'month':
      return <Month title={title} sub={sub} />;
    case 'stamp':
      return <Stamp title={title} />;
    case 'sls':
      return <Sls title={title} sub={sub} />;
    case 'cross':
      return <CrossOut title={title} />;
    case 'illusion':
      return <Illusion title={title} sub={sub} />;
    case 'outro':
      return <Outro title={title} sub={sub} />;
  }
};
