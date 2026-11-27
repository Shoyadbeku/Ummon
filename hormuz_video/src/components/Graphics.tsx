import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, random} from 'remotion';
import {C, F, inOut, appear, ease} from './theme';

type P = {dur: number; props: any};
const s2f = (s: number) => Math.round(s * 30);

/* ---------- umumiy bo‘laklar ---------- */
const Arrow: React.FC<{dir?: 'up' | 'right' | 'down'; color?: string; size?: number}> = ({dir = 'up', color = C.red, size = 40}) => {
  const rot = dir === 'up' ? 0 : dir === 'right' ? 90 : 180;
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" style={{transform: `rotate(${rot}deg)`}}>
      <path d="M20 4 L34 20 H25 V36 H15 V20 H6 Z" fill={color} />
    </svg>
  );
};
const Tag: React.FC<{children: React.ReactNode; bg?: string; color?: string}> = ({children, bg = C.red, color = '#fff'}) => (
  <div style={{display: 'inline-block', background: bg, color, fontFamily: F.head, fontWeight: 700, fontSize: 26, letterSpacing: 3, padding: '6px 16px', textTransform: 'uppercase'}}>{children}</div>
);

/* ---------- HOOK SARLAVHASI ---------- */
export const HookTitle: React.FC<P> = ({dur, props}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 6, 8);
  const sc = interpolate(f, [0, 14], [1.25, 1], {extrapolateRight: 'clamp', easing: ease});
  const glitch = f < 10 ? (random(f) - 0.5) * 18 : 0;
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', opacity: o}}>
      <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at center, rgba(0,0,0,0.0) 30%, rgba(0,0,0,0.55) 100%)'}} />
      <div style={{textAlign: 'center', transform: `scale(${sc}) translateX(${glitch}px)`}}>
        <div style={{opacity: appear(f, 0, 6)}}><Tag>{props.kicker}</Tag></div>
        <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 150, color: '#fff', lineHeight: 1.05, marginTop: 14, textShadow: '0 6px 40px rgba(0,0,0,0.8)', letterSpacing: 2}}>{props.title}</div>
        <div style={{height: 6, background: C.red, margin: '10px auto 16px', width: interpolate(f, [6, 22], [0, 820], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease})}} />
        <div style={{fontFamily: F.body, fontWeight: 600, fontSize: 44, color: '#fff', opacity: appear(f, 10, 10), textShadow: '0 3px 20px rgba(0,0,0,0.9)'}}>{props.sub}</div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- LOWER THIRD ---------- */
export const LowerThird: React.FC<P> = ({dur, props}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 12, 8);
  const w = interpolate(f, [0, 14], [0, 1], {extrapolateRight: 'clamp', easing: ease});
  return (
    <AbsoluteFill style={{opacity: o}}>
      <div style={{position: 'absolute', left: 110, bottom: 120, display: 'flex', alignItems: 'stretch'}}>
        <div style={{width: 12, background: C.red}} />
        <div style={{background: C.panel, padding: '16px 34px 18px 26px', clipPath: `inset(0 ${(1 - w) * 100}% 0 0)`, backdropFilter: 'blur(6px)'}}>
          <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 50, color: '#fff', letterSpacing: 1, lineHeight: 1.1}}>{props.name}</div>
          <div style={{fontFamily: F.body, fontWeight: 600, fontSize: 28, color: C.amber, marginTop: 6, opacity: appear(f, 8, 10)}}>{props.role}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- SANA MUHRI ---------- */
export const DateStamp: React.FC<P> = ({dur, props}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 10, 8);
  return (
    <AbsoluteFill style={{opacity: o}}>
      <div style={{position: 'absolute', left: 110, top: 150, transform: `translateX(${(1 - appear(f, 0, 12)) * -60}px)`}}>
        <div style={{background: C.red, color: '#fff', fontFamily: F.head, fontWeight: 700, fontSize: 58, padding: '6px 22px', letterSpacing: 2}}>{props.date}</div>
        <div style={{background: C.panel, color: '#fff', fontFamily: F.body, fontWeight: 600, fontSize: 30, padding: '8px 22px', display: 'inline-block'}}>{props.text}</div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- JOY ---------- */
export const Location: React.FC<P> = ({dur, props}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 10, 8);
  return (
    <AbsoluteFill style={{opacity: o}}>
      <div style={{position: 'absolute', left: 110, top: 150, display: 'flex', alignItems: 'center', gap: 16, background: C.panel, padding: '14px 26px'}}>
        <svg width="44" height="56" viewBox="0 0 24 30"><path d="M12 0C5.4 0 0 5.2 0 11.7 0 20.5 12 30 12 30s12-9.5 12-18.3C24 5.2 18.6 0 12 0z" fill={C.red} /><circle cx="12" cy="11.5" r="4.5" fill="#fff" /></svg>
        <div>
          <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 46, color: '#fff'}}>{props.place}</div>
          <div style={{fontFamily: F.body, fontWeight: 600, fontSize: 26, color: C.grey}}>{props.region}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- OGOHLANTIRISH (tasdiqlanmagan) ---------- */
