import React from 'react';
import {AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {BODY, C, HEAD} from './theme';
import {ClipLayer, sourceLabel} from './Layers';
import metaJson from './data/meta.json';

const useS = (delay = 0, damping = 200) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: f - delay, fps, config: {damping}});
};

const Kicker: React.FC<{children: React.ReactNode}> = ({children}) => (
  <div style={{fontFamily: BODY, fontSize: 24, fontWeight: 700, letterSpacing: 5, color: C.gold, textTransform: 'uppercase'}}>
    {children}
  </div>
);

const H: React.FC<{children: React.ReactNode; size?: number}> = ({children, size = 64}) => (
  <div style={{fontFamily: HEAD, fontWeight: 800, fontSize: size, color: C.ink, lineHeight: 1.1}}>{children}</div>
);

const Center: React.FC<{children: React.ReactNode; pad?: number}> = ({children, pad = 160}) => (
  <AbsoluteFill style={{justifyContent: 'center', padding: `0 ${pad}px`}}>{children}</AbsoluteFill>
);

/* ---- Chapter card ---- */
export const Chapter: React.FC<{num: string; title: string; sub: string}> = ({num, title, sub}) => {
  const s = useS(0, 18);
  const l = useS(6);
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
      {num ? (
        <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 300, color: 'transparent', WebkitTextStroke: `2px ${C.gold}`, opacity: 0.35 * s, position: 'absolute', transform: `scale(${1.2 - 0.2 * s})`}}>
          {num}
        </div>
      ) : null}
      <div style={{textAlign: 'center', transform: `translateY(${(1 - s) * 30}px)`, opacity: s}}>
        <Kicker>{sub}</Kicker>
        <div style={{height: 3, width: 160 * l, background: C.gold, margin: '22px auto'}} />
        <H size={92}>{title}</H>
      </div>
    </AbsoluteFill>
  );
};

/* ---- Typographic statement ---- */
export const Typo: React.FC<{text: string; sub?: string}> = ({text, sub}) => {
  const s = useS(0, 16);
  const s2 = useS(10);
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', textAlign: 'center', padding: '0 180px'}}>
      <div style={{transform: `scale(${0.92 + 0.08 * s})`, opacity: s}}>
        <H size={text.length > 26 ? 76 : 104}>{text}</H>
      </div>
      {sub ? (
        <div style={{fontFamily: BODY, fontSize: 34, color: C.dim, marginTop: 28, opacity: s2, maxWidth: 1300}}>{sub}</div>
      ) : null}
    </AbsoluteFill>
  );
};

