import React, {useMemo} from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {geoMercator, geoPath, geoInterpolate} from 'd3-geo';
import {feature} from 'topojson-client';
import world from 'world-atlas/countries-50m.json';
import {C, F, inOut, appear, ease} from './theme';

type P = {dur: number; props: any};
const s2f = (s: number) => Math.round(s * 30);
// Natural Earth / world-atlas: ISO 3166-1 raqamli kodlar
const ID = {UZB: '860', IRN: '364', TKM: '795', KWT: '414', SAU: '682', BHR: '048', QAT: '634', ARE: '784', OMN: '512', AFG: '004', IRQ: '368', KAZ: '398', TJK: '762', KGZ: '417', PAK: '586'};
const countries: any = (feature(world as any, (world as any).objects.countries) as any).features;
const byId = (id: string) => countries.find((c: any) => c.id === id);

const useProj = (bounds: [[number, number], [number, number]], pad = 60) =>
  useMemo(() => {
    const box = {type: 'Feature', geometry: {type: 'MultiPoint', coordinates: bounds}} as any;
    const pr = geoMercator().fitExtent([[pad, pad], [1920 - pad, 1080 - pad]], box);
    return {pr, path: geoPath(pr)};
  }, []);

const Base: React.FC<{path: any; fills?: Record<string, string>; strokes?: Record<string, string>}> = ({path, fills = {}, strokes = {}}) => (
  <g>
    {countries.map((c: any) => (
      <path key={c.id + (c.properties?.name || '')} d={path(c) || ''} fill={fills[c.id] || '#1c2a3f'} stroke={strokes[c.id] || 'rgba(255,255,255,0.28)'} strokeWidth={strokes[c.id] ? 3 : 1.2} />
    ))}
  </g>
);
const Label: React.FC<{x: number; y: number; text: string; size?: number; color?: string; o?: number; weight?: number}> = ({x, y, text, size = 34, color = '#fff', o = 1, weight = 700}) => (
  <text x={x} y={y} fill={color} opacity={o} fontFamily="Oswald" fontWeight={weight} fontSize={size} textAnchor="middle" style={{paintOrder: 'stroke', stroke: 'rgba(0,0,0,0.75)', strokeWidth: 6}}>{text}</text>
);
const Pulse: React.FC<{x: number; y: number; f: number; color?: string}> = ({x, y, f, color = C.red}) => {
  const k = (f % 40) / 40;
  return (
    <g>
      <circle cx={x} cy={y} r={14 + k * 50} fill="none" stroke={color} strokeWidth={4} opacity={1 - k} />
      <circle cx={x} cy={y} r={13} fill={color} stroke="#fff" strokeWidth={4} />
    </g>
  );
};
const Title: React.FC<{f: number; kicker: string; title: string}> = ({f, kicker, title}) => (
  <div style={{position: 'absolute', left: 110, top: 80, opacity: appear(f, 0, 12)}}>
    <div style={{display: 'inline-block', background: C.red, fontFamily: F.head, fontWeight: 700, fontSize: 30, letterSpacing: 3, color: '#fff', padding: '6px 16px'}}>{kicker}</div>
    <div style={{fontFamily: F.head, fontWeight: 700, fontSize: 66, color: '#fff', marginTop: 8, textShadow: '0 4px 20px rgba(0,0,0,0.9)'}}>{title}</div>
  </div>
);
const Frame: React.FC<{children: React.ReactNode; dur: number; f: number; zoom?: [number, number]}> = ({children, dur, f, zoom = [1.0, 1.06]}) => {
  const z = interpolate(f, [0, dur], zoom);
  return (
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 40%, #0f2036 0%, #060c16 100%)', opacity: inOut(f, dur, 8, 8)}}>
      <AbsoluteFill style={{transform: `scale(${z})`}}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};
const Credit = () => (
  <div style={{position: 'absolute', right: 40, bottom: 26, fontFamily: F.body, fontSize: 20, color: 'rgba(255,255,255,0.55)'}}>XARITA: Natural Earth (public domain)</div>
);

/* ===== Oʻzbekiston → Ormuz (17.3–21.9) ===== */
export const MapUz: React.FC<P> = ({dur}) => {
  const f = useCurrentFrame();
  const {pr, path} = useProj([[40, 21], [78, 49]]);
  const T = pr([69.24, 41.31])!, H = pr([56.25, 26.57])!;
  const k = interpolate(f, [s2f(1.2), s2f(3.2)], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const ip = geoInterpolate([69.24, 41.31], [56.25, 26.57]);
  const pts = Array.from({length: 41}, (_, i) => pr(ip((i / 40) * k))!);
  const d = 'M' + pts.map((p) => p.join(',')).join('L');
  return (
    <Frame dur={dur} f={f}>
      <svg width={1920} height={1080}>
        <Base path={path} fills={{[ID.UZB]: C.navy2, [ID.IRN]: '#22324a'}} strokes={{[ID.UZB]: C.amber}} />
        <path d={path(byId(ID.UZB))} fill="rgba(255,178,26,0.25)" opacity={appear(f, 0, 12)} />
        <path d={d} fill="none" stroke={C.red} strokeWidth={6} strokeDasharray="18 12" />
        <Pulse x={T[0]} y={T[1]} f={f} color={C.amber} />
        <Label x={T[0] + 95} y={T[1] + 12} text="TOSHKENT" size={30} />
        <Label x={pr([62.0, 43.6])![0]} y={pr([62.0, 43.6])![1]} text="OʻZBEKISTON" size={46} color={C.amber} o={appear(f, 4, 10)} />
        <Label x={pr([54, 32.5])![0]} y={pr([54, 32.5])![1]} text="ERON" size={46} color="#9fb0c6" o={appear(f, 8, 10)} />
        <g opacity={appear(f, s2f(3.0), 10)}>
          <Pulse x={H[0]} y={H[1]} f={f} />
          <Label x={H[0] + 10} y={H[1] + 62} text="ORMUZ BOʻGʻOZI" color="#fff" />
        </g>
        <g opacity={appear(f, s2f(3.4), 12)}>
          <Label x={(T[0] + H[0]) / 2 + 150} y={(T[1] + H[1]) / 2 + 10} text="≈ 2 000 km" size={64} color={C.red} />
          <Label x={(T[0] + H[0]) / 2 + 150} y={(T[1] + H[1]) / 2 + 50} text="toʻgʻri chiziqda" size={28} weight={500} />
        </g>
      </svg>
      <Title f={f} kicker="XARITA" title="Ormuz boʻgʻozida nima boʻlyapti?" />
      <Credit />
    </Frame>
  );
};

/* ===== Fors ko‘rfazi: Kuvayt va hujumni qoralagan davlatlar (147.6–152.8) ===== */
export const MapGulf: React.FC<P> = ({dur}) => {
  const f = useCurrentFrame();
  const {pr, path} = useProj([[39.5, 20.5], [61.5, 33.5]], 40);
  const cond = [ID.SAU, ID.BHR, ID.QAT, ID.ARE];
  const fills: Record<string, string> = {[ID.KWT]: C.red, [ID.IRN]: '#2a3445'};
  cond.forEach((c, i) => { if (f > s2f(0.6 + i * 0.45)) fills[c] = '#8a6410'; });
  const L = (lon: number, lat: number) => pr([lon, lat])!;
  const labels: [string, number, number, number][] = [['SAUDIYA ARABISTONI', 46.5, 24.2, 0.6], ['BAHRAYN', 50.2, 26.55, 1.05], ['QATAR', 51.2, 25.0, 1.5], ['BAA', 54.3, 23.6, 1.95]];
  const K = L(47.6, 29.3);
  return (
    <Frame dur={dur} f={f} zoom={[1.04, 1.0]}>
      <svg width={1920} height={1080}>
        <Base path={path} fills={fills} />
        <Pulse x={K[0]} y={K[1]} f={f} />
        <Label x={K[0] - 90} y={K[1] + 10} text="KUVAYT" size={46} />
        {labels.map(([t, lo, la, at]) => { const p = L(lo, la); return <Label key={t} x={p[0]} y={p[1]} text={t} size={36} color={C.amber} o={appear(f, s2f(at), 8)} />; })}
        <Label x={L(53.5, 30.5)[0]} y={L(53.5, 30.5)[1]} text="ERON" size={46} color="#9fb0c6" />
        <Label x={L(53.5, 30.5)[0]} y={L(53.5, 30.5)[1] + 44} text="ayblovni rad etdi" size={30} weight={500} color="#c9d3df" o={appear(f, s2f(4.0), 10)} />
      </svg>
      <Title f={f} kicker="26-NOYABR" title="Hujumni qoralagan davlatlar" />
      <div style={{position: 'absolute', left: 110, bottom: 90, display: 'flex', gap: 30, background: 'rgba(6,12,22,0.85)', padding: '12px 20px', fontFamily: F.body, fontWeight: 600, fontSize: 26, color: '#fff'}}>
        <span><span style={{display: 'inline-block', width: 22, height: 22, background: C.red, marginRight: 10, verticalAlign: 'middle'}} />Hujum nishoni</span>
        <span><span style={{display: 'inline-block', width: 22, height: 22, background: '#8a6410', marginRight: 10, verticalAlign: 'middle'}} />Hujumni qoraladi</span>
      </div>
      <Credit />
    </Frame>
  );
};

/* ===== Janubiy yo‘l: O‘zbekiston → Turkmaniston → Eron → Bandar Abbos (218.5–224.4) ===== */
export const MapRoute: React.FC<P> = ({dur}) => {
  const f = useCurrentFrame();
  const {pr, path} = useProj([[47, 24], [76, 47.5]]);
  const route: [number, number][] = [[69.24, 41.31], [66.96, 39.65], [64.42, 39.77], [63.58, 39.07], [61.2, 37.6], [59.6, 36.3], [57.7, 33.5], [56.9, 30.3], [56.27, 27.18]];
  const k = interpolate(f, [s2f(0.3), s2f(3.6)], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const P = route.map((c) => pr(c)!);
  // umumiy uzunlik bo‘yicha qisman chizish
  const segs = P.slice(1).map((p, i) => Math.hypot(p[0] - P[i][0], p[1] - P[i][1]));
  const total = segs.reduce((a, b) => a + b, 0);
  const T = pr([69.24, 41.31])!, B = pr([56.27, 27.18])!;
  return (
    <Frame dur={dur} f={f}>
      <svg width={1920} height={1080}>
        <Base path={path} fills={{[ID.UZB]: '#5a4410', [ID.TKM]: '#26364d', [ID.IRN]: '#26364d'}} strokes={{[ID.UZB]: C.amber}} />
        <polyline points={P.map((p) => p.join(',')).join(' ')} fill="none" stroke={C.amber} strokeWidth={9} strokeLinejoin="round" strokeLinecap="round" strokeDasharray={`${total * k} ${total}`} />
        <Pulse x={T[0]} y={T[1]} f={f} color={C.amber} />
        <Label x={T[0] + 95} y={T[1] + 12} text="TOSHKENT" size={30} />
        <Label x={pr([62.5, 43.9])![0]} y={pr([62.5, 43.9])![1]} text="OʻZBEKISTON" size={44} color={C.amber} />
        <Label x={pr([59.0, 39.6])![0]} y={pr([59.0, 39.6])![1]} text="TURKMANISTON" size={36} color="#9fb0c6" />
        <Label x={pr([54.0, 32.6])![0]} y={pr([54.0, 32.6])![1]} text="ERON" size={44} color="#9fb0c6" />
        <g opacity={appear(f, s2f(3.4), 10)}>
          <Pulse x={B[0]} y={B[1]} f={f} />
          <Label x={B[0] - 40} y={B[1] + 64} text="BANDAR ABBOS PORTI" size={38} />
        </g>
        <g opacity={appear(f, s2f(4.0), 12)}>
          <rect x={B[0] + 70} y={B[1] - 230} width={520} height={190} fill="rgba(9,16,28,0.9)" stroke={C.red} strokeWidth={4} />
          <text x={B[0] + 100} y={B[1] - 120} fill="#fff" fontFamily="Oswald" fontWeight={700} fontSize={110}>~90%</text>
          <text x={B[0] + 100} y={B[1] - 70} fill={C.amber} fontFamily="Inter" fontWeight={600} fontSize={26}>Eron orqali tashiladigan yuklarimiz</text>
        </g>
      </svg>
      <Title f={f} kicker="JANUBIY YOʻL" title="Dengizga chiqish yoʻli boʻlmagan Oʻzbekiston" />
      <div style={{position: 'absolute', left: 110, bottom: 60, fontFamily: F.body, fontSize: 22, color: 'rgba(255,255,255,0.6)'}}>Yoʻnalish chizigʻi taxminiy (sxematik).</div>
      <Credit />
    </Frame>
  );
};
