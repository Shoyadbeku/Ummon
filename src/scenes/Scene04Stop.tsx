import React from 'react';
import {AbsoluteFill, interpolate, spring} from 'remotion';
import {KineticText} from '../components/text/KineticText';
import {Avatar, SpeechBubble} from '../components/visuals/ui';
import {clamp, shake} from '../lib/anim';
import {COLORS, FONT_DISPLAY} from '../lib/theme';
import {SceneFrame, useSceneBasics} from './shared';

export const Scene04Stop: React.FC = () => {
  const {frame, fps, windows, scene} = useSceneBasics();
  const [w0, w1, w2] = windows;
  const sh = shake(frame, w1.start, 34, 26);
  const hand = spring({frame: frame - w1.start + 4, fps, config: {damping: 8, stiffness: 200, mass: 0.8}});
  const bubble = spring({frame: frame - w2.start + 4, fps, config: {damping: 12, stiffness: 160}});
  const pulse = interpolate(frame - w1.start, [0, 4, 30], [0, 0.55, 0], clamp);
  const ringScale = interpolate(frame - w1.start, [0, 40], [0.2, 2.2], clamp);
  const ringOpacity = interpolate(frame - w1.start, [0, 40], [0.8, 0], clamp);

  return (
    <SceneFrame>
      <AbsoluteFill style={{background: COLORS.red, opacity: pulse, mixBlendMode: 'screen'}} />
      {/* Ogohlantirish chiziqlari */}
      <AbsoluteFill
        style={{
          opacity: interpolate(frame - w1.start, [0, 10], [0, 0.12], clamp),
          backgroundImage: `repeating-linear-gradient(-45deg, ${COLORS.red} 0 40px, transparent 40px 80px)`,
          backgroundPosition: `${frame * 2}px 0`,
        }}
      />
      <div style={{position: 'absolute', inset: 0, transform: `translate(${sh.x}px, ${sh.y}px) rotate(${sh.r}deg)`}}>
        <div style={{position: 'absolute', top: 170, left: 0, right: 0}}>
          <KineticText
            text={scene.segments[0].text}
            start={w0.start}
            duration={w0.duration}
            align="center"
            fontSize={58}
            fontWeight={700}
            color="#CBD5E1"
          />
        </div>

        <div
          style={{
            position: 'absolute',
            left: 960 - 300,
            top: 540 - 300,
            width: 600,
            height: 600,
            borderRadius: '50%',
            border: `10px solid ${COLORS.red}`,
            transform: `scale(${ringScale})`,
            opacity: ringOpacity,
          }}
        />

        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: 300,
            textAlign: 'center',
            fontSize: 220,
            transform: `scale(${hand}) rotate(${interpolate(hand, [0, 1], [-40, -8])}deg)`,
            opacity: 0.95,
          }}
        >
          ✋
        </div>

        <div style={{position: 'absolute', top: 530, left: 0, right: 0}}>
          <KineticText
            text={scene.segments[1].text.replace('— ', '').toUpperCase()}
            highlight={['TO‘XTANGLAR!']}
            start={w1.start}
            duration={6}
            mode="slam"
            align="center"
            fontSize={190}
            fontWeight={900}
            accent={COLORS.red}
            accent2="#FECACA"
            letterSpacing={-6}
            style={{textShadow: 'none'}}
          />
        </div>

        <div
          style={{
            position: 'absolute',
            left: 960 - 520,
            top: 790,
            display: 'flex',
            alignItems: 'center',
            gap: 40,
            transform: `scale(${bubble})`,
            transformOrigin: '120px 50%',
          }}
        >
          <Avatar emoji="😱" color={COLORS.red} size={150} />
          <SpeechBubble color="#F8FAFC" tail="left">
            <div style={{fontFamily: FONT_DISPLAY, fontWeight: 900, fontSize: 60, color: '#0F172A'}}>
              {scene.segments[2].text} 📵
            </div>
          </SpeechBubble>
        </div>
      </div>
    </SceneFrame>
  );
};
