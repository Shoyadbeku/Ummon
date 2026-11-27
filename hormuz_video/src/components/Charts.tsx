import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {C, F, inOut, appear, ease} from './theme';

type P = {dur: number; props: any};
const s2f = (s: number) => Math.round(s * 30);

/* ============ KEMALAR HARAKATI (59.0–77.3) ============
   Raqamlar ovozdagi maʼlumotlardan: urushdan oldin kuniga 125–140;
   noyabr boshidagi 1 hafta — 226; 17–23-noyabr — 125; qisqarish >40% */
export const TrafficChart: React.FC<P> = ({dur}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 10, 10);
  const st1 = appear(f, 0, 12);
  const st2 = appear(f, s2f(5.0), 14); // 64.0
  const st3 = appear(f, s2f(9.4), 14); // 68.4
  const st4 = appear(f, s2f(13.9), 12); // 72.9
  const maxH = 470;
  const h1 = maxH * st2;
  const h2 = maxH * (125 / 226) * st3;
  const pct = Math.round(interpolate(f, [s2f(13.9), s2f(15.2)], [0, 44.7], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
  return (
    <AbsoluteFill style={{opacity: o}}>
      <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(90deg, rgba(3,7,14,0.15) 0%, rgba(3,7,14,0.88) 55%)'}} />
      {/* 1-bosqich: urushdan oldin */}
      <div style={{position: 'absolute', right: 110, top: 140, width: 820, opacity: st1 * (1 - st2)}}>
        <div style={{display: 'inline-block', background: C.red, fontFamily: F.head, fontWeight: 700, fontSize: 28, letterSpacing: 3, color: '#fff', padding: '6px 16px'}}>URUSHDAN OLDIN</div>
        <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 96, color: '#fff', lineHeight: 1.05, marginTop: 10}}>125–140 <span style={{fontSize: 52, fontWeight: 500}}>kema / kuniga</span></div>
        <div style={{fontFamily: F.body, fontWeight: 600, fontSize: 28, color: C.grey}}>Ormuz boʻgʻozidan har kuni oʻtgan kemalar</div>
      </div>
      {/* 2–3-bosqich: haftalik ustunlar */}
      <div style={{position: 'absolute', right: 160, bottom: 200, width: 760, height: 640, opacity: st2}}>
        <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 3, background: C.line}} />
        {[{h: h1, v: 226, lab: 'Noyabr boshi', sub: '1 hafta', col: C.grey, a: st2, x: 60}, {h: h2, v: 125, lab: '17–23-noyabr', sub: '1 hafta', col: C.red, a: st3, x: 420}].map((b, i) => (
          <div key={i} style={{position: 'absolute', left: b.x, bottom: 0, width: 260, opacity: b.a}}>
            <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 84, color: '#fff', textAlign: 'center', marginBottom: 8}}>{Math.round(b.v * b.a)}</div>
            <div style={{height: b.h, background: b.col, boxShadow: i ? `0 0 40px ${C.red}66` : 'none'}} />
            <div style={{position: 'absolute', top: '100%', width: '100%', textAlign: 'center', paddingTop: 12}}>
              <div style={{fontFamily: F.head, fontWeight: 500, fontSize: 36, color: '#fff'}}>{b.lab}</div>
            </div>
          </div>
        ))}
        <div style={{position: 'absolute', left: 0, right: 0, bottom: -110, textAlign: 'center', fontFamily: F.body, fontWeight: 600, fontSize: 26, color: C.grey}}>Fors koʻrfaziga kirib-chiqqan kemalar (haftalik)</div>
      </div>
      {/* 4-bosqich: foiz */}
      <div style={{position: 'absolute', left: 140, top: 160, opacity: st4, transform: `scale(${0.7 + 0.3 * st4})`, transformOrigin: 'left top'}}>
        <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 220, color: C.red, lineHeight: 1, textShadow: '0 8px 40px rgba(0,0,0,0.9)'}}>−{pct}%</div>
        <div style={{fontFamily: F.head, fontWeight: 500, fontSize: 54, color: '#fff', textShadow: '0 4px 20px rgba(0,0,0,0.9)'}}>ikki hafta ichida harakat</div>
        <div style={{fontFamily: F.body, fontWeight: 600, fontSize: 30, color: C.amber, marginTop: 6}}>«40 foizdan koʻproq qisqardi»</div>
      </div>
    </AbsoluteFill>
  );
};