export const Warning: React.FC<P> = ({dur, props}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 10, 8);
  const blink = 0.75 + 0.25 * Math.sin(f / 4);
  return (
    <AbsoluteFill style={{opacity: o}}>
      <div style={{position: 'absolute', left: 110, top: 150, maxWidth: 900, display: 'flex', gap: 22, alignItems: 'center', background: 'rgba(20,14,0,0.88)', border: `3px solid ${C.amber}`, padding: '18px 28px', transform: `translateY(${(1 - appear(f, 0, 12)) * -30}px)`}}>
        <svg width="70" height="62" viewBox="0 0 70 62" style={{opacity: blink, flexShrink: 0}}><path d="M35 2 L68 60 H2 Z" fill={C.amber} /><rect x="32" y="20" width="6" height="22" fill="#111" /><rect x="32" y="47" width="6" height="6" fill="#111" /></svg>
        <div>
          <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 44, color: C.amber, letterSpacing: 3}}>{props.title}</div>
          <div style={{fontFamily: F.body, fontWeight: 600, fontSize: 30, color: '#fff', marginTop: 4, lineHeight: 1.3}}>{props.text}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- KATTA RAQAM (hisoblagich) ---------- */
export const BigNumber: React.FC<P> = ({dur, props}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 10, 8);
  const v = Math.round(interpolate(f, [4, 40], [0, props.value], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease}));
  return (
    <AbsoluteFill style={{opacity: o}}>
      <div style={{position: 'absolute', right: 110, top: 170, background: C.panel, padding: '24px 40px 28px', borderTop: `8px solid ${C.red}`, minWidth: 560}}>
        <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 190, color: '#fff', lineHeight: 1}}>{v}<span style={{color: C.red}}>{props.suffix}</span></div>
        <div style={{fontFamily: F.head, fontWeight: 500, fontSize: 48, color: '#fff', textTransform: 'uppercase', letterSpacing: 1}}>{props.label}</div>
        <div style={{fontFamily: F.body, fontWeight: 600, fontSize: 26, color: C.grey, marginTop: 10}}>{props.note}</div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- STAT QATORI ---------- */
export const StatLine: React.FC<P> = ({dur, props}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 10, 8);
  return (
    <AbsoluteFill style={{opacity: o}}>
      <div style={{position: 'absolute', left: 110, top: 170, display: 'flex', alignItems: 'center', gap: 26, background: C.panel, padding: '18px 36px', borderLeft: `10px solid ${C.red}`}}>
        <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 150, color: '#fff', lineHeight: 1}}>{props.value}</div>
        <div>
          <div style={{fontFamily: F.head, fontWeight: 500, fontSize: 50, color: '#fff', maxWidth: 640, lineHeight: 1.1}}>{props.text}</div>
          <div style={{fontFamily: F.body, fontWeight: 600, fontSize: 26, color: C.amber, marginTop: 8}}>{props.note}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- NARX YORLIG‘I ---------- */
export const PriceTag: React.FC<P> = ({dur, props}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 10, 8);
  return (
    <AbsoluteFill style={{opacity: o}}>
      <div style={{position: 'absolute', right: 110, top: 170, background: C.panel, padding: '20px 34px', borderTop: `8px solid ${C.red}`, transform: `translateX(${(1 - appear(f, 0, 12)) * 80}px)`}}>
        <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 34, color: C.amber, letterSpacing: 4}}>{props.label}</div>
        <div style={{display: 'flex', alignItems: 'center', gap: 18, marginTop: 6}}>
          {props.from ? <div style={{fontFamily: F.head, fontWeight: 500, fontSize: 70, color: C.grey}}>{props.from}</div> : null}
          {props.from ? <Arrow dir="right" color={C.red} size={48} /> : <Arrow dir="up" color={C.red} size={56} />}
          <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 96, color: '#fff', opacity: appear(f, 8, 10)}}>{props.to}</div>
        </div>
        <div style={{fontFamily: F.body, fontWeight: 600, fontSize: 26, color: C.grey}}>{props.note}</div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- SARLAVHA KARTASI ---------- */
