import React from 'react';
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import type {Scene} from '../types';
import {ACCENT, Credit, FONT, SERIF, Starfield, WARM, ease} from './Common';

const GRADE = 'contrast(1.08) saturate(1.08) brightness(0.97)';

/** Ken Burns transform for a scene of `dur` frames */
const useMove = (scene: Scene, dur: number, strength = 0.12) => {
  const frame = useCurrentFrame();
  const t = interpolate(frame, [0, dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const m = scene.move ?? 'in';
  let scale = 1.04;
  let tx = 0;
  let ty = 0;
  if (m === 'in') scale = 1.02 + strength * t;
  if (m === 'out') scale = 1.02 + strength * (1 - t);
  if (m === 'left') {scale = 1.1; tx = interpolate(t, [0, 1], [3, -3]);}
  if (m === 'right') {scale = 1.1; tx = interpolate(t, [0, 1], [-3, 3]);}
  if (m === 'up') {scale = 1.1; ty = interpolate(t, [0, 1], [3, -3]);}
  if (m === 'down') {scale = 1.1; ty = interpolate(t, [0, 1], [-3, 3]);}
  const ox = (scene.focusX ?? 0.5) * 100;
  const oy = (scene.focusY ?? 0.5) * 100;
  return {transform: `translate(${tx}%, ${ty}%) scale(${scale})`, transformOrigin: `${ox}% ${oy}%`};
};

/** Authentic video footage. Non-16:9 sources sit on a blurred copy of themselves (no stretching). */
export const VideoScene: React.FC<{scene: Scene; dur: number}> = ({scene, dur}) => {
  const {fps} = useVideoConfig();
  const mv = useMove(scene, dur, 0.06);
  const src = staticFile(scene.src!);
  const start = Math.round((scene.srcStart ?? 0) * fps);
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <AbsoluteFill style={{...mv}}>
        <OffthreadVideo
          src={src}
          startFrom={start}
          playbackRate={scene.rate ?? 1}
          muted
          style={{width: '100%', height: '100%', objectFit: 'cover', filter: GRADE}}
        />
      </AbsoluteFill>
      <Credit text={scene.credit} label={scene.label} />
    </AbsoluteFill>
  );
};

/** Authentic photograph with 2.5D treatment: blurred depth layer + moving foreground plate */
export const PhotoScene: React.FC<{scene: Scene; dur: number}> = ({scene, dur}) => {
  const frame = useCurrentFrame();
  const mv = useMove(scene, dur, 0.14);
  const src = staticFile(scene.src!);
  const bgShift = interpolate(frame, [0, dur], [1.15, 1.22]);
  return (
    <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `scale(${bgShift})`}}>
        <Img src={src} style={{width: '100%', height: '100%', objectFit: 'cover', filter: 'blur(38px) brightness(0.45) saturate(1.2)'}} />
      </AbsoluteFill>
      <AbsoluteFill style={{...mv}}>
        <Img src={src} style={{width: '100%', height: '100%', objectFit: 'contain', filter: GRADE}} />
      </AbsoluteFill>
      <Credit text={scene.credit} label={scene.label} />
    </AbsoluteFill>
  );
};

const Backdrop: React.FC<{scene: Scene; dur: number}> = ({scene, dur}) => {
  const frame = useCurrentFrame();
  if (!scene.bg) return <Starfield seed={scene.id} />;
  const s = interpolate(frame, [0, dur], [1.05, 1.15]);
  const isVid = scene.bg.endsWith('.mp4');
  const style: React.CSSProperties = {width: '100%', height: '100%', objectFit: 'cover', filter: 'brightness(0.32) saturate(1.1) blur(2px)'};
  return (
    <AbsoluteFill style={{transform: `scale(${s})`, background: '#000'}}>
      {isVid ? <OffthreadVideo src={staticFile(scene.bg)} muted style={style} /> : <Img src={staticFile(scene.bg)} style={style} />}
    </AbsoluteFill>
  );
};

