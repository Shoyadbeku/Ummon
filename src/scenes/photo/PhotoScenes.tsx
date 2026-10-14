import React, {useMemo} from 'react';
import {AbsoluteFill, interpolate, random, spring} from 'remotion';
import {CARD, cardPoint, PhotoStage} from '../../components/media/PhotoStage';
import {CHARACTERS, type CharacterId} from '../../components/media/characters';
import {Caption} from '../../components/text/Caption';
import {KineticText} from '../../components/text/KineticText';
import {PassportCard} from '../../components/visuals/PassportCard';
import {Steam} from '../../components/visuals/Steam';
import {Avatar, Chip, Flash, GlassCard, SceneTag, SpeechBubble, Thermometer, Viewfinder} from '../../components/visuals/ui';
import {SCENES} from '../../data/script';
import {clamp, float, shake} from '../../lib/anim';
import {COLORS, FONT_BODY, FONT_DISPLAY} from '../../lib/theme';
import {useSceneBasics} from '../shared';

/* ───────────── Umumiy yordamchilar ───────────── */

const Tag: React.FC = () => {
  const {scene, index} = useSceneBasics();
  return (
    <div style={{position: 'absolute', left: 64, top: 60}}>
      <SceneTag index={index} total={SCENES.length} label={scene.title} color={scene.accent} />
    </div>
  );
};

/** Personaj avatari — spring bilan "stiker" kabi yopishadi */
const CharacterPop: React.FC<{
  id: CharacterId;
  at: number;
  x: number;
  y: number;
  size?: number;
  children?: React.ReactNode;
  bubbleSide?: 'left' | 'right';
}> = ({id, at, x, y, size = 150, children, bubbleSide = 'right'}) => {
  const {frame, fps} = useSceneBasics();
  const c = CHARACTERS[id];
  const s = spring({frame: frame - at, fps, config: {damping: 11, stiffness: 170, mass: 0.7}});
  const b = spring({frame: frame - at - 8, fps, config: {damping: 13, stiffness: 160}});
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y + float(frame, 6, 0.06, x),
        display: 'flex',
        flexDirection: bubbleSide === 'right' ? 'row' : 'row-reverse',
        alignItems: 'center',
        gap: 30,
      }}
    >
      <div style={{transform: `scale(${s}) rotate(${(1 - s) * -25}deg)`}}>
        <Avatar src={c.src} color={c.color} size={size} />
      </div>
      {children && (
        <div style={{transform: `scale(${b})`, transformOrigin: bubbleSide === 'right' ? 'left center' : 'right center'}}>
          <SpeechBubble color="#FFFFFF" tail={bubbleSide === 'right' ? 'left' : 'right'} style={{padding: '24px 36px'}}>
            <div style={{fontFamily: FONT_DISPLAY, fontWeight: 900, fontSize: 44, color: '#0F172A', whiteSpace: 'nowrap'}}>
              {children}
            </div>
          </SpeechBubble>
        </div>
      )}
    </div>
  );
};

/** Emoji stiker (oq chegara bilan) */
const Sticker: React.FC<{emoji: string; at: number; x: number; y: number; size?: number; rot?: number}> = ({
  emoji,
  at,
  x,
  y,
  size = 130,
  rot = -12,
}) => {
  const {frame, fps} = useSceneBasics();
  const s = spring({frame: frame - at, fps, config: {damping: 9, stiffness: 170}});
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y + float(frame, 8, 0.07, y),
        fontSize: size,
        transform: `scale(${s}) rotate(${interpolate(s, [0, 1], [rot * 4, rot])}deg)`,
        filter:
          'drop-shadow(4px 0 0 #fff) drop-shadow(-4px 0 0 #fff) drop-shadow(0 4px 0 #fff) drop-shadow(0 -4px 0 #fff) drop-shadow(0 18px 24px rgba(0,0,0,0.45))',
      }}
    >
      {emoji}
    </div>
  );
};

