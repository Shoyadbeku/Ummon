import React from 'react';
import {AbsoluteFill, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, random} from 'remotion';
import sb from '../data/storyboard.json';
import {C, F, inOut, appear} from '../components/theme';
import * as G from '../components/Graphics';
import * as CH from '../components/Charts';
import * as M from '../components/Maps';

const FPS = sb.fps;
const fr = (s: number) => Math.round(s * FPS);
const XF = 8; // o‘tish (crossfade) davomiyligi, kadr

const GFX: Record<string, React.FC<any>> = {map_uz: M.MapUz, map_gulf: M.MapGulf, map_route: M.MapRoute, oil_chart: CH.OilChart};
const OV: Record<string, React.FC<any>> = {
  hook_title: G.HookTitle, lower_third: G.LowerThird, price_tag: G.PriceTag, title_card: G.TitleCard, date_stamp: G.DateStamp,
  location: G.Location, warning: G.Warning, big_number: G.BigNumber, traffic_chart: CH.TrafficChart, timeline: CH.Timeline,
  demands: G.Demands, stat_line: G.StatLine, quote: G.Quote, share_fifth: G.ShareFifth, oil_chart: () => null,
  source_card: G.SourceCard, three_dirs: G.ThreeDirs, chain: G.Chain, kinetic: G.Kinetic, scenarios: G.Scenarios,
  recap: G.Recap, question: G.Question, end_card: G.EndCard,
};

/* ---- bitta kadr: Ken Burns + kirishda crossfade ---- */
const Shot: React.FC<{s: any; idx: number; len: number; fadeIn: boolean}> = ({s, idx, len, fadeIn}) => {
  const f = useCurrentFrame();
  const r = random(s.id);
  const dir = idx % 2 === 0 ? 1 : -1;
  const z0 = 1.03 + r * 0.03, z1 = z0 + 0.05 + r * 0.03;
  const z = interpolate(f, [0, len], [z0, z1]);
  const tx = interpolate(f, [0, len], [0, dir * (10 + r * 18)]);
  const op = fadeIn ? interpolate(f, [0, XF], [0, 1], {extrapolateRight: 'clamp'}) : 1;
  if (s.src === 'GFX') {
    const Comp = GFX[s.mode];
    return <AbsoluteFill style={{opacity: op}}><Comp dur={len} props={{}} /></AbsoluteFill>;
  }
  return (
    <AbsoluteFill style={{opacity: op, overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `scale(${z}) translateX(${tx}px)`}}>
        <OffthreadVideo src={staticFile(`shots/${s.id}.mp4`)} muted style={{width: 1920, height: 1080}} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/* ---- manba yozuvi (har bir tashqi kadrda) ---- */
const Credit: React.FC<{text: string; len: number}> = ({text, len}) => {
  const f = useCurrentFrame();
  const o = inOut(f, len, 8, 6);
  return (
    <div style={{position: 'absolute', right: 48, bottom: 40, opacity: o * 0.95, display: 'flex', alignItems: 'center', gap: 10, background: 'rgba(0,0,0,0.55)', padding: '6px 14px', borderLeft: `4px solid ${C.red}`}}>
      <span style={{fontFamily: F.body, fontWeight: 600, fontSize: 21, color: '#fff', letterSpacing: 0.3}}>{text}</span>
    </div>
  );
};

/* ---- doimiy belgilar: yuqori chap “bug”, vinyetka, grain ---- */
const Chrome: React.FC = () => {
  const f = useCurrentFrame();
  const inGfx = (sb.shots as any[]).some((s) => s.src === 'GFX' && f >= fr(s.start) - 4 && f < fr(s.end) + 4);
  const show = f > fr(30.0) && f < fr(333) && !inGfx;
  const o = show ? Math.min(appear(f, fr(30.0), 15), 1 - appear(f, fr(332.5), 15)) : 0;
  return (
    <>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.45) 100%)', pointerEvents: 'none'}} />
      <AbsoluteFill style={{opacity: 0.05, backgroundImage: `url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' seed='${f % 7}'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>")`}} />
      <div style={{position: 'absolute', left: 110, top: 56, opacity: o, display: 'flex', alignItems: 'stretch', fontFamily: F.head}}>
        <div style={{background: C.red, color: '#fff', fontWeight: 700, fontSize: 26, letterSpacing: 3, padding: '4px 14px'}}>TAHLIL</div>
        <div style={{background: 'rgba(9,16,28,0.8)', color: '#fff', fontWeight: 500, fontSize: 26, letterSpacing: 3, padding: '4px 16px'}}>ORMUZ INQIROZI</div>
      </div>
    </>
  );
};

export const Hormuz: React.FC = () => {
  const shots = sb.shots as any[];
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {shots.map((s, i) => {
        const from = fr(s.start);
        const len = fr(s.end) - from;
        const fadeIn = i > 0 && !(s.src === 'GFX') && shots[i - 1].src !== 'GFX' ? true : i > 0;
        const extra = i < shots.length - 1 ? XF : 0;
        return (
          <Sequence key={s.id} from={from} durationInFrames={len + extra} layout="none">
            <Shot s={s} idx={i} len={len + extra} fadeIn={fadeIn} />
          </Sequence>
        );
      })}
      {shots.filter((s) => s.credit).map((s) => (
        <Sequence key={'c' + s.id} from={fr(s.start)} durationInFrames={fr(s.end) - fr(s.start)}>
          <Credit text={s.credit} len={fr(s.end) - fr(s.start)} />
        </Sequence>
      ))}
      <Chrome />
      {(sb.overlays as any[]).map((o, i) => {
        const Comp = OV[o.type];
        if (!Comp) return null;
        const len = fr(o.end) - fr(o.start);
        return (
          <Sequence key={'o' + i} from={fr(o.start)} durationInFrames={len}>
            <Comp dur={len} props={o.props} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
