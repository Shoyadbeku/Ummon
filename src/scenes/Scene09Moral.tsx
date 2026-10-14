import React from 'react';
import {interpolate, spring} from 'remotion';
import {KineticText} from '../components/text/KineticText';
import {HeroVisual} from '../components/media/HeroVisual';
import {PlovPlate} from '../components/visuals/PlovPlate';
import {Steam} from '../components/visuals/Steam';
import {clamp} from '../lib/anim';
import {COLORS, FONT_BODY, FONT_DISPLAY} from '../lib/theme';
import {SceneFrame, useSceneBasics} from './shared';

const FILTERS = ['Oddiy', 'Yorqin', 'Retro', 'Bug‘ ♨️'];

export const Scene09Moral: React.FC = () => {
  const {frame, fps, windows, scene, timing} = useSceneBasics();
  const [w0, w1, w2] = windows;
  const plateIn = spring({frame: frame - 4, fps, config: {damping: 16, stiffness: 70}});
  // Filtr karuseli: so'z aytilganda "Bug'" filtri tanlanadi
  const sel = interpolate(frame, [w0.start, w0.end, w1.start + 6], [0, 2, 3], {
    ...clamp,
    easing: (t) => t * t * (3 - 2 * t),
  });
  const glow = 0.5 + 0.5 * Math.sin(frame * 0.08);

  return (
    <SceneFrame>
      <div
        style={{
          position: 'absolute',
          right: 120,
          top: 20,
          width: 900,
          height: 900,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${scene.accent}88 0%, ${scene.accent}22 40%, transparent 65%)`,
          opacity: 0.7 + glow * 0.3,
        }}
      />
      <div
        style={{
          position: 'absolute',
          right: 260,
          top: 170,
          transform: `scale(${0.7 + plateIn * 0.3}) rotate(${(1 - plateIn) * -30}deg)`,
          opacity: plateIn,
        }}
      >
        <HeroVisual
          width={620}
          height={620}
          radius={310}
          fallback={<PlovPlate size={620} heat={1} tilt={52} spin={frame * 0.08} />}
          overlay={
            timing.image ? <Steam heat={1} width={560} height={560} style={{position: 'absolute', left: 60, top: -20}} /> : null
          }
        />
        <Steam heat={1} width={600} height={700} wisps={8} style={{position: 'absolute', left: 10, top: -240}} />
      </div>

      <div style={{position: 'absolute', left: 130, top: 200, width: 820}}>
        <KineticText
          text={scene.segments[0].text}
          highlight={scene.segments[0].highlight}
          start={w0.start}
          duration={w0.duration}
          fontSize={72}
          fontWeight={800}
          color="#E2E8F0"
          accent={COLORS.cyan}
          accent2="#ECFEFF"
        />
        <div style={{height: 14}} />
        <KineticText
          text={scene.segments[1].text.toUpperCase()}
          highlight={['BUG‘I,']}
          start={w1.start}
          duration={w1.duration}
          mode="slam"
          fontSize={140}
          fontWeight={900}
          accent={scene.accent}
          accent2="#FFF7ED"
          letterSpacing={-4}
        />
        <div style={{height: 14}} />
        <KineticText
          text={scene.segments[2].text}
          highlight={scene.segments[2].highlight}
          start={w2.start}
          duration={w2.duration}
          fontSize={64}
          fontWeight={800}
          accent={COLORS.red}
          accent2="#FED7AA"
        />
      </div>

      {/* Filtrlar */}
      <div style={{position: 'absolute', right: 190, bottom: 90, display: 'flex', gap: 30}}>
        {FILTERS.map((f, i) => {
          const s = spring({frame: frame - 10 - i * 5, fps, config: {damping: 14}});
          const active = Math.max(0, 1 - Math.abs(sel - i));
          return (
            <div key={f} style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, transform: `scale(${s * (1 + active * 0.18)})`}}>
              <div
                style={{
                  width: 130,
                  height: 130,
                  borderRadius: 30,
                  overflow: 'hidden',
                  border: `4px solid ${active > 0.5 ? scene.accent : 'rgba(255,255,255,0.2)'}`,
                  boxShadow: active > 0.5 ? `0 0 50px ${scene.accent}` : 'none',
                  background: ['#5B4636', '#C2410C', '#78716C', '#EA580C'][i],
                  filter: ['none', 'saturate(1.6)', 'sepia(0.8)', 'none'][i],
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 64,
                }}
              >
                {['🍚', '🌈', '📼', '♨️'][i]}
              </div>
              <div style={{fontFamily: FONT_BODY, fontWeight: 700, fontSize: 26, color: active > 0.5 ? COLORS.text : COLORS.muted}}>{f}</div>
            </div>
          );
        })}
      </div>

      <div
        style={{
          position: 'absolute',
          right: 170,
          top: 140,
          fontFamily: FONT_DISPLAY,
          fontWeight: 900,
          fontSize: 30,
          letterSpacing: 6,
          color: scene.accent,
          opacity: interpolate(frame, [w1.start, w1.start + 20], [0, 1], clamp),
        }}
      >
        ✨ ENG YAXSHI FILTR
      </div>
    </SceneFrame>
  );
};
