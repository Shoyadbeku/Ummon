import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {Fit, Move} from '../data/types';

const ease = Easing.bezier(0.33, 0, 0.2, 1);

export const useMove = (move: Move | undefined) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const m = move ?? {s0: 1.04, s1: 1.12};
  const t = interpolate(frame, [0, durationInFrames], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const s = m.s0 + (m.s1 - m.s0) * t;
  const x = (m.x0 ?? 0) + ((m.x1 ?? 0) - (m.x0 ?? 0)) * t;
  const y = (m.y0 ?? 0) + ((m.y1 ?? 0) - (m.y0 ?? 0)) * t;
  return `scale(${s}) translate(${x}%, ${y}%)`;
};

/** Grade applied to all real footage: gentle contrast + cool shadows, never altering content. */
const grade = 'contrast(1.06) saturate(0.92) brightness(0.96)';

const Layer: React.FC<{file: string; video?: {from: number; rate?: number}; style: React.CSSProperties}> = ({file, video, style}) => {
  const {fps} = useVideoConfig();
  const src = staticFile(file);
  if (video) {
    return (
      <OffthreadVideo
        src={src}
        muted
        startFrom={Math.round(video.from * fps)}
        playbackRate={video.rate ?? 1}
        style={style}
      />
    );
  }
  return <Img src={src} style={style} />;
};

/**
 * Real footage/photo. "contain" keeps the original aspect ratio (no stretching, no face crop)
 * and fills the 16:9 frame with a blurred copy of the same image.
 */
export const Media: React.FC<{file: string; fit?: Fit; move?: Move; video?: {from: number; rate?: number}}> = ({file, fit = 'cover', move, video}) => {
  const transform = useMove(move);
  const full: React.CSSProperties = {position: 'absolute', width: '100%', height: '100%', objectFit: 'cover'};
  if (fit === 'cover') {
    return (
      <AbsoluteFill style={{overflow: 'hidden', backgroundColor: '#000'}}>
        <AbsoluteFill style={{transform, filter: grade}}>
          <Layer file={file} video={video} style={full} />
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{overflow: 'hidden', backgroundColor: '#000'}}>
      <AbsoluteFill style={{filter: 'blur(38px) brightness(0.38) saturate(0.8)', transform: 'scale(1.15)'}}>
        <Layer file={file} video={video} style={full} />
      </AbsoluteFill>
      <AbsoluteFill style={{transform, filter: grade, padding: '40px 0'}}>
        <Layer file={file} video={video} style={{width: '100%', height: '100%', objectFit: 'contain', filter: 'drop-shadow(0 30px 60px rgba(0,0,0,0.6))'}} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