/** Rasm ichidagi nuqtadan ko'tariladigan bug' (karta koordinatalarida) */
const SteamAt: React.FC<{px: number; py: number; w?: number; h?: number; heat?: number}> = ({px, py, w = 360, h = 420, heat = 1}) => (
  <Steam
    heat={heat}
    width={w}
    height={h}
    wisps={6}
    style={{position: 'absolute', left: px * (CARD.w - 20) - w / 2, top: py * (CARD.h - 20) - h}}
  />
);

/* ───────────── 01 — Hook ───────────── */

export const Photo01Hook: React.FC = () => {
  const {frame, windows, scene} = useSceneBasics();
  const [w0, w1] = windows;
  const sh = shake(frame, w0.start + 4, 22, 12);
  return (
    <AbsoluteFill style={{transform: `translate(${sh.x}px, ${sh.y}px)`}}>
      <PhotoStage accent={scene.accent} inCard={<Viewfinder label="FOTO • 148-KADR" color={scene.accent} />} />
      <Tag />
      <Sticker emoji="😂" at={w1.start + 10} x={CARD.x + CARD.w - 70} y={CARD.y + 90} />
      <Sticker emoji="📸" at={w1.end - 4} x={CARD.x - 90} y={CARD.y + 330} rot={14} />
      <div style={{position: 'absolute', right: 80, top: 360}}>
        <Chip icon="🌡️" label="31°C ↓" color={COLORS.cold} delay={w1.start} size={36} />
      </div>
      <Caption
        styles={[
          {mode: 'slam', uppercase: true, size: 92},
          {size: 72, accent: COLORS.cyan},
        ]}
      />
      <Flash at={[w1.end + 6]} strength={0.7} />
    </AbsoluteFill>
  );
};

/* ───────────── 02 — Fotosessiya ───────────── */

export const Photo02Intro: React.FC = () => {
  const {windows, scene} = useSceneBasics();
  const [w0, w1] = windows;
  return (
    <AbsoluteFill>
      <PhotoStage accent={scene.accent} camera={(f) => ({scale: interpolate(f, [0, 500], [1.02, 1.16], clamp), originX: 50, originY: 70})} />
      <Tag />
      <div style={{position: 'absolute', left: 120, top: 250}}>
        <Chip icon="🍽️" label="Restoran • 13:05" color={COLORS.amber} delay={w0.start + 10} size={34} />
      </div>
      <div style={{position: 'absolute', right: 110, top: 420}}>
        <Chip icon="📸" label="Fotosessiya" color={scene.accent} delay={w1.start + 20} size={40} />
      </div>
      <CharacterPop id="fotograf" at={w1.start + Math.round(w1.duration * 0.55)} x={CARD.x + CARD.w - 80} y={CARD.y + 40} size={140} />
      <Caption />
    </AbsoluteFill>
  );
};

/* ───────────── 03 — Issiq palov ───────────── */

export const Photo03HotPlov: React.FC = () => {
  const {frame, windows, scene} = useSceneBasics();
  const [w0, w1, w2] = windows;
  const temp = Math.round(interpolate(frame, [w0.start, w1.end], [40, 92], clamp));
  return (
    <AbsoluteFill>
      <PhotoStage
        accent={scene.accent}
        camera={(f) => ({scale: interpolate(f, [0, 400], [1.12, 1.02], clamp), originX: 42, originY: 70})}
        inCard={
          <>
            <SteamAt px={0.38} py={0.72} />
            <SteamAt px={0.55} py={0.72} w={300} />
          </>
        }
      />
      <Tag />
      <CharacterPop id="ofitsiant" at={w0.start + 6} x={60} y={250} size={140}>
        Marhamat! 🍽️
      </CharacterPop>
      <div style={{position: 'absolute', right: 90, top: 300}}>
        <Chip icon="🌡️" label={`${temp}°C`} color={COLORS.saffron} delay={w0.start} size={46} />
      </div>
      <div style={{position: 'absolute', right: 90, top: 420}}>
        <Chip icon="♨️" label="Bug‘ chiqyapti" color={scene.accent} delay={w1.start} size={32} />
      </div>
      {[0, 1, 2, 3].map((i) => (
        <Sticker key={i} emoji="🥄" at={w2.start + i * 6} x={[260, 1560, 330, 1500][i]} y={[620, 600, 420, 780][i]} size={90} rot={[-30, 30, -50, 45][i]} />
      ))}
      <Caption />
    </AbsoluteFill>
  );
};

