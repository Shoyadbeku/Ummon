import React from 'react';
import {interpolate, spring} from 'remotion';
import {KineticText} from '../components/text/KineticText';
import {HeroVisual} from '../components/media/HeroVisual';
import {PlovPlate} from '../components/visuals/PlovPlate';
import {Chip, GlassCard, Phone, Viewfinder} from '../components/visuals/ui';
import {float} from '../lib/anim';
import {COLORS, FONT_BODY} from '../lib/theme';
import {SceneFrame, useSceneBasics} from './shared';

export const Scene02Intro: React.FC = () => {
  const {frame, fps, windows, scene} = useSceneBasics();
  const [w0, w1] = windows;
  const enter = spring({frame: frame - 4, fps, config: {damping: 16, stiffness: 80}});

  // Parallaks qatlamlar: orqa karta < telefon < chiplar
  const drift = interpolate(frame, [0, 600], [0, -80]);

  return (
    <SceneFrame>
      <div style={{position: 'absolute', left: 130, top: 300, width: 900}}>
        <KineticText
          text={scene.segments[0].text}
          start={w0.start}
          duration={w0.duration}
          fontSize={60}
          fontWeight={700}
          color="#CBD5E1"
        />
        <div style={{height: 26}} />
        <KineticText
          text={scene.segments[1].text}
          highlight={scene.segments[1].highlight}
          start={w1.start}
          duration={w1.duration}
          fontSize={84}
          accent={scene.accent}
          accent2="#F5D0FE"
        />
      </div>

      <div style={{position: 'absolute', right: 120, top: 110, width: 700, height: 860}}>
        <GlassCard
          glow={scene.accent}
          style={{
            position: 'absolute',
            left: 40,
            top: 120,
            width: 600,
            height: 640,
            transform: `translate(${drift * 0.4}px, ${(1 - enter) * 200}px) rotate(-7deg)`,
            opacity: enter,
          }}
        >
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: `radial-gradient(circle at 30% 20%, ${scene.accent}55, transparent 60%)`,
            }}
          />
          <div style={{position: 'absolute', left: 40, bottom: 40, fontFamily: FONT_BODY, color: COLORS.muted, fontSize: 28}}>
            🍽️ Restoran • 13:05
          </div>
        </GlassCard>

        <div
          style={{
            position: 'absolute',
            left: 150,
            top: 30 + float(frame, 12, 0.04),
            transform: `translate(${drift * 0.8}px, ${(1 - enter) * 500}px) perspective(1600px) rotateY(-16deg) rotateZ(4deg)`,
          }}
        >
          <Phone width={380} glow={scene.accent}>
            <HeroVisual
              width={354}
              height={752}
              radius={0}
              fallback={
                <div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: 'radial-gradient(circle, #2F1D10, #08080C 75%)',
                  }}
                >
                  <PlovPlate size={400} tilt={0} spin={frame * 0.2} heat={1} steam={false} />
                </div>
              }
              overlay={<Viewfinder label="FOTOSESSIYA" color={scene.accent} />}
            />
          </Phone>
        </div>

        <div style={{position: 'absolute', left: -40, top: 140 + float(frame, 18, 0.05, 1), transform: `translateX(${drift * 1.4}px)`}}>
          <Chip icon="📸" label="Fotosessiya" color={scene.accent} delay={w1.start + 10} />
        </div>
        <div style={{position: 'absolute', right: -20, top: 520 + float(frame, 16, 0.045, 2), transform: `translateX(${drift * 1.6}px)`}}>
          <Chip icon="✨" label="Kadr #47" color={COLORS.cyan} delay={w1.start + 30} />
        </div>
        <div style={{position: 'absolute', left: 0, bottom: 40 + float(frame, 14, 0.05, 3), transform: `translateX(${drift * 1.2}px)`}}>
          <Chip icon="🍚" label="Palov" color={COLORS.amber} delay={w0.start + 20} size={34} />
        </div>
      </div>
    </SceneFrame>
  );
};