/* ---- Numbered steps / checklist ---- */
export const Steps: React.FC<{title: string; items: string[]; numbered?: boolean; dur: number}> = ({title, items, numbered = true, dur}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = useS(0);
  const gap = Math.max(10, Math.min(40, (dur - 40) / items.length));
  return (
    <Center>
      <div style={{opacity: t, transform: `translateY(${(1 - t) * 20}px)`}}>
        <Kicker>{numbered ? 'Bosqichlar' : 'Mezonlar'}</Kicker>
        <div style={{marginTop: 14, marginBottom: 46}}>
          <H size={60}>{title}</H>
        </div>
      </div>
      {items.map((it, i) => {
        const s = spring({frame: f - 12 - i * gap, fps, config: {damping: 200}});
        return (
          <div key={i} style={{display: 'flex', alignItems: 'center', gap: 28, marginBottom: 24, opacity: s, transform: `translateX(${(1 - s) * -40}px)`}}>
            <div style={{width: 64, height: 64, borderRadius: 32, border: `2px solid ${C.gold}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: HEAD, fontWeight: 800, fontSize: 28, color: C.gold, background: 'rgba(242,193,78,0.08)'}}>
              {numbered ? i + 1 : '✓'}
            </div>
            <div style={{fontFamily: BODY, fontSize: 44, fontWeight: 600, color: C.ink}}>{it}</div>
          </div>
        );
      })}
    </Center>
  );
};

/* ---- Visa requirement for the three named destinations ---- */
export const VisaMap: React.FC<{items: [string, string][]}> = ({items}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <Center>
      <Kicker>O‘zbekiston oddiy pasporti bilan</Kicker>
      <div style={{display: 'flex', gap: 36, marginTop: 50}}>
        {items.map(([name, st], i) => {
          const s = spring({frame: f - 6 - i * 14, fps, config: {damping: 16}});
          return (
            <div key={i} style={{flex: 1, padding: '44px 36px', background: 'rgba(14,29,54,0.82)', border: `1px solid ${C.line}`, borderTop: `4px solid ${C.red}`, borderRadius: 8, opacity: s, transform: `translateY(${(1 - s) * 50}px)`}}>
              <div style={{fontFamily: HEAD, fontWeight: 800, fontSize: 50, color: C.ink}}>{name}</div>
              <div style={{marginTop: 26, display: 'inline-block', padding: '10px 18px', border: `2px solid ${C.red}`, color: C.red, fontFamily: BODY, fontWeight: 800, fontSize: 28, letterSpacing: 2, textTransform: 'uppercase', transform: `rotate(-3deg) scale(${1.4 - 0.4 * s})`}}>
                {st}
              </div>
            </div>
          );
        })}
      </div>
    </Center>
  );
};

/* ---- Rank card: 82nd place, 57 destinations ---- */
export const Rank: React.FC<{rank: number; dest: number}> = ({rank, dest}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [6, 50], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const p2 = interpolate(f, [40, 90], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const s = useS(0);
  return (
    <Center>
      <div style={{opacity: s}}>
        <Kicker>Henley Passport Index · 2026-yil oktabr</Kicker>
        <div style={{marginTop: 12}}><H size={58}>O‘zbekiston pasporti</H></div>
      </div>
      <div style={{display: 'flex', gap: 120, marginTop: 70, alignItems: 'flex-end'}}>
        <div>
          <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 230, color: C.gold, lineHeight: 0.9}}>{Math.round(rank * p)}<span style={{fontSize: 90}}>-o‘rin</span></div>
          <div style={{fontFamily: BODY, fontSize: 32, color: C.dim, marginTop: 16}}>reytingdagi o‘rni</div>
        </div>
        <div style={{opacity: p2}}>
          <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 230, color: C.ink, lineHeight: 0.9}}>{Math.round(dest * p2)}</div>
          <div style={{fontFamily: BODY, fontSize: 32, color: C.dim, marginTop: 16, maxWidth: 560}}>davlat va hududga oldindan vizasiz yoki yetib borganda viza bilan</div>
        </div>
      </div>
    </Center>
  );
};

/* ---- Horizontal bar comparison ---- */
export const Bars: React.FC<{title: string; bars: [string, number][]; note?: string}> = ({title, bars, note}) => {
  const f = useCurrentFrame();
  const max = Math.max(...bars.map((b) => b[1]));
  const s = useS(0);
  return (
    <Center>
      <div style={{opacity: s}}>
        <Kicker>Pasport imkoniyatlari</Kicker>
        <div style={{marginTop: 12, marginBottom: 50}}><H size={50}>{title}</H></div>
      </div>
      {bars.map(([name, v], i) => {
        const p = interpolate(f, [8 + i * 8, 48 + i * 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
        const uz = name.startsWith('O‘zbekiston');
        return (
          <div key={i} style={{display: 'flex', alignItems: 'center', marginBottom: 26}}>
            <div style={{width: 300, fontFamily: BODY, fontSize: 36, fontWeight: uz ? 800 : 500, color: uz ? C.gold : C.ink}}>{name}</div>
            <div style={{flex: 1, height: 58, background: 'rgba(244,241,234,0.06)', borderRadius: 4, position: 'relative'}}>
              <div style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: `${(v / max) * 100 * p}%`, background: uz ? C.gold : i === 0 ? C.teal : 'rgba(244,241,234,0.55)', borderRadius: 4}} />
            </div>
            <div style={{width: 140, textAlign: 'right', fontFamily: HEAD, fontWeight: 800, fontSize: 46, color: uz ? C.gold : C.ink}}>{Math.round(v * p)}</div>
          </div>
        );
      })}
      {note ? <div style={{fontFamily: BODY, fontSize: 22, color: C.dim, marginTop: 20}}>{note}</div> : null}
    </Center>
  );
};

/* ---- 57 destinations are not all visa-free ---- */
export const Split57: React.FC<{title: string; left: string; right: string}> = ({title, left, right}) => {
  const f = useCurrentFrame();
  const s = useS(0, 16);
  const sp = interpolate(f, [20, 50], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
  const box = (t: string, col: string, dx: number) => (
    <div style={{width: 600, padding: '40px 36px', background: 'rgba(14,29,54,0.85)', border: `2px solid ${col}`, borderRadius: 10, transform: `translateX(${dx * sp}px)`, opacity: sp, textAlign: 'center'}}>
      <div style={{fontFamily: HEAD, fontWeight: 800, fontSize: 44, color: col}}>{t}</div>
    </div>
  );
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
      <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 150, color: C.ink, opacity: s, transform: `translateY(${-110 * sp}px)`}}>{title}</div>
      <div style={{position: 'absolute', top: 560, display: 'flex', gap: 80}}>
        {box(left, C.teal, -10)}
        {box(right, C.gold, 10)}
      </div>
      <div style={{position: 'absolute', top: 770, fontFamily: BODY, fontSize: 30, color: C.dim, opacity: sp}}>
        Reytingdagi barcha yo‘nalishlar ham “vizasiz” emas
      </div>
    </AbsoluteFill>
  );
};

/* ---- Risk meter ---- */
export const Risk: React.FC<{title: string}> = ({title}) => {
  const f = useCurrentFrame();
  const s = useS(0);
  const a = interpolate(f, [10, 70], [-80, 25], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.back(1.4))});
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
      <div style={{opacity: s, textAlign: 'center'}}>
        <Kicker>Viza siyosatida</Kicker>
        <div style={{marginTop: 12}}><H size={56}>{title}</H></div>
      </div>
      <svg width="700" height="380" viewBox="0 0 700 380" style={{marginTop: 40, opacity: s}}>
        <defs>
          <linearGradient id="rg" x1="0" x2="1">
            <stop offset="0" stopColor={C.teal} />
            <stop offset="0.5" stopColor={C.gold} />
            <stop offset="1" stopColor={C.red} />
          </linearGradient>
        </defs>
        <path d="M 70 340 A 280 280 0 0 1 630 340" stroke="url(#rg)" strokeWidth="34" fill="none" strokeLinecap="round" />
        <g transform={`rotate(${a} 350 340)`}>
          <line x1="350" y1="340" x2="350" y2="110" stroke={C.ink} strokeWidth="8" strokeLinecap="round" />
        </g>
        <circle cx="350" cy="340" r="18" fill={C.ink} />
        <text x="70" y="378" fill={C.dim} fontFamily="Inter" fontSize="24" textAnchor="middle">past</text>
        <text x="630" y="378" fill={C.dim} fontFamily="Inter" fontSize="24" textAnchor="middle">yuqori</text>
      </svg>
      <div style={{fontFamily: BODY, fontSize: 28, color: C.dim, marginTop: 20, opacity: s}}>Shaxsiy emas — mamlakat bo‘yicha umumiy baho</div>
    </AbsoluteFill>
  );
};

/* ---- Asymmetric visa regime ---- */
export const Reciprocity: React.FC<{a: string; b: string; ab: string; ba: string}> = ({a, b, ab, ba}) => {
  const f = useCurrentFrame();
  const s = useS(0);
  const p1 = interpolate(f, [15, 45], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const p2 = interpolate(f, [60, 90], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const node = (t: string, col: string) => (
    <div style={{width: 380, height: 160, borderRadius: 12, border: `2px solid ${col}`, background: 'rgba(14,29,54,0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: HEAD, fontWeight: 800, fontSize: 42, color: C.ink}}>{t}</div>
  );
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', opacity: s}}>
      <div style={{position: 'absolute', top: 160, textAlign: 'center'}}>
        <Kicker>Shartlar har doim ham bir xil emas</Kicker>
      </div>
      <div style={{display: 'flex', alignItems: 'center', gap: 40}}>
        {node(a, C.gold)}
        <div style={{width: 560, position: 'relative', height: 200}}>
          <div style={{position: 'absolute', top: 40, left: 0, height: 4, width: `${p1 * 100}%`, background: C.teal}} />
          <div style={{position: 'absolute', top: 0, width: '100%', textAlign: 'center', fontFamily: BODY, fontWeight: 700, fontSize: 30, color: C.teal, opacity: p1}}>{ab} →</div>
          <div style={{position: 'absolute', top: 150, right: 0, height: 4, width: `${p2 * 100}%`, background: C.red}} />
          <div style={{position: 'absolute', top: 165, width: '100%', textAlign: 'center', fontFamily: BODY, fontWeight: 700, fontSize: 30, color: C.red, opacity: p2}}>← {ba}</div>
        </div>
        {node(b, C.line)}
      </div>
      <div style={{position: 'absolute', bottom: 190, fontFamily: BODY, fontSize: 26, color: C.dim}}>Sxematik misol</div>
    </AbsoluteFill>
  );
};

/* ---- Ranking timeline 75 → 74 → 82 (lower is better) ---- */
export const Timeline: React.FC<{points: [string, number][]}> = ({points}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = useS(0);
  const x0 = 260, x1 = 1660;
  const y = (r: number) => 360 + (r - 70) * 34;
  const xs = points.map((_, i) => x0 + ((x1 - x0) * i) / (points.length - 1));
  const draw = interpolate(f, [10, 30 + points.length * 30], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const d = points.map((p, i) => `${i ? 'L' : 'M'} ${xs[i]} ${y(p[1])}`).join(' ');
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', top: 120, left: 160, opacity: s}}>
        <Kicker>Henley Passport Index · 2026</Kicker>
        <div style={{marginTop: 12}}><H size={56}>O‘zbekiston pasportining o‘rni</H></div>
      </div>
      <svg width="1920" height="1080" style={{position: 'absolute'}}>
        <path d={d} stroke={C.gold} strokeWidth="6" fill="none" strokeDasharray="3000" strokeDashoffset={3000 * (1 - draw)} />
        {points.map((p, i) => {
          const sp = spring({frame: f - 14 - i * 30, fps, config: {damping: 14}});
          return (
            <g key={i} opacity={sp}>
              <circle cx={xs[i]} cy={y(p[1])} r={18 * sp} fill={i === points.length - 1 ? C.red : C.gold} />
              <text x={xs[i]} y={y(p[1]) - 50} fill={C.ink} fontFamily="Montserrat" fontWeight="800" fontSize="76" textAnchor="middle">{p[1]}</text>
              <text x={xs[i]} y={850} fill={C.dim} fontFamily="Inter" fontSize="32" textAnchor="middle">{p[0]}</text>
            </g>
          );
        })}
      </svg>
      <div style={{position: 'absolute', bottom: 150, left: 160, fontFamily: BODY, fontSize: 24, color: C.dim}}>O‘rin raqami qancha kichik bo‘lsa, pasport shuncha kuchli</div>
    </AbsoluteFill>
  );
};

/* ---- Generic left-to-right process ---- */
export const Flow: React.FC<{steps: string[]}> = ({steps}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
      <div style={{position: 'absolute', top: 200, textAlign: 'center'}}>
        <Kicker>Vizasiz rejim — umumiy tartib</Kicker>
      </div>
      <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
        {steps.map((st, i) => {
          const s = spring({frame: f - 8 - i * 24, fps, config: {damping: 200}});
          return (
            <React.Fragment key={i}>
              <div style={{width: 330, height: 170, borderRadius: 10, background: 'rgba(14,29,54,0.88)', border: `2px solid ${i === steps.length - 1 ? C.gold : C.line}`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', opacity: s, transform: `translateY(${(1 - s) * 30}px)`}}>
                <div style={{fontFamily: HEAD, fontWeight: 800, color: C.gold, fontSize: 26}}>{i + 1}</div>
                <div style={{fontFamily: BODY, fontWeight: 700, fontSize: 32, color: C.ink, textAlign: 'center', padding: '6px 16px'}}>{st}</div>
              </div>
              {i < steps.length - 1 ? <div style={{fontSize: 44, color: C.gold, opacity: s}}>→</div> : null}
            </React.Fragment>
          );
        })}
      </div>
      <div style={{position: 'absolute', bottom: 200, fontFamily: BODY, fontSize: 26, color: C.dim}}>Yevropa Ittifoqi qaror qabul qiladi — bitta davlatning xohishi yetarli emas</div>
    </AbsoluteFill>
  );
};

/* ---- 90 / 180 days rule ---- */
export const Calendar: React.FC = () => {
  const f = useCurrentFrame();
  const s = useS(0);
  const shown = Math.floor(interpolate(f, [15, 120], [0, 180], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
      <div style={{textAlign: 'center', opacity: s, marginBottom: 40}}>
        <Kicker>Shengen: qisqa muddatli vizasiz rejim</Kicker>
        <div style={{marginTop: 12}}><H size={70}>180 kun ichida — ko‘pi bilan 90 kun</H></div>
      </div>
      <div style={{display: 'grid', gridTemplateColumns: 'repeat(30, 34px)', gap: 8}}>
        {Array.from({length: 180}).map((_, i) => (
          <div key={i} style={{width: 34, height: 34, borderRadius: 5, background: i < shown ? (i < 90 ? C.teal : 'rgba(244,241,234,0.14)') : 'rgba(244,241,234,0.04)'}} />
        ))}
      </div>
      <div style={{display: 'flex', gap: 60, marginTop: 36, fontFamily: BODY, fontSize: 28, color: C.ink, opacity: s}}>
        <span><span style={{color: C.teal}}>■</span> bo‘lish mumkin bo‘lgan 90 kun</span>
        <span><span style={{color: C.dim}}>■</span> qolgan 90 kun</span>
      </div>
    </AbsoluteFill>
  );
};

/* ---- KZ vs UZ table ---- */
export const Compare: React.FC<{rows: string[][]; cols: string[]}> = ({rows, cols}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = useS(0);
  return (
    <Center pad={200}>
      <div style={{opacity: s, marginBottom: 40}}>
        <Kicker>Qo‘shnilar, lekin shartlar har xil</Kicker>
        <div style={{marginTop: 12}}><H size={56}>Yo‘nalishga qarab farq</H></div>
      </div>
      <div style={{display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', border: `1px solid ${C.line}`, borderRadius: 10, overflow: 'hidden'}}>
        {cols.map((c, i) => (
          <div key={i} style={{padding: '22px 26px', background: 'rgba(242,193,78,0.12)', fontFamily: HEAD, fontWeight: 800, fontSize: 34, color: C.gold}}>{c}</div>
        ))}
        {rows.map((r, ri) =>
          r.map((c, ci) => {
            const sp = spring({frame: f - 14 - ri * 40 - ci * 8, fps, config: {damping: 200}});
            return (
              <div key={`${ri}-${ci}`} style={{padding: '30px 26px', borderTop: `1px solid ${C.line}`, background: 'rgba(14,29,54,0.82)', fontFamily: BODY, fontWeight: ci ? 600 : 500, fontSize: 34, color: ci === 0 ? C.dim : C.ink, opacity: sp}}>{c}</div>
            );
          }),
        )}
      </div>
    </Center>
  );
};

/* ---- Recap of the four factors ---- */
export const Recap: React.FC<{items: string[]}> = ({items}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = useS(0);
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
      <div style={{textAlign: 'center', opacity: s, marginBottom: 60}}>
        <Kicker>Xulosa</Kicker>
        <div style={{marginTop: 12}}><H size={66}>Yagona sabab yo‘q</H></div>
      </div>
      <div style={{display: 'flex', gap: 28}}>
        {items.map((it, i) => {
          const sp = spring({frame: f - 20 - i * 22, fps, config: {damping: 15}});
          return (
            <div key={i} style={{width: 340, height: 260, borderRadius: 12, background: 'rgba(14,29,54,0.88)', border: `1px solid ${C.line}`, borderBottom: `4px solid ${C.gold}`, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', opacity: sp, transform: `scale(${0.85 + 0.15 * sp})`}}>
              <div style={{fontFamily: HEAD, fontWeight: 900, fontSize: 64, color: C.gold}}>{i + 1}</div>
              <div style={{fontFamily: BODY, fontWeight: 700, fontSize: 32, color: C.ink, textAlign: 'center', padding: '10px 20px'}}>{it}</div>
            </div>
          );
        })}
      </div>
      <div style={{marginTop: 50, fontFamily: BODY, fontSize: 30, color: C.dim, opacity: interpolate(f, [120, 150], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}}>
        Bu omillar birgalikda ta’sir qiladi
      </div>
    </AbsoluteFill>
  );
};

/* ---- Viewer question ---- */
export const Cta: React.FC<{text: string}> = ({text}) => {
  const s = useS(0, 16);
  const s2 = useS(30);
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', textAlign: 'center', padding: '0 220px'}}>
      <div style={{opacity: s, transform: `translateY(${(1 - s) * 30}px)`}}>
        <Kicker>Sizning fikringiz</Kicker>
        <div style={{marginTop: 24}}><H size={62}>{text}</H></div>
      </div>
      <div style={{marginTop: 50, display: 'flex', alignItems: 'center', gap: 16, padding: '18px 30px', borderRadius: 40, background: C.gold, color: C.navy, fontFamily: BODY, fontWeight: 800, fontSize: 30, opacity: s2, transform: `scale(${0.9 + 0.1 * s2})`}}>
        💬 Izohlarda yozib qoldiring
      </div>
    </AbsoluteFill>
  );
};

/* ---- Two real clips side by side ---- */
export const SplitClips: React.FC<{left: [string, number]; right: [string, number]; leftLabel: string; rightLabel: string; dur: number; seed: number}> = ({left, right, leftLabel, rightLabel, dur, seed}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: f, fps, config: {damping: 200}});
  const panel = (src: [string, number], label: string, side: 0 | 1, col: string) => (
    <div style={{position: 'absolute', top: 0, bottom: 0, left: side ? 966 : 0, width: 954, overflow: 'hidden', transform: `translateX(${(1 - s) * (side ? 120 : -120)}px)`}}>
      <ClipLayer src={src} dur={dur} seed={seed + side} />
      <div style={{position: 'absolute', top: 60, left: 50, padding: '12px 22px', background: 'rgba(7,16,31,0.82)', borderLeft: `5px solid ${col}`, fontFamily: HEAD, fontWeight: 800, fontSize: 36, color: C.ink}}>{label}</div>
      <div style={{position: 'absolute', bottom: 30, left: 30, fontFamily: BODY, fontSize: 17, color: C.ink, background: 'rgba(7,16,31,0.7)', padding: '5px 10px', borderRadius: 3}}>{sourceLabel(src[0])}</div>
    </div>
  );
  return (
    <AbsoluteFill style={{background: C.navy}}>
      {panel(left, leftLabel, 0, C.teal)}
      {panel(right, rightLabel, 1, C.gold)}
    </AbsoluteFill>
  );
};

/* ---- Footage credits roll ---- */
export const Credits: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const M = metaJson as Record<string, {channel: string; title: string; label: string}>;
  const names = Array.from(new Set(Object.values(M).map((m) => m.label.replace(/^Manba: /, '').replace(/ \/ YouTube$/, '').replace(/ · arxiv.*$/, '')))).sort();
  const y = interpolate(f, [30, dur - 20], [0, -Math.max(0, names.length * 58 - 560)], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const s = interpolate(f, [0, 20], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: C.navy, opacity: s}}>
      <div style={{position: 'absolute', left: 160, top: 120, width: 640}}>
        <Kicker>Footage sources</Kicker>
        <div style={{marginTop: 14}}><H size={74}>Video manbalari</H></div>
        <div style={{marginTop: 34, fontFamily: BODY, fontSize: 26, lineHeight: 1.5, color: C.dim}}>
          Barcha arxiv kadrlari YouTube’dagi asl kanallardan qisqa parchalar sifatida, sharh va tahlil maqsadida olingan. Har bir kadr ustida manba ko‘rsatildi. To‘liq havolalar — video tavsifida.
        </div>
        <div style={{marginTop: 40, fontFamily: BODY, fontSize: 24, color: C.dim}}>Ovoz: muallifning asl ovozi · Musiqa va effektlar: original</div>
      </div>
      <div style={{position: 'absolute', left: 980, top: 140, height: 800, overflow: 'hidden', width: 800, maskImage: 'linear-gradient(transparent, #000 8%, #000 92%, transparent)'}}>
        <div style={{transform: `translateY(${y}px)`}}>
          {names.map((n) => (
            <div key={n} style={{fontFamily: HEAD, fontWeight: 700, fontSize: 36, color: C.ink, height: 58}}>
              {n} <span style={{color: C.gold, fontFamily: BODY, fontWeight: 500, fontSize: 24}}>/ YouTube</span>
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};