export const TitleCard: React.FC<P> = ({dur, props}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 6, 6);
  const ls = interpolate(f, [0, dur], [18, 6]);
  return (
    <AbsoluteFill style={{opacity: o, justifyContent: 'center', alignItems: 'center', background: 'rgba(5,10,20,0.55)'}}>
      <div style={{textAlign: 'center'}}>
        <div style={{height: 4, background: C.red, width: 900, margin: '0 auto 22px', transform: `scaleX(${appear(f, 0, 12)})`}} />
        <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 160, color: '#fff', letterSpacing: ls, lineHeight: 1}}>{props.title}</div>
        <div style={{fontFamily: F.body, fontWeight: 600, fontSize: 44, color: C.amber, marginTop: 18, opacity: appear(f, 8, 10)}}>{props.sub}</div>
        <div style={{height: 4, background: C.red, width: 900, margin: '22px auto 0', transform: `scaleX(${appear(f, 0, 12)})`}} />
      </div>
    </AbsoluteFill>
  );
};

/* ---------- KINETIK MATN ---------- */
export const Kinetic: React.FC<P> = ({dur, props}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 4, 8);
  const words: string[] = props.text.split(' ');
  return (
    <AbsoluteFill style={{opacity: o, justifyContent: 'center', alignItems: 'center', background: 'rgba(0,0,0,0.35)'}}>
      <div style={{display: 'flex', gap: 28, flexWrap: 'wrap', justifyContent: 'center', maxWidth: 1600}}>
        {words.map((w, i) => (
          <span key={i} style={{fontFamily: F.head, fontWeight: 700, fontSize: 130, color: i === words.length - 1 ? C.red : '#fff', opacity: appear(f, i * 5, 8), transform: `translateY(${(1 - appear(f, i * 5, 10)) * 60}px)`, display: 'inline-block', textShadow: '0 6px 30px rgba(0,0,0,0.8)'}}>{w}</span>
        ))}
      </div>
    </AbsoluteFill>
  );
};

/* ---------- IQTIBOS ---------- */
export const Quote: React.FC<P> = ({dur, props}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 10, 8);
  return (
    <AbsoluteFill style={{opacity: o}}>
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 560, background: 'linear-gradient(to top, rgba(0,0,0,0.92), rgba(0,0,0,0))'}} />
      <div style={{position: 'absolute', left: 160, right: 160, bottom: 130, display: 'flex', gap: 26}}>
        <svg width="90" height="80" viewBox="0 0 90 80" style={{flexShrink: 0}}><path d="M0 80V44C0 18 14 3 38 0l4 10C28 14 21 24 21 36h17v44zm50 0V44C50 18 64 3 88 0l2 10C78 14 71 24 71 36h17v44z" fill={C.red} /></svg>
        <div>
          <div style={{fontFamily: F.head, fontWeight: 500, fontSize: 62, color: '#fff', lineHeight: 1.18, textShadow: '0 4px 20px rgba(0,0,0,0.9)'}}>{props.text}</div>
          <div style={{fontFamily: F.body, fontWeight: 600, fontSize: 30, color: C.amber, marginTop: 16, opacity: appear(f, 10, 10)}}>— {props.who}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- MANBA KARTASI ---------- */
export const SourceCard: React.FC<P> = ({dur, props}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 10, 8);
  return (
    <AbsoluteFill style={{opacity: o, background: 'rgba(4,8,16,0.55)'}}>
      <div style={{position: 'absolute', left: 160, top: 300, maxWidth: 1250}}>
        <Tag>{props.kicker}</Tag>
        <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 96, color: '#fff', lineHeight: 1.08, marginTop: 20, opacity: appear(f, 4, 12), textShadow: '0 6px 30px rgba(0,0,0,0.8)'}}>{props.title}</div>
        <div style={{fontFamily: F.body, fontWeight: 600, fontSize: 34, color: C.amber, marginTop: 20, opacity: appear(f, 12, 10)}}>{props.source}</div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- RO‘YXAT KARTALARI (talablar / 3 yo‘nalish / ssenariylar / xulosa) ---------- */
