import React from 'react';
import {interpolate, spring} from 'remotion';
import {KineticText} from '../components/text/KineticText';
import {HeroVisual} from '../components/media/HeroVisual';
import {PlovPlate} from '../components/visuals/PlovPlate';
import {Flash, Phone, Viewfinder} from '../components/visuals/ui';
import {float, shake} from '../lib/anim';
import {COLORS} from '../lib/theme';
import {SceneFrame, useSceneBasics} from './shared';

export const Scene01Hook: React.FC = () => {
  const {frame, fps, windows, scene} = useSceneBasics();
  const [w0, w1] = windows;
  const sh = shake(frame, w0.start + 4, 22, 14);

  const phoneIn = spring({frame: frame - 6, fps, config: {damping: 14, stiffness: 90}});
  const sticker1 = spring({frame: frame - w1.start - 6, fps, config: {damping: 9, stiffness: 160}});
  const sticker2 = spring({frame: frame - w1.end + 6, fps, config: {damping: 9, stiffness: 160}});

  return (
    <SceneFrame>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `translate(${sh.x}px, ${sh.y}px) rotate(${sh.r}deg)`,
        }}
      >
        <div style={{position: 'absolute', left: 130, top: 250, width: 1050}}>
          <KineticText
            text={scene.segments[0].text.toUpperCase()}
            highlight={['SOVIDI,']}
            start={w0.start}
            duration={w0.duration}
            mode="slam"
            fontSize={168}
            fontWeight={900}
            accent={scene.accent}
            accent2="#FFE4B5"
            letterSpacing={-4}
            lineHeight={1}
          />
          <div style={{height: 34}} />
          <KineticText
            text={scene.segments[1].text}
            highlight={['surat']}
            start={w1.start}
            duration={w1.duration}
            mode="rise"
            fontSize={92}
            accent={COLORS.cyan}
            accent2="#E0F2FE"
            maxWidth={1000}
          />
        </div>

        {/* Telefon + palov (parallaks: telefon sekinroq suzadi) */}
        <div
          style={{
            position: 'absolute',
            right: 190,
            top: 120 + float(frame, 14, 0.035),
            transform: `translateX(${(1 - phoneIn) * 600}px) rotate(${interpolate(phoneIn, [0, 1], [24, 8])}deg)`,
          }}
        >
          <Phone width={400} glow={scene.accent}>
            <HeroVisual
              width={372}
              height={792}
              radius={0}
              fallback={
                <div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: 'radial-gradient(circle, #3B2412, #0B0B10 75%)',
                  }}
                >
                  <PlovPlate size={340} tilt={30} spin={frame * 0.15} heat={1} />
                </div>
              }
              overlay={<Viewfinder label="FOTO" />}
            />
          </Phone>
        </div>

        <div
          style={{
            position: 'absolute',
            right: 80,
            top: 210,
            fontSize: 150,
            transform: `scale(${sticker1}) rotate(${interpolate(sticker1, [0, 1], [-60, -12])}deg)`,
          }}
        >
          😂
        </div>
        <div
          style={{
            position: 'absolute',
            right: 520,
            top: 760,
            fontSize: 140,
            transform: `scale(${sticker2}) rotate(${interpolate(sticker2, [0, 1], [60, 14])}deg)`,
          }}
        >
          📸
        </div>
      </div>
      <Flash at={[w1.end + 6]} strength={0.7} />
    </SceneFrame>
  );
};
