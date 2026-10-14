import React from 'react';
import {interpolate, spring} from 'remotion';
import {KineticText} from '../components/text/KineticText';
import {HeroVisual} from '../components/media/HeroVisual';
import {PlovPlate} from '../components/visuals/PlovPlate';
import {Avatar, SpeechBubble} from '../components/visuals/ui';
import {clamp, shake} from '../lib/anim';
import {COLORS, FONT_BODY, FONT_DISPLAY} from '../lib/theme';
import {SceneFrame, useSceneBasics} from './shared';

const FIELDS: [string, string][] = [
  ['Ismi', 'Palov (Osh)'],
  ['Tug‘ilgan joyi', 'Qozon, Toshkent'],
  ['Suratlar soni', '147 ta 📸'],
  ['Harorati', '27°C ↓'],
];

export const Scene07Passport: React.FC = () => {
  const {frame, fps, windows, scene} = useSceneBasics();
  const [w0, w1] = windows;
  const bubbleIn = spring({frame: frame - w1.start + 6, fps, config: {damping: 14, stiffness: 140}});
  // "pasport" so'zi taxminan shu yerda aytiladi
  const tPassport = w1.start + Math.round(w1.duration * 0.72);
  const flip = spring({frame: frame - tPassport + 14, fps, config: {damping: 14, stiffness: 90}});
  const tStamp = tPassport + 40;
  const stamp = spring({frame: frame - tStamp, fps, config: {damping: 9, stiffness: 260, mass: 0.9}});
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
        <div
          style={{
            width: 720,
            height: 760,
            borderRadius: 34,
            transform: `rotateY(${interpolate(flip, [0, 1], [-95, -6])}deg) rotateZ(${interpolate(flip, [0, 1], [-8, 3])}deg)`,
            opacity: interpolate(flip, [0, 0.15], [0, 1], clamp),
            background: 'linear-gradient(160deg, #0F3D2E, #062018)',
            border: '2px solid #D4AF37AA',
            boxShadow: `0 60px 120px rgba(0,0,0,0.6), 0 0 140px ${scene.accent}44`,
            padding: 44,
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              position: 'absolute',
              inset: 0,
              backgroundImage: 'repeating-radial-gradient(circle at 80% 10%, rgba(212,175,55,0.08) 0 2px, transparent 2px 22px)',
            }}
          />
          <div style={{position: 'relative', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
            <div style={{fontFamily: FONT_DISPLAY, fontWeight: 900, color: '#F5D77A', fontSize: 46, letterSpacing: 4}}>
              PALOV PASPORTI
            </div>
            <div style={{fontSize: 56}}>🍚</div>
          </div>
          <div style={{position: 'relative', fontFamily: FONT_BODY, color: '#A7F3D0', fontSize: 22, letterSpacing: 6, marginTop: 6}}>
            OSHXONA RESPUBLIKASI • №&nbsp;0001
          </div>
          <div style={{position: 'relative', display: 'flex', gap: 36, marginTop: 40}}>
            <div style={{width: 250, height: 300, borderRadius: 18, background: '#F8FAF5', overflow: 'hidden', position: 'relative'}}>
              <HeroVisual
                width={250}
                height={300}
                radius={0}
                zoom={0.05}
                fallback={
                  <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                    <PlovPlate size={240} tilt={0} heat={0.4} steam={false} />
                  </div>
                }
              />
            </div>
            <div style={{display: 'flex', flexDirection: 'column', gap: 18, flex: 1}}>
              {FIELDS.map(([k, v], i) => {
                const s = spring({frame: frame - tPassport - 6 - i * 6, fps, config: {damping: 200}});
                return (
                  <div key={k} style={{opacity: s, transform: `translateX(${(1 - s) * 30}px)`}}>
                    <div style={{fontFamily: FONT_BODY, fontSize: 20, color: '#6EE7B7', letterSpacing: 3, textTransform: 'uppercase'}}>{k}</div>
                    <div style={{fontFamily: FONT_DISPLAY, fontSize: 34, color: '#F8FAFC', fontWeight: 800}}>{v}</div>
                  </div>
                );
              })}
            </div>
          </div>
          <div
            style={{
              position: 'absolute',
              left: 44,
              right: 44,
              bottom: 40,
              fontFamily: 'monospace',
              fontSize: 26,
              color: '#A7F3D0',
              letterSpacing: 3,
              opacity: 0.85,
            }}
          >
            P&lt;UZBPALOV&lt;&lt;OSH&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;
            <br />
            0001UZB&lt;92C&lt;&lt;SOVUQ&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;
          </div>
          {/* Muhr */}
          <div
            style={{
              position: 'absolute',
              right: 50,
              bottom: 150,
              padding: '14px 30px',
              border: `8px solid ${COLORS.red}`,
              borderRadius: 18,
              color: COLORS.red,
              fontFamily: FONT_DISPLAY,
              fontWeight: 900,
              fontSize: 54,
              letterSpacing: 4,
              transform: `rotate(-14deg) scale(${interpolate(stamp, [0, 1], [3, 1])})`,
              opacity: interpolate(frame - tStamp, [0, 4], [0, 0.92], clamp),
              mixBlendMode: 'screen',
            }}
          >
            TASDIQLANDI
          </div>
        </div>
      </div>
    </SceneFrame>
  );
};
