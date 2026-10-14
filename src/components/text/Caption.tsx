import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {clamp} from '../../lib/anim';
import {useScene, useSegmentWindows} from '../../lib/scene-context';
import {COLORS} from '../../lib/theme';
import {KineticText, type KineticMode} from './KineticText';

export type CaptionSegmentStyle = {
  mode?: KineticMode;
  uppercase?: boolean;
  accent?: string;
  accent2?: string;
  size?: number;
};

/**
 * Kinetik subtitr paneli: joriy gap katta chiqadi, oldingisi kichrayib
 * tepaga suriladi. So'zlar ovoz bilan sinxron (segment vaqt oynalari).
 */
export const Caption: React.FC<{
  styles?: CaptionSegmentStyle[];
  hideAfter?: number;
}> = ({styles = [], hideAfter}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {scene} = useScene();
  const windows = useSegmentWindows();

  let cur = 0;
  windows.forEach((w, i) => {
    if (frame >= w.start - 4) cur = i;
  });

  const enter = spring({frame: frame - 2, fps, config: {damping: 18, stiffness: 110}});
  const exit = hideAfter !== undefined ? interpolate(frame, [hideAfter, hideAfter + 14], [1, 0], clamp) : 1;

  return (
    <div
      style={{
        position: 'absolute',
        left: 180,
        right: 180,
        bottom: 42,
        minHeight: 210,
        padding: '26px 48px 30px 56px',
        borderRadius: 34,
        background: 'linear-gradient(135deg, rgba(10,14,28,0.88), rgba(10,14,28,0.72))',
        border: '1.5px solid rgba(255,255,255,0.14)',
        boxShadow: `0 30px 80px rgba(0,0,0,0.55), 0 0 80px ${scene.accent}33`,
        backdropFilter: 'blur(14px)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-end',
        gap: 6,
        opacity: enter * exit,
        transform: `translateY(${(1 - enter) * 80 + (1 - exit) * 40}px)`,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 22,
          bottom: 22,
          width: 8,
          borderRadius: 8,
          background: `linear-gradient(${scene.accent}, ${COLORS.pink})`,
        }}
      />
      {scene.segments.map((seg, i) => {
        if (i > cur || i < cur - 1) return null;
        const st = styles[i] ?? {};
        const next = windows[i + 1];
        const shrink = next ? spring({frame: frame - next.start + 4, fps, config: {damping: 200, stiffness: 140}}) : 0;
        const big = st.size ?? 64;
        const size = interpolate(shrink, [0, 1], [big, 34]);
        const w = windows[i];
        return (
          <div key={i} style={{opacity: interpolate(shrink, [0, 1], [1, 0.55])}}>
            <KineticText
              text={st.uppercase ? seg.text.toUpperCase() : seg.text}
              highlight={(seg.highlight ?? []).map((h) => (st.uppercase ? h.toUpperCase() : h))}
              start={w.start}
              duration={w.duration}
              mode={st.mode ?? 'rise'}
              fontSize={size}
              fontWeight={shrink > 0.5 ? 700 : 800}
              accent={st.accent ?? scene.accent}
              accent2={st.accent2 ?? '#FFFFFF'}
              lineHeight={1.15}
            />
          </div>
        );
      })}
    </div>
  );
};