/* ───────────── 04 — To'xtanglar! ───────────── */

export const Photo04Stop: React.FC = () => {
  const {frame, fps, windows, scene} = useSceneBasics();
  const [, w1, w2] = windows;
  const sh = shake(frame, w1.start, 34, 24);
  const pulse = interpolate(frame - w1.start, [0, 4, 30], [0, 0.5, 0], clamp);
  const word = spring({frame: frame - w1.start, fps, config: {damping: 10, stiffness: 240}});
  const wordOut = interpolate(frame, [w2.start, w2.start + 16], [1, 0], clamp);
  return (
    <AbsoluteFill style={{transform: `translate(${sh.x}px, ${sh.y}px) rotate(${sh.r * 0.5}deg)`}}>
      <PhotoStage
        accent={scene.accent}
        camera={(f) => ({scale: f < w1.start ? 1.03 : 1.03 + spring({frame: f - w1.start, fps, config: {damping: 14}}) * 0.18, originX: 50, originY: 32})}
      />
      <AbsoluteFill style={{background: COLORS.red, opacity: pulse, mixBlendMode: 'screen'}} />
      <Tag />
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 420,
          textAlign: 'center',
          fontFamily: FONT_DISPLAY,
          fontWeight: 900,
          fontSize: 200,
          letterSpacing: -6,
          color: '#FFFFFF',
          WebkitTextStroke: `10px ${COLORS.red}`,
          paintOrder: 'stroke fill',
          textShadow: '0 20px 60px rgba(0,0,0,0.6)',
          opacity: interpolate(frame - w1.start, [0, 3], [0, 1], clamp) * wordOut,
          transform: `scale(${interpolate(word, [0, 1], [2.6, 1])}) rotate(-4deg)`,
        }}
      >
        TO‘XTANGLAR!
      </div>
      <Sticker emoji="✋" at={w1.start - 2} x={1640} y={520} size={170} rot={18} />
      <CharacterPop id="fotograf" at={w2.start - 4} x={60} y={150} size={150} bubbleSide="right">
        Hali suratga olmadim! 📵
      </CharacterPop>
      <Caption styles={[{size: 56}, {mode: 'slam', uppercase: true, size: 84, accent: COLORS.red, accent2: '#FECACA'}, {size: 64}]} />
    </AbsoluteFill>
  );
};

/* ───────────── 05 — Fotosessiya boshlandi ───────────── */

export const Photo05Photoshoot: React.FC = () => {
  const {frame, fps, windows, scene} = useSceneBasics();
  const [w0, w1, w2] = windows;
  const tSide = w0.start + Math.round(w0.duration * 0.5);
  const tZoom = w1.start;
  const tSelfie = w2.start;
  const label = frame < tSide ? 'TEPADAN • 1x' : frame < tZoom ? 'YONIDAN • 1.5x' : frame < tSelfie ? 'GO‘SHT • 3x ZOOM' : 'SELFI 🤳';
  return (
    <AbsoluteFill>
      <PhotoStage
        accent={scene.accent}
        switchAt={[tSelfie]}
        camera={(f, idx) => {
          if (idx === 1) return {scale: interpolate(f, [tSelfie, tSelfie + 300], [1.02, 1.12], clamp), originX: 72, originY: 35};
          const side = spring({frame: f - tSide, fps, config: {damping: 16}});
          const zoom = spring({frame: f - tZoom, fps, config: {damping: 16}});
          return {scale: 1.02 + side * 0.25 + zoom * 1.1, originX: 50, originY: 74};
        }}
        inCard={<Viewfinder label={label} color={scene.accent} />}
      />
      <Flash at={[tSide, tZoom, tSelfie, w2.start + Math.round(w2.duration * 0.45), w2.start + Math.round(w2.duration * 0.75)]} strength={0.5} />
      <Tag />
      <div style={{position: 'absolute', right: 70, top: 200, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 22}}>
        <Chip icon="🤳" label="Selfi" color={COLORS.pink} delay={w2.start + Math.round(w2.duration * 0.2)} size={40} />
        <Chip icon="🎵" label="Musiqa" color={COLORS.violet} delay={w2.start + Math.round(w2.duration * 0.45)} size={40} />
        <Chip icon="📍" label="Joylashuv" color={COLORS.green} delay={w2.start + Math.round(w2.duration * 0.72)} size={40} />
      </div>
      <Caption />
    </AbsoluteFill>
  );
};

