import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';

// 6 xil kamera harakati — sahnalar navbatma-navbat oladi
const MOVES = [
  {s0: 1.0, s1: 1.18, x0: 0, x1: -2, y0: 0, y1: -1},
  {s0: 1.2, s1: 1.04, x0: -2, x1: 2, y0: 1, y1: 0},
  {s0: 1.08, s1: 1.22, x0: 3, x1: -1, y0: -1, y1: 1},
  {s0: 1.15, s1: 1.15, x0: -3.5, x1: 3.5, y0: 0, y1: 0},
  {s0: 1.22, s1: 1.06, x0: 0, x1: 0, y0: -2, y1: 1.5},
  {s0: 1.04, s1: 1.2, x0: 2, x1: 0, y0: 1.5, y1: -1},
];

export const KenBurnsImage: React.FC<{src: string; index: number}> = ({src, index}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const m = MOVES[index % MOVES.length];
  const p = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.sin),
  });
  const s = m.s0 + (m.s1 - m.s0) * p;
  const x = m.x0 + (m.x1 - m.x0) * p;
  const y = m.y0 + (m.y1 - m.y0) * p;
  // Eski kinoplyonka kabi yengil yorug'lik "miltillashi"
  const flicker = 1 + Math.sin(frame * 0.9 + index) * 0.012 + Math.sin(frame * 2.3) * 0.008;

  return (
    <AbsoluteFill style={{overflow: 'hidden', backgroundColor: '#000'}}>
      <Img
        src={staticFile(src)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${s}) translate(${x}%, ${y}%)`,
          filter: `sepia(0.18) saturate(0.9) contrast(1.06) brightness(${0.94 * flicker})`,
        }}
      />
    </AbsoluteFill>
  );
};
