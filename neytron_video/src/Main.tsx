import React from 'react';
import {AbsoluteFill, Sequence, OffthreadVideo, staticFile, useCurrentFrame, interpolate, Easing} from 'remotion';
import shotsJson from './shots.json';
import {C, sec, TOTAL_FRAMES, HEAD, ease, pop} from './theme';
import {Captions} from './Captions';
import {Overlay, Hook} from './Overlays';
import {MG} from './MG';
import {Grain, LightLeak, Flash} from './Effects';

export type Shot = {
  start: number; end: number; dur: number; seg: number; word: number;
  kind: 'clip' | 'mg'; clip?: string; file?: string; mg?: string; props?: any;
  overlay?: {type: string; text: string; extra?: string};
};
// Burned-in captions are off; the SRT file is delivered separately.
const SHOW_CAPTIONS = false;
export const shots = shotsJson as unknown as Shot[];

// chapter tag that stays on screen at the top
const chapters = shots
  .filter((s) => s.kind === 'mg' && s.mg === 'chapter')
  .map((s) => ({start: s.start, n: s.props.n, title: s.props.title}));

const ClipShot: React.FC<{shot: Shot; index: number}> = ({shot, index}) => {
  const f = useCurrentFrame();
  const len = Math.max(1, sec(shot.dur));
  // Ken Burns: alternate push-in / pull-out, slight drift
  const zIn = index % 2 === 0;
  const kb = interpolate(f, [0, len], zIn ? [1.0, 1.09] : [1.09, 1.0], {extrapolateRight: 'clamp'});
  const drift = interpolate(f, [0, len], index % 3 === 0 ? [-14, 14] : [10, -10], {extrapolateRight: 'clamp'});
  // entry transition variety
  const style = index % 4;
  const p = ease(f, 0, 8, 0, 1);
  let enter: React.CSSProperties = {};
  if (style === 0) enter = {transform: `scale(${1.18 - 0.18 * p})`, filter: `blur(${(1 - p) * 14}px)`};
  if (style === 1) enter = {transform: `translateX(${(1 - p) * 180}px)`, filter: `blur(${(1 - p) * 18}px)`};
  if (style === 2) enter = {transform: `translateY(${(1 - p) * -160}px)`, filter: `blur(${(1 - p) * 16}px)`};
  if (style === 3) enter = {transform: `scale(${0.9 + 0.1 * p})`, filter: `brightness(${1 + (1 - p) * 1.4})`};
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: C.bg}}>
      <AbsoluteFill style={enter}>
        <AbsoluteFill style={{transform: `scale(${kb}) translateX(${drift}px)`}}>
          <OffthreadVideo src={staticFile(shot.file!)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
        </AbsoluteFill>
      </AbsoluteFill>
      {/* readability gradients for top text + bottom captions */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0) 30%, rgba(0,0,0,0) 62%, rgba(0,0,0,0.6) 85%, rgba(0,0,0,0.75) 100%)',
        }}
      />
      {shot.overlay ? <Overlay ov={shot.overlay} shot={shot} /> : null}
    </AbsoluteFill>
  );
};

const ChapterTag: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / 30;
  let cur = null as null | (typeof chapters)[number];
  for (const c of chapters) if (t >= c.start + 2.2) cur = c;
  if (!cur) return null;
  const here = shots.find((s) => t >= s.start && t < s.end);
  if (!here || here.kind !== 'clip') return null;
  const local = f - sec(cur.start + 2.2);
  const p = ease(local, 0, 14);
  return (
    <div
      style={{
        position: 'absolute', top: 40, left: 50, display: 'flex', alignItems: 'center', gap: 14,
        opacity: p, transform: `translateX(${(1 - p) * -40}px)`,
        background: 'rgba(8,10,16,0.55)', border: '1px solid rgba(255,255,255,0.18)', borderRadius: 40,
        padding: '10px 22px 10px 12px', backdropFilter: 'blur(8px)',
      }}
    >
      <div style={{width: 40, height: 40, borderRadius: 20, background: C.gold, color: '#000', fontFamily: HEAD, fontWeight: 900, fontSize: 22, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        {cur.n}
      </div>
      <div style={{fontFamily: HEAD, fontWeight: 800, fontSize: 24, color: '#fff', letterSpacing: 2}}>{cur.title}</div>
    </div>
  );
};

const HookLayer: React.FC = () => {
  const f = useCurrentFrame();
  const end = sec(shots[2].start);
  const o = interpolate(f, [end - 6, end], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{opacity: o}}>
      <Hook text="DUNYONI ASLIDA KIM BOSHQARADI?" />
    </AbsoluteFill>
  );
};

const Fade: React.FC = () => {
  const f = useCurrentFrame();
  const o = interpolate(f, [TOTAL_FRAMES - 14, TOTAL_FRAMES - 1], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{background: '#000', opacity: o}} />;
};

export const Main: React.FC = () => {
  return (
    <AbsoluteFill style={{background: C.bg}}>
      {shots.map((s, i) => {
        const from = sec(s.start);
        const dur = Math.max(1, sec(s.end) - from);
        return (
          <Sequence key={i} from={from} durationInFrames={dur} premountFor={20} name={`${i} ${s.kind === 'clip' ? s.clip : s.mg}`}>
            {s.kind === 'clip' ? <ClipShot shot={s} index={i} /> : <MG shot={s} index={i} />}
          </Sequence>
        );
      })}
      {/* flashes + light leaks on chapter cards */}
      {shots.map((s, i) =>
        s.kind === 'mg' && (s.mg === 'chapter' || s.mg === 'question') ? (
          <Sequence key={'fx' + i} from={Math.max(0, sec(s.start) - 3)} durationInFrames={40}>
            <Flash />
            <LightLeak />
          </Sequence>
        ) : null
      )}
      {/* hook headline persists across the first fast cuts */}
      <Sequence from={0} durationInFrames={sec(shots[2].start)}>
        <HookLayer />
      </Sequence>
      <ChapterTag />
      {SHOW_CAPTIONS ? <Captions /> : null}
      <Grain />
      <Fade />
    </AbsoluteFill>
  );
};