/* ───────────── 06 — Palov soviyapti ───────────── */

export const Photo06Waiting: React.FC = () => {
  const {frame, windows, scene, timing} = useSceneBasics();
  const [w0, w1] = windows;
  const heat = interpolate(frame, [w0.start, w1.end], [1, 0.05], clamp);
  const temp = Math.round(interpolate(heat, [0, 1], [24, 92]));
  const minutes = Math.round(interpolate(frame, [0, timing.durationInFrames - 30], [0, 25], clamp));
  const snow = useMemo(
    () => new Array(36).fill(0).map((_, i) => ({x: random(`psx${i}`) * 1920, s: 0.6 + random(`pss${i}`), d: random(`psd${i}`) * 200})),
    [],
  );
  return (
    <AbsoluteFill>
      <PhotoStage
        accent={scene.accent}
        filter={`saturate(${0.55 + heat * 0.45}) hue-rotate(${(1 - heat) * 18}deg) brightness(${0.85 + heat * 0.15})`}
        inCard={<AbsoluteFill style={{background: COLORS.cold, opacity: (1 - heat) * 0.18, mixBlendMode: 'color'}} />}
      />
      <Tag />
      <div style={{position: 'absolute', right: 70, top: 170, transform: 'scale(0.8)', transformOrigin: 'top right'}}>
        <Thermometer value={heat} height={460} label={`${temp}°C`} />
      </div>
      <div style={{position: 'absolute', left: 50, top: 190, display: 'flex', flexDirection: 'column', gap: 18}}>
        {(['yashil', 'qizil', 'kok'] as CharacterId[]).map((id, i) => (
          <CharacterPop key={id} id={id} at={8 + i * 8} x={0} y={i * 150} size={120} />
        ))}
      </div>
      <div style={{position: 'absolute', left: 60, top: 660}}>
        <GlassCard style={{padding: '20px 30px'}} radius={24}>
          <div style={{fontFamily: FONT_BODY, color: COLORS.muted, fontSize: 20, fontWeight: 600, letterSpacing: 3}}>KUTISH</div>
          <div style={{fontFamily: FONT_DISPLAY, color: COLORS.text, fontSize: 48, fontWeight: 900, fontVariantNumeric: 'tabular-nums'}}>
            ⏰ {minutes} daq
          </div>
        </GlassCard>
      </div>
      {snow.map((p, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: p.x + Math.sin(frame * 0.03 + i) * 30,
            top: ((frame * 2.2 * p.s + p.d * 6) % 1200) - 100,
            fontSize: 22 * p.s,
            opacity: interpolate(frame, [w1.start, w1.start + 40], [0, 0.6], clamp),
          }}
        >
          ❄️
        </div>
      ))}
      <Caption styles={[{size: 62}, {size: 72, accent: COLORS.cold, accent2: '#E0F2FE'}]} />
    </AbsoluteFill>
  );
};

/* ───────────── 07 — Palov pasporti ───────────── */

export const Photo07Passport: React.FC = () => {
  const {frame, windows, scene} = useSceneBasics();
  const [w0, w1] = windows;
  const tPassport = w1.start + Math.round(w1.duration * 0.72);
  const sh = shake(frame, tPassport + 44, 16, 10);
  const dim = interpolate(frame, [tPassport - 10, tPassport + 10], [0, 0.45], clamp);
  return (
    <AbsoluteFill>
      <PhotoStage accent={scene.accent} camera={(f) => ({scale: interpolate(f, [0, 450], [1.02, 1.14], clamp), originX: 80, originY: 45})} />
      <AbsoluteFill style={{background: '#000', opacity: dim}} />
      <Tag />
      <CharacterPop id="kok" at={w0.start + 4} x={1500} y={160} size={150} bubbleSide="left">
        🤨
      </CharacterPop>
      <div
        style={{
          position: 'absolute',
          left: 600,
          top: 90,
          transform: `translate(${sh.x}px, ${sh.y}px) scale(0.86)`,
          transformOrigin: 'top center',
          perspective: 1800,
        }}
      >
        <PassportCard tPassport={tPassport} accent={scene.accent} photo="avatars/palov.jpg" />
      </div>
      <Caption styles={[{size: 54}, {size: 60}]} />
    </AbsoluteFill>
  );
};