/** Chapter / documentary title card */
export const TitleScene: React.FC<{scene: Scene; dur: number}> = ({scene, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: frame - 4, fps, config: {damping: 200, mass: 1.2}});
  const line = spring({frame: frame - 14, fps, config: {damping: 200}});
  const sub = spring({frame: frame - 22, fps, config: {damping: 200}});
  const track = interpolate(frame, [0, dur], [6, 14]);
  return (
    <AbsoluteFill>
      <Backdrop scene={scene} dur={dur} />
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', fontFamily: SERIF, color: '#fff'}}>
        <div style={{fontSize: 104, fontWeight: 700, letterSpacing: track, textAlign: 'center', opacity: p, transform: `translateY(${(1 - p) * 30}px)`, textShadow: '0 6px 40px rgba(0,0,0,0.8)', padding: '0 120px', lineHeight: 1.1}}>
          {scene.title}
        </div>
        <div style={{width: 520 * line, height: 2, background: `linear-gradient(90deg, transparent, ${ACCENT}, transparent)`, margin: '34px 0'}} />
        {scene.subtitle ? (
          <div style={{fontFamily: FONT, fontSize: 32, letterSpacing: 6, textTransform: 'uppercase', color: 'rgba(255,255,255,0.8)', opacity: sub, textAlign: 'center', padding: '0 160px'}}>
            {scene.subtitle}
          </div>
        ) : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const fmt = (v: number, d: number) =>
  v.toLocaleString('en-US', {minimumFractionDigits: d, maximumFractionDigits: d}).replace(/,/g, ' ');

/** Animated statistic — numbers come straight from the narration */
export const StatScene: React.FC<{scene: Scene; dur: number}> = ({scene, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const count = interpolate(frame, [6, Math.min(dur * 0.55, 2.2 * fps)], [0, scene.value ?? 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const p = spring({frame, fps, config: {damping: 200}});
  const n = spring({frame: frame - 18, fps, config: {damping: 200}});
  return (
    <AbsoluteFill>
      <Backdrop scene={scene} dur={dur} />
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', color: '#fff', fontFamily: FONT}}>
        {scene.title ? (
          <div style={{fontSize: 34, letterSpacing: 6, textTransform: 'uppercase', color: ACCENT, opacity: p, marginBottom: 18, textAlign: 'center', padding: '0 120px'}}>
            {scene.title}
          </div>
        ) : null}
        <div style={{display: 'flex', alignItems: 'baseline', gap: 22, transform: `scale(${0.9 + 0.1 * p})`, opacity: p}}>
          {scene.prefix ? <span style={{fontSize: 70, fontWeight: 300, color: 'rgba(255,255,255,0.8)'}}>{scene.prefix}</span> : null}
          {scene.value !== undefined ? (
            <span style={{fontSize: 190, fontWeight: 800, fontVariantNumeric: 'tabular-nums', letterSpacing: -4, textShadow: `0 0 60px ${ACCENT}55`}}>
              {fmt(count, scene.decimals ?? 0)}
            </span>
          ) : null}
          {scene.unit ? <span style={{fontSize: 74, fontWeight: 600, color: WARM}}>{scene.unit}</span> : null}
        </div>
        {scene.note ? (
          <div style={{marginTop: 26, fontSize: 38, color: 'rgba(255,255,255,0.85)', opacity: n, transform: `translateY(${(1 - n) * 16}px)`, textAlign: 'center', padding: '0 180px', lineHeight: 1.35}}>
            {scene.note}
          </div>
        ) : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** Big kinetic statement for key lines with no specific footage */
export const StatementScene: React.FC<{scene: Scene; dur: number}> = ({scene, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const words = (scene.title ?? '').split(' ');
  return (
    <AbsoluteFill>
      <Backdrop scene={scene} dur={dur} />
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', padding: '0 170px'}}>
        <div style={{fontFamily: SERIF, fontSize: 82, fontWeight: 700, color: '#fff', textAlign: 'center', lineHeight: 1.2, textShadow: '0 6px 30px rgba(0,0,0,0.8)'}}>
          {words.map((w, i) => {
            const p = spring({frame: frame - 4 - i * 3, fps, config: {damping: 200}});
            const hl = w.startsWith('*');
            return (
              <span key={i} style={{display: 'inline-block', marginRight: 22, opacity: p, transform: `translateY(${(1 - p) * 26}px)`, color: hl ? WARM : '#fff'}}>
                {hl ? w.slice(1) : w}
              </span>
            );
          })}
        </div>
        {scene.subtitle ? (
          <div style={{marginTop: 30, fontFamily: FONT, fontSize: 30, letterSpacing: 4, textTransform: 'uppercase', color: ACCENT, opacity: spring({frame: frame - 20, fps, config: {damping: 200}})}}>
            {scene.subtitle}
          </div>
        ) : null}
      </AbsoluteFill>
      <Credit text={scene.credit} />
    </AbsoluteFill>
  );
};

/** Split-screen comparison of two real objects */
export const CompareScene: React.FC<{scene: Scene; dur: number}> = ({scene, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const side = (it: NonNullable<Scene['left']>, i: number) => {
    const p = spring({frame: frame - 4 - i * 10, fps, config: {damping: 200}});
    const s = interpolate(frame, [0, dur], [1.04, 1.12]);
    return (
      <div style={{flex: 1, position: 'relative', overflow: 'hidden', opacity: p, transform: `translateX(${(1 - p) * (i ? 60 : -60)}px)`}}>
        {it.src ? (
          it.src.endsWith('.mp4') ? (
            <OffthreadVideo src={staticFile(it.src)} muted style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${s})`, filter: GRADE}} />
          ) : (
            <Img src={staticFile(it.src)} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${s})`, filter: GRADE}} />
          )
        ) : (
          <Starfield seed={`${scene.id}${i}`} />
        )}
        <div style={{position: 'absolute', left: 0, right: 0, top: 0, padding: '60px 50px 90px', background: 'linear-gradient(rgba(0,0,0,0.75), transparent)', fontFamily: FONT, color: '#fff', textAlign: 'center'}}>
          <div style={{fontSize: 44, fontWeight: 700}}>{it.label}</div>
          {it.value ? <div style={{fontSize: 34, color: i ? WARM : ACCENT, marginTop: 8, fontWeight: 600}}>{it.value}</div> : null}
        </div>
      </div>
    );
  };
  return (
    <AbsoluteFill style={{background: '#000', flexDirection: 'row', gap: 6}}>
      {scene.left ? side(scene.left, 0) : null}
      {scene.right ? side(scene.right, 1) : null}
      <Credit text={scene.credit} />
    </AbsoluteFill>
  );
};