const ListCards: React.FC<{dur: number; header: string; items: {t: number; text: string; icon?: string}[]; side?: 'left' | 'right' | 'center'; numbered?: boolean; dim?: number; footer?: {t: number; text: string}}> = ({dur, header, items, side = 'right', numbered = true, dim = 0.45, footer}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 10, 10);
  const pos: React.CSSProperties = side === 'right' ? {right: 110, top: 150, width: 820} : side === 'left' ? {left: 110, top: 150, width: 820} : {left: 260, right: 260, top: 200};
  return (
    <AbsoluteFill style={{opacity: o, background: `rgba(3,7,14,${dim})`}}>
      <div style={{position: 'absolute', ...pos}}>
        <Tag>{header}</Tag>
        <div style={{marginTop: 22, display: 'flex', flexDirection: 'column', gap: 18}}>
          {items.map((it, i) => {
            const a = appear(f, s2f(it.t), 12);
            return (
              <div key={i} style={{display: 'flex', alignItems: 'center', gap: 24, background: C.panel, padding: '20px 28px', borderLeft: `8px solid ${i % 2 ? C.amber : C.red}`, opacity: a, transform: `translateX(${(1 - a) * (side === 'left' ? -80 : 80)}px)`}}>
                {numbered ? <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 72, color: i % 2 ? C.amber : C.red, width: 60, textAlign: 'center'}}>{i + 1}</div> : null}
                <div style={{fontFamily: F.head, fontWeight: 500, fontSize: 50, color: '#fff', lineHeight: 1.15}}>{it.text}</div>
              </div>
            );
          })}
        </div>
        {footer ? <div style={{marginTop: 26, opacity: appear(f, s2f(footer.t), 10), fontFamily: F.head, fontWeight: 700, fontSize: 46, color: C.amber, letterSpacing: 2}}>{footer.text}</div> : null}
      </div>
    </AbsoluteFill>
  );
};
export const Demands: React.FC<P> = ({dur}) => (
  <ListCards dur={dur} header="Eron talablari" side="left" items={[
    {t: 1.4, text: 'Harbiy harakatlarni toʻxtatish'},
    {t: 3.0, text: 'Blokadani olib tashlash'},
    {t: 4.3, text: 'Sanksiyalarni bekor qilish'},
  ]} />
);
export const ThreeDirs: React.FC<P> = ({dur}) => (
  <ListCards dur={dur} header="Taʼsir yoʻnalishlari" side="right" items={[
    {t: 0.0, text: 'Jahon energiya narxlari'},
    {t: 1.8, text: 'Yuk tashish xarajatlari'},
    {t: 3.4, text: 'Sugʻurta'},
  ]} />
);
export const Scenarios: React.FC<P> = ({dur}) => (
  <ListCards dur={dur} header="Oldinda bir necha yoʻl" side="center" dim={0.6} items={[
    {t: 1.6, text: 'Muzokaralar qayta boshlanishi mumkin'},
    {t: 3.7, text: 'Yangi zarbalar keskinlikni oshirishi mumkin'},
    {t: 5.4, text: '«Na urush, na tinchlik» holati davom etishi mumkin'},
  ]} footer={{t: 9.6, text: 'HOZIRCHA BIRORTASI ANIQ EMAS'}} />
);
export const Recap: React.FC<P> = ({dur}) => (
  <ListCards dur={dur} header="Xulosa" side="right" numbered={false} dim={0.35} items={[
    {t: 0.0, text: 'Urush yana Ormuz boʻgʻoziga qaytdi'},
    {t: 3.8, text: 'Tankerlar minaga urilmoqda'},
    {t: 5.5, text: 'Kemalar soni keskin kamaydi'},
    {t: 8.9, text: 'Neft narxi yana koʻtarildi'},
  ]} />
);

