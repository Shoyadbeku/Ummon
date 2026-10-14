import React from 'react';
import {interpolate, spring} from 'remotion';
import {KineticText} from '../components/text/KineticText';
import {HeroVisual} from '../components/media/HeroVisual';
import {PlovPlate} from '../components/visuals/PlovPlate';
import {Steam} from '../components/visuals/Steam';
import {Chip} from '../components/visuals/ui';
import {clamp, float} from '../lib/anim';
import {COLORS} from '../lib/theme';
import {SceneFrame, useSceneBasics} from './shared';

const SPOONS = [
  {from: -1, x: 420, y: 620, r: -35, d: 0},
  {from: 1, x: 1420, y: 600, r: 35, d: 6},
  {from: -1, x: 560, y: 860, r: -60, d: 12},
  {from: 1, x: 1290, y: 870, r: 60, d: 18},
];

export const Scene03HotPlov: React.FC = () => {
  const {frame, fps, windows, scene, timing} = useSceneBasics();
  const [w0, w1, w2] = windows;
  const plateIn = spring({frame: frame - 2, fps, config: {damping: 15, stiffness: 70}});
  const temp = Math.round(interpolate(frame, [w0.start, w1.end], [20, 92], clamp));

  return (
    <SceneFrame>
      {/* Orqa nur */}
      <div
        style={{
          position: 'absolute',
          left: 960 - 700,
          top: 760 - 700,
          width: 1400,
          height: 1400,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${scene.accent}66 0%, transparent 60%)`,
          opacity: plateIn,
        }}
      />

      <div style={{position: 'absolute', left: 0, right: 0, top: 150, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
        <KineticText
          text={scene.segments[0].text}
          highlight={scene.segments[0].highlight}
          start={w0.start}
          duration={w0.duration}
          fontSize={110}
          fontWeight={900}
          align="center"
          mode="pop"
          accent={scene.accent}
          accent2="#FFF7D6"
        />
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: 6}}>
          <KineticText
            text={scene.segments[1].text}
            highlight={scene.segments[1].highlight}
            start={w1.start}
            duration={w1.duration}
            fontSize={50}
            fontWeight={700}
            color="#E2E8F0"
            align="center"
            accent={COLORS.saffron}
            accent2="#FFFFFF"
          />
          <KineticText
            text={scene.segments[2].text}
            highlight={scene.segments[2].highlight}
            start={w2.start}
            duration={w2.duration}
            fontSize={50}
            fontWeight={700}
            color="#E2E8F0"
            align="center"
            accent={COLORS.cyan}
            accent2="#FFFFFF"
          />
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          left: 960 - 380,
          top: 470,
          transform: `translateY(${(1 - plateIn) * 500 + float(frame, 6, 0.04)}px) scale(${0.8 + plateIn * 0.2})`,
        }}
      >
        <HeroVisual
          width={760}
          height={760}
          radius={380}
          zoom={0.18}
          fallback={<PlovPlate size={760} heat={1} tilt={55} spin={frame * 0.06} />}
          overlay={
            timing.image ? (
              <Steam heat={1} width={600} height={600} style={{position: 'absolute', left: 80, top: -40}} />
            ) : null
          }
        />
      </div>

      {SPOONS.map((sp, i) => {
        const s = spring({frame: frame - w2.start - sp.d, fps, config: {damping: 12, stiffness: 120}});
        const bob = float(frame, 10, 0.12, i);
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: sp.x + sp.from * (1 - s) * 900,
              top: sp.y + bob,
              fontSize: 130,
              transform: `rotate(${sp.r + (1 - s) * sp.from * 90}deg)`,
              filter: 'drop-shadow(0 20px 30px rgba(0,0,0,0.5))',
            }}
          >
            🥄
          </div>
        );
      })}

      <div style={{position: 'absolute', right: 150, top: 520}}>
        <Chip icon="🌡️" label={`${temp}°C`} color={COLORS.saffron} delay={w0.start} size={46} />
      </div>
      <div style={{position: 'absolute', left: 150, top: 530}}>
        <Chip icon="♨️" label="Yangi damlangan" color={scene.accent} delay={w1.start} size={34} />
      </div>
    </SceneFrame>
  );
};