/* ───────────── 08 — Joylandi ───────────── */

export const Photo08Posted: React.FC = () => {
  const {frame, windows, scene} = useSceneBasics();
  const [w0, w1] = windows;
  const upload = interpolate(frame, [w0.start, w0.end - 6], [0, 1], clamp);
  const likes = Math.round(interpolate(frame, [w0.end - 6, w1.end], [0, 1248], {...clamp, easing: (t) => 1 - Math.pow(1 - t, 3)}));
  const phone = cardPoint(0.66, 0.72);
  return (
    <AbsoluteFill>
      <PhotoStage
        accent={scene.accent}
        camera={(f) => ({scale: interpolate(f, [0, 450], [1.03, 1.15], clamp), originX: 60, originY: 60})}
        filter={`saturate(${interpolate(frame, [w1.start, w1.end], [1, 0.7], clamp)})`}
      />
      <Tag />
      {/* Yuklash holati */}
      <div style={{position: 'absolute', left: CARD.x + 40, top: CARD.y + 30}}>
        <GlassCard radius={24} style={{padding: '18px 26px', width: 430}}>
          <div style={{fontFamily: FONT_BODY, fontWeight: 700, fontSize: 24, color: upload >= 1 ? COLORS.green : COLORS.text}}>
            {upload >= 1 ? '✓ Internetga joylandi!' : `⬆️ Joylanmoqda… ${Math.round(upload * 100)}%`}
          </div>
          <div style={{height: 10, borderRadius: 10, background: 'rgba(255,255,255,0.15)', marginTop: 12}}>
            <div style={{width: `${upload * 100}%`, height: '100%', borderRadius: 10, background: `linear-gradient(90deg, ${scene.accent}, ${COLORS.violet})`}} />
          </div>
        </GlassCard>
      </div>
      <div style={{position: 'absolute', right: 70, top: 260}}>
        <Chip icon="❤️" label={likes.toLocaleString('en-US')} color={COLORS.pink} delay={w0.end - 10} size={44} />
      </div>
      <div style={{position: 'absolute', right: 70, top: 380}}>
        <Chip icon="🥶" label="16°C" color={COLORS.cold} delay={w1.start + Math.round(w1.duration * 0.5)} size={44} />
      </div>
      {new Array(12).fill(0).map((_, i) => {
        const t0 = w0.end + i * 10;
        const p = interpolate(frame, [t0, t0 + 70], [0, 1], clamp);
        if (p <= 0 || p >= 1) return null;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: phone.x + Math.sin(i * 2.1 + p * 6) * 70,
              top: phone.y - p * 420,
              fontSize: 50 + (i % 3) * 14,
              opacity: Math.sin(p * Math.PI),
            }}
          >
            {i % 3 === 0 ? '👍' : '❤️'}
          </div>
        );
      })}
      <Caption styles={[{size: 64}, {size: 64, accent: COLORS.cold, accent2: '#E0F2FE'}]} />
    </AbsoluteFill>
  );
};

/* ───────────── 09 — Eng yaxshi filtr ───────────── */

const FILTERS = [
  {name: 'Oddiy', icon: '🍚'},
  {name: 'Yorqin', icon: '🌈'},
  {name: 'Retro', icon: '📼'},
  {name: 'Bug‘', icon: '♨️'},
];

