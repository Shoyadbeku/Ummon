import React from 'react';
import {interpolate, spring} from 'remotion';
import {KineticText} from '../components/text/KineticText';
import {HeroVisual} from '../components/media/HeroVisual';
import {PlovPlate} from '../components/visuals/PlovPlate';
import {GlassCard, Phone} from '../components/visuals/ui';
import {clamp, float} from '../lib/anim';
import {COLORS, FONT_BODY, FONT_DISPLAY} from '../lib/theme';
import {SceneFrame, useSceneBasics} from './shared';

export const Scene08Posted: React.FC = () => {
  const {frame, fps, windows, scene} = useSceneBasics();
  const [w0, w1] = windows;
  const phoneIn = spring({frame: frame - 2, fps, config: {damping: 15, stiffness: 80}});
  const upload = interpolate(frame, [w0.start, w0.end - 6], [0, 1], clamp);
  const posted = upload >= 1;
  const likes = Math.round(interpolate(frame, [w0.end - 6, w1.end], [0, 1248], {...clamp, easing: (t) => 1 - Math.pow(1 - t, 3)}));
  const coldCard = spring({frame: frame - w1.start, fps, config: {damping: 14, stiffness: 110}});
  const heat = interpolate(frame, [w1.start, w1.end], [0.3, 0.02], clamp);

  return (
    <SceneFrame>
      <div
        style={{
          position: 'absolute',
          left: 250,
          top: 150 + float(frame, 10, 0.04),
          transform: `translateY(${(1 - phoneIn) * 700}px) rotate(-5deg) scale(0.9)`,
          transformOrigin: 'top left',
        }}
      >
        <Phone width={430} glow={scene.accent}>
          <div style={{position: 'absolute', inset: 0, background: '#0B0D14', fontFamily: FONT_BODY, color: COLORS.text}}>
            {/* Yuklash paneli */}
            <div style={{position: 'absolute', top: 70, left: 26, right: 26}}>
              <div style={{fontSize: 20, fontWeight: 700, color: posted ? COLORS.green : COLORS.muted}}>
                {posted ? '✓ Joylandi' : `Joylanmoqda… ${Math.round(upload * 100)}%`}
              </div>
              <div style={{height: 8, borderRadius: 8, background: 'rgba(255,255,255,0.1)', marginTop: 10}}>
                <div
                  style={{
                    width: `${upload * 100}%`,
                    height: '100%',
                    borderRadius: 8,
                    background: `linear-gradient(90deg, ${scene.accent}, ${COLORS.violet})`,
                  }}
                />
              </div>
            </div>
            {/* Post sarlavhasi */}
            <div style={{position: 'absolute', top: 140, left: 26, right: 26, display: 'flex', alignItems: 'center', gap: 14}}>
              <div
                style={{
                  width: 54,
                  height: 54,
                  borderRadius: 27,
                  background: `linear-gradient(135deg, ${scene.accent}, ${COLORS.amber})`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 28,
                }}
              >
                😎
              </div>
              <div>
                <div style={{fontWeight: 700, fontSize: 22}}>palov_ishqibozi</div>
                <div style={{fontSize: 18, color: COLORS.muted}}>📍 Toshkent • 🎵 Lazgi remix</div>
              </div>
            </div>
            <div style={{position: 'absolute', top: 215, left: 0, right: 0, height: 400, overflow: 'hidden', background: '#2A1A0E'}}>
              <HeroVisual
                width={402}
                height={400}
                radius={0}
                zoom={0.08}
                fallback={
                  <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                    <PlovPlate size={420} tilt={0} heat={1} steam={false} style={{filter: 'saturate(1.35) contrast(1.1)'}} />
                  </div>
                }
              />
            </div>
            <div style={{position: 'absolute', top: 640, left: 26, right: 26}}>
              <div style={{display: 'flex', gap: 22, fontSize: 36}}>
                <span style={{transform: `scale(${1 + Math.max(0, Math.sin(frame * 0.3)) * 0.15 * (likes > 0 ? 1 : 0)})`}}>❤️</span>
                <span>💬</span>
                <span>📤</span>
              </div>
              <div style={{fontWeight: 800, fontSize: 26, marginTop: 10, fontVariantNumeric: 'tabular-nums'}}>
                {likes.toLocaleString('en-US')} ta yoqtirish
              </div>
              <div style={{fontSize: 20, color: '#CBD5E1', marginTop: 6}}>Eng mazali palov 😍🔥 #palov #osh</div>
            </div>
          </div>
        </Phone>
      </div>

      {/* Uchuvchi yuraklar */}
      {new Array(10).fill(0).map((_, i) => {
        const t0 = w0.end + i * 12;
        const p = interpolate(frame, [t0, t0 + 70], [0, 1], clamp);
        if (p <= 0 || p >= 1) return null;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: 660 + Math.sin(i * 2.1 + p * 6) * 60,
              top: 760 - p * 520,
              fontSize: 54 + (i % 3) * 14,
              opacity: Math.sin(p * Math.PI),
            }}
          >
            {i % 3 === 0 ? '👍' : '❤️'}
          </div>
        );
      })}

      <div style={{position: 'absolute', left: 860, top: 190, width: 940}}>
        <KineticText
          text={scene.segments[0].text}
          highlight={scene.segments[0].highlight}
          start={w0.start}
          duration={w0.duration}
          fontSize={74}
          accent={scene.accent}
          accent2="#FCE7F3"
        />
        <div style={{height: 22}} />
        <KineticText
          text={scene.segments[1].text}
          highlight={scene.segments[1].highlight}
          start={w1.start}
          duration={w1.duration}
          fontSize={64}
          fontWeight={800}
          color="#CBD5E1"
          accent={COLORS.cold}
          accent2="#E0F2FE"
        />
        <GlassCard
          glow={COLORS.cold}
          radius={32}
          style={{
            marginTop: 40,
            width: 620,
            padding: 30,
            display: 'flex',
            alignItems: 'center',
            gap: 30,
            transform: `scale(${coldCard})`,
            transformOrigin: 'left center',
          }}
        >
          <div style={{fontSize: 96}}>🥶</div>
          <div>
            <div style={{fontFamily: FONT_BODY, fontSize: 24, letterSpacing: 3, color: COLORS.muted}}>HAQIQIY PALOV</div>
            <div style={{fontFamily: FONT_DISPLAY, fontWeight: 900, fontSize: 64, color: COLORS.cold}}>
              {Math.round(interpolate(heat, [0, 1], [16, 60]))}°C ❄️
            </div>
          </div>
        </GlassCard>
      </div>
    </SceneFrame>
  );
};