/* ============ XRONOLOGIYA (79.6–120.3) ============ */
const MILESTONES = [
  {t: 0.0, date: '28-FEVRAL 2026', text: 'AQSh va Isroil Eronga zarba berdi'},
  {t: 6.4, date: '28-FEVRALDAN SOʻNG', text: 'Eron mintaqa boʻylab raketa va dronlar bilan javob qaytardi'},
  {t: 14.2, date: 'APREL', text: 'AQSh Eronga qarshi dengiz blokadasini joriy qildi'},
  {t: 17.9, date: 'IYUL', text: 'Anglashuv memorandumi — blokada bekor qilindi'},
  {t: 24.5, date: 'BIR NECHA HAFTADAN SOʻNG', text: 'Kelishuv barbod boʻldi, blokada qayta tiklandi'},
  {t: 33.6, date: 'HOZIR', text: 'Tehron Ormuz orqali javob bermoqda'},
];
export const Timeline: React.FC<P> = ({dur}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 10, 10);
  let cur = 0;
  MILESTONES.forEach((m, i) => { if (f >= s2f(m.t)) cur = i; });
  const m = MILESTONES[cur];
  const ca = appear(f, s2f(m.t), 10);
  const W = 1500, x0 = 210;
  const prog = interpolate(f, MILESTONES.map((mm) => s2f(mm.t)), MILESTONES.map((_, i) => i / (MILESTONES.length - 1)), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  return (
    <AbsoluteFill style={{opacity: o}}>
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 380, background: 'linear-gradient(to top, rgba(0,0,0,0.9), rgba(0,0,0,0))'}} />
      {/* joriy bosqich */}
      <div style={{position: 'absolute', left: 110, top: 150, opacity: ca, transform: `translateY(${(1 - ca) * 20}px)`}}>
        <div style={{display: 'inline-block', background: C.red, fontFamily: F.head, fontWeight: 700, fontSize: 56, color: '#fff', padding: '4px 20px', letterSpacing: 2}}>{m.date}</div>
        <div style={{background: C.panel, fontFamily: F.head, fontWeight: 500, fontSize: 46, color: '#fff', padding: '10px 20px', maxWidth: 1000}}>{m.text}</div>
      </div>
      {/* chiziq */}
      <div style={{position: 'absolute', left: x0, width: W, bottom: 150, height: 4, background: 'rgba(255,255,255,0.25)'}} />
      <div style={{position: 'absolute', left: x0, width: W * prog, bottom: 150, height: 4, background: C.red}} />
      {MILESTONES.map((mm, i) => {
        const x = x0 + (W * i) / (MILESTONES.length - 1);
        const on = f >= s2f(mm.t);
        return (
          <div key={i} style={{position: 'absolute', left: x - 13, bottom: 138}}>
            <div style={{width: 26, height: 26, borderRadius: 13, background: on ? C.red : '#33404f', border: '4px solid #fff', boxShadow: i === cur ? `0 0 0 10px ${C.red}55` : 'none'}} />
            <div style={{position: 'absolute', top: 40, left: -120, width: 266, textAlign: 'center', fontFamily: F.head, fontWeight: on ? 700 : 500, fontSize: 26, color: on ? '#fff' : '#8592a3', letterSpacing: 1}}>{mm.date}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

/* ============ NEFT NARXI (180.4–192.2) ============
   Faqat ovozda aytilgan nuqtalar: oktabrda har kuni > $100, oktabr oxiri $114,
   24-noyabr ~$88 (3 oydagi eng past koʻrsatkichlardan biri), 27-noyabr $96–97 */
export const OilChart: React.FC<P> = ({dur}) => {
  const f = useCurrentFrame();
  const o = inOut(f, dur, 10, 10);
  const X0 = 260, X1 = 1680, Y0 = 880, Y1 = 340; // px
  const yv = (v: number) => Y0 - ((v - 80) / (120 - 80)) * (Y0 - Y1);
  // vaqt o‘qi: 1-okt .. 30-noy (61 kun)
  const xd = (d: number) => X0 + (d / 60) * (X1 - X0);
  const pts = [{d: 30, v: 114, lab: '$114', sub: 'Oktabr oxiri', t: 1.2}, {d: 54, v: 88, lab: '~$88', sub: '24-noyabr', t: 3.4}, {d: 57, v: 96.5, lab: '$96–97', sub: '27-noyabr (bugun)', t: 8.4}];
  const lineP = (k: number) => appear(f, s2f(pts[k].t), 18);
  return (
    <AbsoluteFill style={{opacity: o, background: `linear-gradient(160deg, ${C.navy} 0%, #050a12 100%)`}}>
      <div style={{position: 'absolute', left: 110, top: 80}}>
        <div style={{display: 'inline-block', background: C.red, fontFamily: F.head, fontWeight: 700, fontSize: 30, letterSpacing: 3, color: '#fff', padding: '6px 16px'}}>BRENT NEFTI</div>
        <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 70, color: '#fff', marginTop: 8}}>1 barrel narxi, AQSh dollari</div>
      </div>
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        {/* to‘r */}
        {[80, 90, 100, 110, 120].map((v) => (
          <g key={v}>
            <line x1={X0} x2={X1} y1={yv(v)} y2={yv(v)} stroke={v === 100 ? 'rgba(255,178,26,0.7)' : 'rgba(255,255,255,0.12)'} strokeWidth={v === 100 ? 3 : 2} strokeDasharray={v === 100 ? '10 8' : undefined} />
            <text x={X0 - 24} y={yv(v) + 10} fill={v === 100 ? C.amber : '#8592a3'} fontFamily="Oswald" fontSize={30} textAnchor="end">${v}</text>
          </g>
        ))}
        {/* oktabr zonasi */}
        <g opacity={appear(f, 0, 14)}>
          <rect x={xd(0)} y={yv(120)} width={xd(31) - xd(0)} height={yv(100) - yv(120)} fill="rgba(227,18,27,0.16)" />
          <text x={(xd(0) + xd(31)) / 2} y={yv(117)} fill="#fff" fontFamily="Oswald" fontSize={34} textAnchor="middle">OKTABR: har kuni $100 dan qimmat</text>
        </g>
        {/* nuqtalarni tutashtiruvchi chiziq (faqat maʼlum nuqtalar) */}
        {pts.slice(1).map((p, i) => {
          const a = pts[i];
          const k = lineP(i + 1);
          const x2 = a.d + (p.d - a.d) * k, v2 = a.v + (p.v - a.v) * k;
          return <line key={i} x1={xd(a.d)} y1={yv(a.v)} x2={xd(x2)} y2={yv(v2)} stroke={i === 1 ? C.red : '#fff'} strokeWidth={6} strokeDasharray={i === 0 ? '14 10' : undefined} strokeLinecap="round" />;
        })}
        {pts.map((p, i) => {
          const a = appear(f, s2f(p.t) + (i ? 14 : 0), 10);
          const up = i !== 1;
          return (
            <g key={i} opacity={a}>
              <circle cx={xd(p.d)} cy={yv(p.v)} r={14} fill={i === 2 ? C.red : '#fff'} stroke="#000" strokeWidth={3} />
              <text x={xd(p.d) + (i === 2 ? 30 : 0)} y={yv(p.v) + (up ? -40 : 70)} fill="#fff" fontFamily="Oswald" fontWeight={700} fontSize={64} textAnchor={i === 2 ? 'start' : 'middle'}>{p.lab}</text>
              <text x={xd(p.d) + (i === 2 ? 30 : 0)} y={yv(p.v) + (up ? -96 : 108)} fill={C.amber} fontFamily="Inter" fontWeight={600} fontSize={28} textAnchor={i === 2 ? 'start' : 'middle'}>{p.sub}</text>
            </g>
          );
        })}
        {/* o‘q yorliqlari */}
        <text x={xd(15)} y={Y0 + 60} fill="#8592a3" fontFamily="Oswald" fontSize={32} textAnchor="middle">OKTABR</text>
        <text x={xd(45)} y={Y0 + 60} fill="#8592a3" fontFamily="Oswald" fontSize={32} textAnchor="middle">NOYABR</text>
        <line x1={xd(31)} x2={xd(31)} y1={Y0} y2={Y0 + 20} stroke="#8592a3" strokeWidth={2} />
      </svg>
      <div style={{position: 'absolute', left: 260, bottom: 60, fontFamily: F.body, fontWeight: 400, fontSize: 24, color: '#8592a3'}}>Sxematik grafik: faqat reportajda keltirilgan qiymatlar koʻrsatilgan; oraliq kunlar chizilmagan.</div>
    </AbsoluteFill>
  );
};
