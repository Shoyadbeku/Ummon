import React from 'react';
import {interpolate, spring} from 'remotion';
import {KineticText} from '../components/text/KineticText';
import {HeroVisual} from '../components/media/HeroVisual';
import {GlassCard} from '../components/visuals/ui';
import {clamp, float} from '../lib/anim';
import {COLORS, FONT_BODY, FONT_DISPLAY} from '../lib/theme';
import {SceneFrame, useSceneBasics} from './shared';

const Option: React.FC<{
  icon: string;
  title: string;
  color: string;
  delay: number;
  percent: number;
  side: -1 | 1;
}> = ({icon, title, color, delay, percent, side}) => {
  const {frame, fps} = useSceneBasics();
  const s = spring({frame: frame - delay, fps, config: {damping: 13, stiffness: 110}});
  return (
    <div
      style={{
        transform: `translateX(${(1 - s) * side * 700}px) rotate(${(1 - s) * side * 12 + float(frame, 1.2, 0.05, side)}deg)`,
        opacity: s,
      }}
    >
      <GlassCard glow={color} radius={44} style={{width: 640, padding: '44px 50px'}}>
        <div style={{position: 'absolute', inset: 0, background: `linear-gradient(140deg, ${color}40, transparent 60%)`}} />
        <div style={{position: 'relative', display: 'flex', alignItems: 'center', gap: 30}}>
          <div style={{fontSize: 120}}>{icon}</div>
          <div style={{fontFamily: FONT_DISPLAY, fontWeight: 900, fontSize: 64, color: COLORS.text, lineHeight: 1.05}}>{title}</div>
        </div>
        <div style={{position: 'relative', marginTop: 36, height: 22, borderRadius: 22, background: 'rgba(255,255,255,0.1)'}}>
          <div
            style={{
              width: `${percent}%`,
              height: '100%',
              borderRadius: 22,
              background: `linear-gradient(90deg, ${color}, #FFFFFF)`,
              boxShadow: `0 0 30px ${color}`,
            }}
          />
        </div>
        <div style={{position: 'relative', marginTop: 14, fontFamily: FONT_BODY, fontWeight: 700, fontSize: 30, color: COLORS.muted, fontVariantNumeric: 'tabular-nums'}}>
          {Math.round(percent)}%
        </div>
      </GlassCard>
    </div>
  );
};

export const Scene10Question: React.FC = () => {
  const {frame, fps, windows, scene, timing} = useSceneBasics();
  const [w0, w1, w2] = windows;
  // Ovoz berish "jonli" tebranadi — javob hali noma'lum
  const base = interpolate(frame, [w2.end, w2.end + 60], [0, 1], clamp);
  const a = 50 + Math.sin(frame * 0.05) * 9 * base;
  const vs = spring({frame: frame - w2.start, fps, config: {damping: 8, stiffness: 200}});
  const cta = spring({frame: frame - w2.end - 10, fps, config: {damping: 12, stiffness: 140}});
  const pulse = 1 + Math.sin(frame * 0.15) * 0.04;

  return (
    <SceneFrame>
      {timing.image && (
        <div style={{position: 'absolute', inset: 0, opacity: 0.25}}>
          <HeroVisual width={1920} height={1080} radius={0} fallback={null} />
        </div>
      )}
      <div style={{position: 'absolute', top: 150, left: 0, right: 0, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
        <KineticText text={scene.segments[0].text} start={w0.start} duration={w0.duration} fontSize={56} fontWeight={700} color="#CBD5E1" align="center" />
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: 4}}>
          <KineticText
            text={scene.segments[1].text}
            highlight={scene.segments[1].highlight}
            start={w1.start}
            duration={w1.duration}
            fontSize={80}
            fontWeight={900}
            accent={COLORS.amber}
            accent2="#FEF3C7"
          />
          <KineticText
            text={scene.segments[2].text}
            highlight={scene.segments[2].highlight}
            start={w2.start}
            duration={w2.duration}
            fontSize={80}
            fontWeight={900}
            accent={COLORS.cyan}
            accent2="#CFFAFE"
          />
        </div>
      </div>

      <div style={{position: 'absolute', top: 470, left: 0, right: 0, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 120}}>
        <Option icon="🍽️" title="Avval ovqat" color={COLORS.amber} delay={w1.start + 10} percent={a * base} side={-1} />
        <Option icon="📸" title="Avval surat" color={COLORS.cyan} delay={w2.start + 10} percent={(100 - a) * base} side={1} />
      </div>
      <div
        style={{
          position: 'absolute',
          left: 960 - 75,
          top: 610,
          width: 150,
          height: 150,
          borderRadius: '50%',
          background: `linear-gradient(135deg, ${scene.accent}, ${COLORS.pink})`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: FONT_DISPLAY,
          fontWeight: 900,
          fontSize: 58,
          color: '#fff',
          boxShadow: `0 0 80px ${scene.accent}`,
          transform: `scale(${vs}) rotate(${(1 - vs) * 180}deg)`,
        }}
      >
        VS
      </div>

      <div
        style={{
          position: 'absolute',
          bottom: 110,
          left: 0,
          right: 0,
          display: 'flex',
          justifyContent: 'center',
          opacity: cta,
          transform: `translateY(${(1 - cta) * 60}px) scale(${pulse})`,
        }}
      >
        <div
          style={{
            padding: '26px 60px',
            borderRadius: 80,
            background: `linear-gradient(90deg, ${scene.accent}, ${COLORS.pink})`,
            fontFamily: FONT_DISPLAY,
            fontWeight: 900,
            fontSize: 48,
            color: '#fff',
            boxShadow: `0 20px 60px ${scene.accent}88`,
          }}
        >
          💬 Javobingizni izohlarda yozing! 👇
        </div>
      </div>
    </SceneFrame>
  );
};
