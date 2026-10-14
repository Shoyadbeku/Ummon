import React from 'react';
import {spring} from 'remotion';
import {KineticText} from '../components/text/KineticText';
import {Avatar, SpeechBubble} from '../components/visuals/ui';
import {shake} from '../lib/anim';
import {SceneFrame, useSceneBasics} from './shared';
import {PassportCard} from '../components/visuals/PassportCard';

export const Scene07Passport: React.FC = () => {
  const {frame, fps, windows, scene} = useSceneBasics();
  const [w0, w1] = windows;
  const bubbleIn = spring({frame: frame - w1.start + 6, fps, config: {damping: 14, stiffness: 140}});
  // "pasport" so'zi taxminan shu yerda aytiladi
  const tPassport = w1.start + Math.round(w1.duration * 0.72);
  const tStamp = tPassport + 40;
  const sh = shake(frame, tStamp + 4, 16, 10);

  return (
    <SceneFrame>
      <div style={{position: 'absolute', left: 130, top: 170, width: 860}}>
        <KineticText
          text={scene.segments[0].text}
          start={w0.start}
          duration={w0.duration}
          fontSize={58}
          fontWeight={700}
          color="#CBD5E1"
        />
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 34,
            marginTop: 50,
            transform: `scale(${bubbleIn})`,
            transformOrigin: '80px 80px',
          }}
        >
          <Avatar emoji="🤨" color={scene.accent} size={150} />
          <SpeechBubble color="#111827" tail="left" style={{border: `2px solid ${scene.accent}88`, maxWidth: 660}}>
            <KineticText
              text={scene.segments[1].text}
              highlight={scene.segments[1].highlight}
              start={w1.start}
              duration={w1.duration}
              fontSize={62}
              fontWeight={800}
              accent={scene.accent}
              accent2="#D1FAE5"
            />
          </SpeechBubble>
        </div>
      </div>

      {/* Pasport karta (3D flip) */}
      <div
        style={{
          position: 'absolute',
          right: 140,
          top: 170,
          perspective: 1800,
          transform: `translate(${sh.x}px, ${sh.y}px)`,
        }}
      >
        <PassportCard tPassport={tPassport} accent={scene.accent} />
      </div>
    </SceneFrame>
  );
};