export const Photo09Moral: React.FC = () => {
  const {frame, fps, windows, scene} = useSceneBasics();
  const [w0, w1, w2] = windows;
  const sel = interpolate(frame, [w0.start, w0.end, w1.start + 6], [0, 2, 3], {...clamp, easing: (t) => t * t * (3 - 2 * t)});
  const glow = 0.5 + 0.5 * Math.sin(frame * 0.08);
  return (
    <AbsoluteFill>
      <PhotoStage
        accent={scene.accent}
        camera={(f) => ({scale: interpolate(f, [0, 420], [1.02, 1.2], clamp), originX: 70, originY: 35})}
        inCard={
          <>
            <div
              style={{
                position: 'absolute',
                left: 0.79 * CARD.w - 300,
                top: 0.25 * CARD.h - 220,
                width: 600,
                height: 440,
                borderRadius: '50%',
                background: `radial-gradient(ellipse, ${scene.accent}88, transparent 65%)`,
                opacity: 0.5 + glow * 0.4,
                mixBlendMode: 'screen',
              }}
            />
            <SteamAt px={0.79} py={0.26} w={340} h={360} />
          </>
        }
      />
      <Tag />
      <div style={{position: 'absolute', right: 60, top: 420}}>
        <Chip icon="✨" label="Eng yaxshi filtr" color={scene.accent} delay={w1.start} size={32} />
      </div>
      <div style={{position: 'absolute', left: 60, top: 200, display: 'flex', flexDirection: 'column', gap: 18}}>
        {FILTERS.map((f, i) => {
          const s = spring({frame: frame - 10 - i * 5, fps, config: {damping: 14}});
          const active = Math.max(0, 1 - Math.abs(sel - i));
          return (
            <div key={f.name} style={{display: 'flex', alignItems: 'center', gap: 14, transform: `scale(${s * (1 + active * 0.15)})`, transformOrigin: 'left center'}}>
              <div
                style={{
                  width: 96,
                  height: 96,
                  borderRadius: 24,
                  border: `4px solid ${active > 0.5 ? scene.accent : 'rgba(255,255,255,0.25)'}`,
                  boxShadow: active > 0.5 ? `0 0 40px ${scene.accent}` : '0 10px 30px rgba(0,0,0,0.4)',
                  background: ['#5B4636', '#C2410C', '#78716C', '#EA580C'][i],
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 50,
                }}
              >
                {f.icon}
              </div>
              <div style={{fontFamily: FONT_BODY, fontWeight: 700, fontSize: 24, color: active > 0.5 ? COLORS.text : COLORS.muted}}>{f.name}</div>
            </div>
          );
        })}
      </div>
      <div style={{position: 'absolute', right: 60, top: 540}}>
        <Chip icon="🔥" label="Issiq = Mazali" color={COLORS.red} delay={w2.start + Math.round(w2.duration * 0.6)} size={34} />
      </div>
      <Caption styles={[{size: 60}, {mode: 'slam', uppercase: true, size: 88}, {size: 64, accent: COLORS.red, accent2: '#FED7AA'}]} />
    </AbsoluteFill>
  );
};

/* ───────────── 10 — Savol ───────────── */

const PollOption: React.FC<{id: CharacterId; title: string; icon: string; color: string; delay: number; percent: number; side: -1 | 1}> = ({
  id,
  title,
  icon,
  color,
  delay,
  percent,
  side,
}) => {
  const {frame, fps} = useSceneBasics();
  const s = spring({frame: frame - delay, fps, config: {damping: 13, stiffness: 110}});
  return (
    <div style={{transform: `translateX(${(1 - s) * side * 600}px) rotate(${(1 - s) * side * 10}deg)`, opacity: s}}>
      <GlassCard glow={color} radius={40} style={{width: 600, padding: '34px 40px', background: 'rgba(10,14,28,0.85)'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 26}}>
          <Avatar src={CHARACTERS[id].src} color={color} size={130} />
          <div style={{fontFamily: FONT_DISPLAY, fontWeight: 900, fontSize: 54, color: COLORS.text, lineHeight: 1.05}}>
            {icon} {title}
          </div>
        </div>
        <div style={{marginTop: 28, height: 20, borderRadius: 20, background: 'rgba(255,255,255,0.1)'}}>
          <div style={{width: `${percent}%`, height: '100%', borderRadius: 20, background: `linear-gradient(90deg, ${color}, #fff)`, boxShadow: `0 0 30px ${color}`}} />
        </div>
        <div style={{marginTop: 10, fontFamily: FONT_BODY, fontWeight: 700, fontSize: 28, color: COLORS.muted}}>{Math.round(percent)}%</div>
      </GlassCard>
    </div>
  );
};

