import React from 'react';
import {interpolate, spring} from 'remotion';
import {KineticText} from '../components/text/KineticText';
import {HeroVisual} from '../components/media/HeroVisual';
import {PlovPlate} from '../components/visuals/PlovPlate';
import {Chip, Flash, GlassCard, Viewfinder} from '../components/visuals/ui';
import {COLORS} from '../lib/theme';
import {SceneFrame, useSceneBasics} from './shared';

export const Scene05Photoshoot: React.FC = () => {
  const {frame, fps, windows, scene} = useSceneBasics();
  const [w0, w1, w2] = windows;

  // Kamera burchaklari: tepadan → yonidan → yaqin (go'sht) → selfi
  const tSide = w0.start + Math.round(w0.duration * 0.5);
  const tZoom = w1.start;
  const tSelfie = w2.start;
  const cfg = {damping: 16, stiffness: 110};
  const toSide = spring({frame: frame - tSide, fps, config: cfg});
  const toZoom = spring({frame: frame - tZoom, fps, config: cfg});
  const toSelfie = spring({frame: frame - tSelfie, fps, config: cfg});

  const tilt = interpolate(toSide, [0, 1], [0, 66]) - toZoom * 20;
  const scale = 1 + toZoom * 1.25 - toSelfie * 0.9;
  const ty = toZoom * 120 - toSelfie * 120;
  const label =
    frame < tSide ? 'TEPADAN • 1x' : frame < tZoom ? 'YONIDAN • 1x' : frame < tSelfie ? 'GO‘SHT • 3x ZOOM' : 'SELFI 🤳';

  const cardIn = spring({frame: frame - 2, fps, config: {damping: 15, stiffness: 80}});

  return (
    <SceneFrame>
      <div
        style={{
          position: 'absolute',
          left: 110,
          top: 150,
          transform: `translateX(${(1 - cardIn) * -900}px) rotate(${(1 - cardIn) * -8}deg)`,
        }}
      >
        <GlassCard glow={scene.accent} radius={44} style={{width: 1000, height: 800}}>
          <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(circle at 50% 55%, #3A2410, #07080D 70%)'}} />
          <HeroVisual
            width={1000}
            height={800}
            radius={0}
            zoom={0.3}
            fallback={
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transform: `translateY(${ty}px) scale(${scale})`,
                }}
              >
                <PlovPlate size={620} tilt={tilt} heat={0.9} spin={frame * 0.05} />
              </div>
            }
            overlay={<Viewfinder label={label} color={scene.accent} />}
          />
          {/* Selfi: oldingi kamera "yuz" */}
          <div
            style={{
              position: 'absolute',
              right: 60,
              bottom: 60,
              fontSize: 220,
              transform: `scale(${toSelfie}) rotate(${(1 - toSelfie) * 40}deg)`,
            }}
          >
            🤳
          </div>
        </GlassCard>
      </div>
      <Flash at={[tSide, tZoom, tSelfie, w2.start + Math.round(w2.duration * 0.45), w2.start + Math.round(w2.duration * 0.75)]} strength={0.55} />

      <div style={{position: 'absolute', left: 1180, top: 190, width: 640}}>
        <KineticText
          text={scene.segments[0].text}
          highlight={scene.segments[0].highlight}
          start={w0.start}
          duration={w0.duration}
          fontSize={76}
          fontWeight={900}
          accent={scene.accent}
          accent2="#ECFEFF"
        />
        <div style={{height: 18}} />
        <KineticText
          text={scene.segments[1].text}
          highlight={scene.segments[1].highlight}
          start={w1.start}
          duration={w1.duration}
          fontSize={60}
          fontWeight={800}
          accent={COLORS.saffron}
          accent2="#FFEDD5"
        />
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 26, marginTop: 50}}>
          <Chip icon="🤳" label="Selfi" color={COLORS.pink} delay={w2.start + Math.round(w2.duration * 0.2)} size={44} />
          <Chip icon="🎵" label="Musiqa" color={COLORS.violet} delay={w2.start + Math.round(w2.duration * 0.45)} size={44} />
          <Chip icon="📍" label="Joylashuv" color={COLORS.green} delay={w2.start + Math.round(w2.duration * 0.72)} size={44} />
        </div>
      </div>
    </SceneFrame>
  );
};
