import React from 'react';
import {AbsoluteFill, Audio, Easing, Sequence, interpolate, random, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {SCENES, Scene, TOTAL_SEC} from './storyboard';
import {Captions, Word} from './components/Captions';
import {Grain, Vignette, SafeGradients, LightLeak, Flash} from './components/Overlays';
import {C} from './theme';
import words from './data/words.json';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// Entrance transition applied to the whole scene (bg + fg) for its first frames
const Entrance: React.FC<{fx?: Scene['fx']; children: React.ReactNode; seed: number}> = ({fx = 'zoom', children, seed}) => {
  const f = useCurrentFrame();
  let style: React.CSSProperties = {};
  if (fx === 'zoom' || fx === 'flash' || fx === 'leak') {
    const p = interpolate(f, [0, 12], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
    style = {transform: `scale(${1.14 - 0.14 * p})`};
  } else if (fx === 'whip') {
    const p = interpolate(f, [0, 8], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
    const dir = random(seed) > 0.5 ? 1 : -1;
    style = {transform: `translateX(${dir * (1 - p) * 40}%) scale(${1.1 - 0.1 * p})`, filter: p < 1 ? `blur(${(1 - p) * 24}px)` : undefined};
  } else if (fx === 'blur') {
    const p = interpolate(f, [0, 14], [0, 1], {...clamp, easing: Easing.out(Easing.quad)});
    style = {filter: p < 1 ? `blur(${(1 - p) * 30}px) brightness(${1 + (1 - p) * 0.6})` : undefined, transform: `scale(${1.08 - 0.08 * p})`};
  } else if (fx === 'shake') {
    const a = interpolate(f, [0, 16], [34, 0], clamp);
    style = {transform: `translate(${(random(`x${f}${seed}`) - 0.5) * a}px, ${(random(`y${f}${seed}`) - 0.5) * a}px) scale(${1 + a / 600})`};
  } else if (fx === 'glitch') {
    if (f < 8) {
      const dx = (random(`g${f}${seed}`) - 0.5) * 60;
      style = {transform: `translateX(${dx}px) skewX(${(random(`k${f}${seed}`) - 0.5) * 12}deg)`, filter: `hue-rotate(${random(`h${f}`) * 180}deg) saturate(2)`};
    }
  }
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <AbsoluteFill style={style}>{children}</AbsoluteFill>
      {fx === 'glitch' && f < 8 && (
        <AbsoluteFill style={{background: `repeating-linear-gradient(0deg, rgba(255,0,80,.25) 0 ${4 + (f % 3) * 6}px, rgba(0,255,220,.18) ${4 + (f % 3) * 6}px ${12 + (f % 4) * 10}px)`, mixBlendMode: 'screen'}} />
      )}
    </AbsoluteFill>
  );
};

const ProgressBar: React.FC<{total: number}> = ({total}) => {
  const f = useCurrentFrame();
  return (
    <div style={{position: 'absolute', top: 0, left: 0, right: 0, height: 8, background: 'rgba(255,255,255,.12)'}}>
      <div style={{width: `${(f / total) * 100}%`, height: '100%', background: `linear-gradient(90deg, ${C.yellow}, ${C.pink})`, boxShadow: `0 0 12px ${C.pink}`}} />
    </div>
  );
};

export const Main: React.FC<{captions?: boolean}> = ({captions = false}) => {
  const {fps, durationInFrames} = useVideoConfig();
  const frame = useCurrentFrame();
  const fadeOut = interpolate(frame, [durationInFrames - 30, durationInFrames - 1], [0, 1], clamp);
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {SCENES.map((s, i) => {
        const from = Math.round(s.t * fps);
        const next = i < SCENES.length - 1 ? Math.round(SCENES[i + 1].t * fps) : Math.round(TOTAL_SEC * fps);
        const dur = next - from;
        return (
          <Sequence key={i} from={from} durationInFrames={dur} name={`S${i} ${s.t}s`}>
            <Entrance fx={s.fx} seed={i}>
              {s.bg(dur)}
              {(s.fg ?? []).map((g, j) => {
                const gf = Math.round((g.at ?? 0) * fps);
                const gd = g.until !== undefined ? Math.round(g.until * fps) - gf : dur - gf;
                return (
                  <Sequence key={j} from={gf} durationInFrames={Math.max(1, gd)} layout="none">
                    <AbsoluteFill>{g.el(gd)}</AbsoluteFill>
                  </Sequence>
                );
              })}
            </Entrance>
            {s.fx === 'flash' && <Flash at={0} />}
            {s.fx === 'leak' && <LightLeak at={0} seed={i} dur={30} />}
          </Sequence>
        );
      })}
      {/* light leaks sprinkled on some cuts for warmth */}
      {SCENES.filter((_, i) => i % 9 === 4).map((s, i) => (
        <LightLeak key={`lk${i}`} at={Math.round(s.t * fps)} seed={i + 100} />
      ))}
      <SafeGradients light={!captions} />
      <Vignette strength={captions ? 0.6 : 0.45} />
      <Grain opacity={0.07} />
      {captions && <Captions words={words as Word[]} />}
      <ProgressBar total={durationInFrames} />
      <AbsoluteFill style={{background: '#000', opacity: fadeOut, pointerEvents: 'none'}} />
      <Audio src={staticFile('audio/final_mix.wav')} />
    </AbsoluteFill>
  );
};
