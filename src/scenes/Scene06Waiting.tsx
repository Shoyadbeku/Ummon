import React, {useMemo} from 'react';
import {AbsoluteFill, interpolate, random, spring} from 'remotion';
import {KineticText} from '../components/text/KineticText';
import {HeroVisual} from '../components/media/HeroVisual';
import {PlovPlate} from '../components/visuals/PlovPlate';
import {Avatar, GlassCard, Thermometer} from '../components/visuals/ui';
import {clamp, float} from '../lib/anim';
import {COLORS, FONT_DISPLAY, FONT_BODY} from '../lib/theme';
import {SceneFrame, useSceneBasics} from './shared';

const FRIENDS = [
  {emoji: '😩', color: COLORS.amber},
  {emoji: '🥱', color: COLORS.violet},
  {emoji: '😵‍💫', color: COLORS.pink},
];

export const Scene06Waiting: React.FC = () => {
  const {frame, fps, windows, scene, timing} = useSceneBasics();
  const [w0, w1] = windows;
  const end = timing.durationInFrames - 30;

  // Harorat va bug' vaqt bo'yicha pasayadi
  const heat = interpolate(frame, [w0.start, w1.end], [1, 0.05], clamp);
  const temp = Math.round(interpolate(heat, [0, 1], [24, 92]));
  const minutes = Math.round(interpolate(frame, [0, end], [0, 25], clamp));
  const coldTint = interpolate(frame, [w1.start, w1.end], [0, 0.22], clamp);

  const snow = useMemo(
    () => new Array(40).fill(0).map((_, i) => ({x: random(`snx${i}`) * 1920, s: 0.6 + random(`sns${i}`), d: random(`snd${i}`) * 200})),
    [],
  );

  return (
    <SceneFrame>
      <AbsoluteFill style={{background: COLORS.cold, opacity: coldTint, mixBlendMode: 'color'}} />

      <div style={{position: 'absolute', left: 130, top: 160, width: 860}}>
        <KineticText
          text={scene.segments[0].text}
          highlight={scene.segments[0].highlight}
          start={w0.start}
          duration={w0.duration}
          fontSize={76}
          accent={COLORS.amber}
          accent2="#FEF3C7"
        />
        <div style={{height: 20}} />
        <KineticText
          text={scene.segments[1].text}
          highlight={scene.segments[1].highlight}
          start={w1.start}
          duration={w1.duration}
          fontSize={96}
          fontWeight={900}
          accent={scene.accent}
          accent2="#E0F2FE"
        />
      </div>

      {/* Do'stlar */}
      <div style={{position: 'absolute', left: 130, bottom: 120, display: 'flex', gap: 36}}>
        {FRIENDS.map((f, i) => {
          const s = spring({frame: frame - 8 - i * 7, fps, config: {damping: 12, stiffness: 140}});
          return (
            <div key={i} style={{transform: `translateY(${(1 - s) * 300 + float(frame, 8, 0.07, i * 2)}px) scale(${s})`}}>
              <Avatar emoji={f.emoji} color={f.color} size={170} />
            </div>
          );
        })}
        <GlassCard style={{padding: '28px 40px', alignSelf: 'center'}} radius={28}>
          <div style={{fontFamily: FONT_BODY, color: COLORS.muted, fontSize: 24, fontWeight: 600, letterSpacing: 3}}>KUTISH VAQTI</div>
          <div style={{fontFamily: FONT_DISPLAY, color: COLORS.text, fontSize: 64, fontWeight: 900, fontVariantNumeric: 'tabular-nums'}}>
            ⏰ {minutes} daq
          </div>
        </GlassCard>
      </div>

      {/* Soviyotgan palov */}
      <div style={{position: 'absolute', right: 330, top: 260}}>
        <HeroVisual
          width={620}
          height={620}
          radius={310}
          filter={`saturate(${0.5 + heat * 0.5}) hue-rotate(${(1 - heat) * 25}deg)`}
          fallback={<PlovPlate size={620} heat={heat} tilt={55} />}
        />
      </div>
      <div style={{position: 'absolute', right: 130, top: 230}}>
        <Thermometer value={heat} height={460} label={`${temp}°C`} />
      </div>

      {snow.map((p, i) => {
        const o = interpolate(frame, [w1.start, w1.start + 40], [0, 0.8], clamp);
        const y = ((frame * 2.2 * p.s + p.d * 6) % 1200) - 100;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: p.x + Math.sin(frame * 0.03 + i) * 30,
              top: y,
              fontSize: 22 * p.s,
              opacity: o * 0.7,
            }}
          >
            ❄️
          </div>
        );
      })}
    </SceneFrame>
  );
};