export const Photo10Question: React.FC = () => {
  const {frame, fps, windows, scene} = useSceneBasics();
  const [, , w2] = windows;
  const pollAt = w2.end - 10;
  const dim = interpolate(frame, [pollAt - 10, pollAt + 10], [0, 0.55], clamp);
  const base = interpolate(frame, [pollAt + 10, pollAt + 70], [0, 1], clamp);
  const a = 50 + Math.sin(frame * 0.05) * 9 * base;
  const vs = spring({frame: frame - pollAt - 6, fps, config: {damping: 8, stiffness: 200}});
  const cta = spring({frame: frame - pollAt - 24, fps, config: {damping: 12, stiffness: 140}});
  return (
    <AbsoluteFill>
      <PhotoStage accent={scene.accent} camera={(f) => ({scale: interpolate(f, [0, 420], [1.02, 1.12], clamp), originX: 50, originY: 50})} />
      <AbsoluteFill style={{background: '#05070D', opacity: dim}} />
      <Tag />
      <div style={{position: 'absolute', left: 0, right: 0, top: 110, textAlign: 'center', opacity: base}}>
        <KineticText
          text="Siz qaysi birisiz?"
          start={pollAt}
          duration={20}
          align="center"
          fontSize={84}
          fontWeight={900}
          mode="pop"
          highlight={['qaysi']}
          accent={scene.accent}
          accent2="#EDE9FE"
        />
      </div>
      {frame > pollAt - 10 && (
        <div style={{position: 'absolute', top: 300, left: 0, right: 0, display: 'flex', justifyContent: 'center', gap: 110}}>
          <PollOption id="yashil" title="Avval ovqat" icon="🍽️" color={COLORS.amber} delay={pollAt} percent={a * base} side={-1} />
          <PollOption id="fotograf" title="Avval surat" icon="📸" color={COLORS.cyan} delay={pollAt + 8} percent={(100 - a) * base} side={1} />
        </div>
      )}
      <div
        style={{
          position: 'absolute',
          left: 960 - 70,
          top: 400,
          width: 140,
          height: 140,
          borderRadius: '50%',
          background: `linear-gradient(135deg, ${scene.accent}, ${COLORS.pink})`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: FONT_DISPLAY,
          fontWeight: 900,
          fontSize: 54,
          color: '#fff',
          border: '6px solid #fff',
          boxShadow: `0 0 80px ${scene.accent}`,
          transform: `scale(${vs}) rotate(${(1 - vs) * 180}deg)`,
        }}
      >
        VS
      </div>
      <Caption hideAfter={pollAt} styles={[{size: 56}, {size: 70, accent: COLORS.amber}, {size: 70, accent: COLORS.cyan}]} />
      <div
        style={{
          position: 'absolute',
          bottom: 90,
          left: 0,
          right: 0,
          display: 'flex',
          justifyContent: 'center',
          opacity: cta,
          transform: `translateY(${(1 - cta) * 60}px) scale(${1 + Math.sin(frame * 0.15) * 0.04})`,
        }}
      >
        <div
          style={{
            padding: '26px 60px',
            borderRadius: 80,
            background: `linear-gradient(90deg, ${scene.accent}, ${COLORS.pink})`,
            fontFamily: FONT_DISPLAY,
            fontWeight: 900,
            fontSize: 48,
            color: '#fff',
            border: '5px solid #fff',
            boxShadow: `0 20px 60px ${scene.accent}88`,
          }}
        >
          💬 Javobingizni izohlarda yozing! 👇
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const PHOTO_SCENES: Record<string, React.FC> = {
  '01-hook': Photo01Hook,
  '02-intro': Photo02Intro,
  '03-hot-plov': Photo03HotPlov,
  '04-stop': Photo04Stop,
  '05-photoshoot': Photo05Photoshoot,
  '06-waiting': Photo06Waiting,
  '07-passport': Photo07Passport,
  '08-posted': Photo08Posted,
  '09-moral': Photo09Moral,
  '10-question': Photo10Question,
};
