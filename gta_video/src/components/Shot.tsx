import React from 'react';
import {AbsoluteFill, Img, Loop, OffthreadVideo, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import clips from '../data/clips.json';

const CLIPS = clips as Record<string, {dur: number; w: number; h: number}>;

export type ShotProps = {
  src: string; // relative to public/
  kind: 'video' | 'image';
  fit?: 'cover' | 'card' | 'contain';
  from?: number; // seconds into source video
  rate?: number; // playback rate (speed ramp base)
  kb?: 'in' | 'out' | 'left' | 'right' | 'up' | 'down' | 'none';
  grade?: 'teal' | 'warm' | 'mono' | 'night' | 'none';
  focus?: string; // object-position, e.g. "30% 50%"
  dim?: number; // 0..1 darken
};

const gradeFilter = (g?: ShotProps['grade']) => {
  switch (g) {
    case 'warm':
      return 'contrast(1.12) saturate(1.15) sepia(.18) brightness(.95)';
    case 'mono':
      return 'grayscale(1) contrast(1.25) brightness(.9)';
    case 'night':
      return 'contrast(1.15) saturate(1.25) hue-rotate(-8deg) brightness(.85)';
    case 'none':
      return 'none';
    case 'teal':
    default:
      return 'contrast(1.12) saturate(1.08) brightness(.93)';
  }
};

const useKenBurns = (kb: ShotProps['kb'], dur: number) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, Math.max(1, dur)], [0, 1], {
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.33, 0, 0.67, 1),
  });
  switch (kb) {
    case 'in':
      return `scale(${1.06 + p * 0.14})`;
    case 'out':
      return `scale(${1.22 - p * 0.14})`;
    case 'left':
      return `scale(1.18) translateX(${4 - p * 8}%)`;
    case 'right':
      return `scale(1.18) translateX(${-4 + p * 8}%)`;
    case 'up':
      return `scale(1.18) translateY(${4 - p * 8}%)`;
    case 'down':
      return `scale(1.18) translateY(${-4 + p * 8}%)`;
    default:
      return 'scale(1.04)';
  }
};

const MediaEl: React.FC<ShotProps & {style: React.CSSProperties; dur: number}> = ({src, kind, from = 0, rate = 1, style, dur}) => {
  const {fps} = useVideoConfig();
  if (kind === 'video') {
    const name = src.replace(/^media\//, '').replace(/\.mp4$/, '');
    const clipDur = CLIPS[name]?.dur ?? 10;
    let start = Math.min(from, Math.max(0, clipDur - 2));
    const avail = Math.max(1, Math.floor((clipDur - start) * fps) - 2);
    let r = rate;
    if (dur * r > avail) r = Math.max(0.5, avail / dur);
    const v = (
      <OffthreadVideo src={staticFile(src)} muted trimBefore={Math.round(start * fps)} playbackRate={r} style={style} />
    );
    if (dur * r > avail) {
      return <Loop durationInFrames={Math.floor(avail / r)}>{v}</Loop>;
    }
    return v;
  }
  return <Img src={staticFile(src)} style={style} />;
};

export const Shot: React.FC<ShotProps & {dur: number}> = (p) => {
  const {dur, fit = 'cover', kb = 'in', grade, focus = '50% 50%', dim = 0} = p;
  const frame = useCurrentFrame();
  const transform = useKenBurns(kb, dur);
  const filter = gradeFilter(grade);

  if (fit === 'cover') {
    return (
      <AbsoluteFill style={{overflow: 'hidden', background: '#000'}}>
        <AbsoluteFill style={{transform}}>
          <MediaEl {...p} dur={dur} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: focus, filter}} />
        </AbsoluteFill>
        {dim > 0 && <AbsoluteFill style={{background: `rgba(0,0,0,${dim})`}} />}
      </AbsoluteFill>
    );
  }

  // Card layout: blurred fill behind a floating 16:9 (or contain) frame with slow parallax tilt
  const tilt = interpolate(frame, [0, Math.max(1, dur)], [-3, 3]);
  const lift = interpolate(frame, [0, Math.max(1, dur)], [12, -12]);
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#000'}}>
      {/* low-res blurred background: render small then scale up = cheap blur */}
      <div style={{position: 'absolute', left: 0, top: 0, width: 270, height: 480, transform: 'scale(4)', transformOrigin: '0 0', overflow: 'hidden'}}>
        {p.kind === 'image' ? (
          <Img src={staticFile(p.src)} style={{width: '100%', height: '100%', objectFit: 'cover', filter: 'blur(9px) brightness(.45) saturate(1.3)'}} />
        ) : (
          <div style={{width: '100%', height: '100%', background: 'radial-gradient(circle at 50% 40%, #2a2a40 0%, #07070c 75%)'}} />
        )}
      </div>
      <AbsoluteFill style={{perspective: 1600, alignItems: 'center', justifyContent: 'center'}}>
        <div
          style={{
            width: 1000,
            height: fit === 'contain' ? 1300 : 562,
            marginTop: -160,
            borderRadius: 28,
            overflow: 'hidden',
            boxShadow: '0 40px 120px rgba(0,0,0,.75), 0 0 0 2px rgba(255,255,255,.12)',
            transform: `rotateY(${tilt}deg) translateY(${lift}px)`,
            background: '#000',
          }}
        >
          <div style={{width: '100%', height: '100%', transform}}>
            <MediaEl {...p} dur={dur} style={{width: '100%', height: '100%', objectFit: fit === 'contain' ? 'contain' : 'cover', objectPosition: focus, filter}} />
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