/* ---------- ZANJIR: yoqilg‘i → yuk → narx ---------- */
export const Chain: React.FC<P> = ({dur}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 10, 10);
  const items = [{t: 0, txt: 'Yoqilgʻi'}, {t: 1.4, txt: 'Yuk tashish'}, {t: 2.9, txt: 'Import narxi'}];
  return (
    <AbsoluteFill style={{opacity: o, background: 'rgba(3,7,14,0.6)', justifyContent: 'center', alignItems: 'center'}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 30}}>
        {items.map((it, i) => {
          const a = appear(f, s2f(it.t), 12);
          return (
            <React.Fragment key={i}>
              {i > 0 ? <div style={{opacity: a}}><Arrow dir="right" color={C.grey} size={70} /></div> : null}
              <div style={{background: C.panel, padding: '30px 40px', borderTop: `8px solid ${C.red}`, textAlign: 'center', opacity: a, transform: `scale(${0.8 + 0.2 * a})`, minWidth: 380}}>
                <div style={{display: 'flex', justifyContent: 'center'}}><Arrow dir="up" color={C.red} size={80} /></div>
                <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 64, color: '#fff', marginTop: 10}}>{it.txt}</div>
                <div style={{fontFamily: F.body, fontWeight: 600, fontSize: 28, color: C.amber}}>qimmatlashadi</div>
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/* ---------- 1/5 ULUSH ---------- */
export const ShareFifth: React.FC<P> = ({dur}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 10, 10);
  return (
    <AbsoluteFill style={{opacity: o, background: 'rgba(3,7,14,0.55)'}}>
      <div style={{position: 'absolute', left: 160, top: 230}}>
        <Tag>Urushdan oldin</Tag>
        <div style={{display: 'flex', gap: 26, marginTop: 40}}>
          {[0, 1, 2, 3, 4].map((i) => {
            const a = appear(f, 6 + i * 5, 10);
            const hi = i === 0;
            return (
              <svg key={i} width="150" height="200" viewBox="0 0 60 80" style={{opacity: a, transform: `translateY(${(1 - a) * 40}px)`}}>
                <rect x="4" y="6" width="52" height="70" rx="6" fill={hi ? C.red : 'rgba(255,255,255,0.18)'} stroke={hi ? C.red : 'rgba(255,255,255,0.5)'} strokeWidth="2" />
                <rect x="4" y="24" width="52" height="4" fill="rgba(0,0,0,0.35)" /><rect x="4" y="52" width="52" height="4" fill="rgba(0,0,0,0.35)" />
              </svg>
            );
          })}
        </div>
        <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 120, color: '#fff', marginTop: 26, lineHeight: 1}}>≈ <span style={{color: C.red}}>1/5</span></div>
        <div style={{fontFamily: F.head, fontWeight: 500, fontSize: 50, color: '#fff', maxWidth: 1300, lineHeight: 1.15, opacity: appear(f, 30, 12)}}>dunyoda isteʼmol qilinadigan neftning qariyb beshdan bir qismi Ormuz orqali oʻtardi</div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- SAVOL ---------- */
export const Question: React.FC<P> = ({dur, props}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 10, 6);
  return (
    <AbsoluteFill style={{opacity: o, background: 'rgba(3,7,14,0.55)', justifyContent: 'center', alignItems: 'center'}}>
      <div style={{textAlign: 'center', maxWidth: 1500}}>
        <Tag>Sizga savol</Tag>
        <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 100, color: '#fff', lineHeight: 1.12, marginTop: 30, textShadow: '0 6px 30px rgba(0,0,0,0.8)', opacity: appear(f, 6, 14)}}>{props.text}</div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------- YAKUNIY KARTA ---------- */
export const EndCard: React.FC<P> = ({dur}) => {
  const f = useCurrentFrame();
  const o = appear(f, 0, 12);
  const fade = interpolate(f, [dur - 36, dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{opacity: o, background: 'rgba(3,7,14,0.65)', justifyContent: 'center', alignItems: 'center'}}>
      <div style={{textAlign: 'center'}}>
        <svg width="120" height="100" viewBox="0 0 24 20" style={{opacity: appear(f, 4, 10)}}><path d="M2 2h20v12H8l-5 4v-4H2z" fill="none" stroke={C.red} strokeWidth="1.8" strokeLinejoin="round" /></svg>
        <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 110, color: '#fff', marginTop: 10}}>Fikringizni izohlarda yozing</div>
        <div style={{fontFamily: F.body, fontWeight: 600, fontSize: 40, color: C.amber, marginTop: 16, opacity: appear(f, 30, 12)}}>Voqealar rivojini kuzatishda davom etamiz</div>
      </div>
      <AbsoluteFill style={{background: '#000', opacity: fade}} />
    </AbsoluteFill>
  );
};
