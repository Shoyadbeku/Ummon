import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {clamp} from '../../lib/anim';
import {COLORS, FONT_BODY, FONT_DISPLAY} from '../../lib/theme';

/** Shisha (glassmorphism) karta */
export const GlassCard: React.FC<{
  children: React.ReactNode;
  style?: React.CSSProperties;
  glow?: string;
  radius?: number;
}> = ({children, style, glow, radius = 36}) => (
  <div
    style={{
      position: 'relative',
      borderRadius: radius,
      background: 'linear-gradient(145deg, rgba(255,255,255,0.12), rgba(255,255,255,0.03))',
      border: `1.5px solid ${COLORS.panelBorder}`,
      boxShadow: `0 40px 90px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.18)${
        glow ? `, 0 0 120px ${glow}55` : ''
      }`,
      backdropFilter: 'blur(18px)',
      overflow: 'hidden',
      ...style,
    }}
  >
    {children}
  </div>
);

/** Kichik "pill" yorliq: ikonka + matn, spring bilan chiqadi */
export const Chip: React.FC<{
  icon: string;
  label: string;
  color: string;
  delay: number;
  size?: number;
  style?: React.CSSProperties;
}> = ({icon, label, color, delay, size = 40, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: frame - delay, fps, config: {damping: 12, stiffness: 180, mass: 0.6}});
  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: size * 0.4,
        padding: `${size * 0.35}px ${size * 0.7}px`,
        borderRadius: size * 2,
        background: `linear-gradient(135deg, ${color}33, ${color}11)`,
        border: `2px solid ${color}AA`,
        boxShadow: `0 0 40px ${color}44`,
        color: COLORS.text,
        fontFamily: FONT_DISPLAY,
        fontWeight: 800,
        fontSize: size,
        transform: `scale(${s}) translateY(${(1 - s) * 30}px)`,
        opacity: interpolate(frame - delay, [0, 6], [0, 1], clamp),
        whiteSpace: 'nowrap',
        ...style,
      }}
    >
      <span>{icon}</span>
      <span>{label}</span>
    </div>
  );
};

/** Sahna yorlig'i (eyebrow): "03 / 10 • ISSIQ PALOV" */
export const SceneTag: React.FC<{index: number; total: number; label: string; color: string; delay?: number}> = ({
  index,
  total,
  label,
  color,
  delay = 4,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: frame - delay, fps, config: {damping: 200}});
  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 16,
        fontFamily: FONT_BODY,
        fontWeight: 700,
        fontSize: 26,
        letterSpacing: 4,
        textTransform: 'uppercase',
        color: COLORS.muted,
        opacity: s,
        transform: `translateX(${(1 - s) * -40}px)`,
      }}
    >
      <span style={{width: 56 * s, height: 4, borderRadius: 4, background: color}} />
      <span style={{color}}>{String(index).padStart(2, '0')}</span>
      <span style={{opacity: 0.5}}>/ {String(total).padStart(2, '0')}</span>
      <span>• {label}</span>
    </div>
  );
};

/** Avatar — rasm (stiker uslubida oq chegarali) yoki emoji */
export const Avatar: React.FC<{
  emoji?: string;
  src?: string;
  color: string;
  size?: number;
  style?: React.CSSProperties;
}> = ({emoji, src, color, size = 160, style}) => (
  <div
    style={{
      width: size,
      height: size,
      borderRadius: '50%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: size * 0.58,
      overflow: 'hidden',
      flexShrink: 0,
      background: src
        ? '#FFFFFF'
        : `radial-gradient(circle at 35% 30%, ${color}66, ${color}22 60%, rgba(255,255,255,0.04))`,
      border: src ? `${Math.max(4, size * 0.05)}px solid #FFFFFF` : `4px solid ${color}`,
      boxShadow: `0 0 0 ${Math.max(3, size * 0.03)}px ${color}, 0 20px 50px rgba(0,0,0,0.45), 0 0 50px ${color}55`,
      ...style,
    }}
  >
    {src ? <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover'}} /> : emoji}
  </div>
);

/** Kamera chirog'i (flash) — berilgan kadrlarda oq chaqnash */
export const Flash: React.FC<{at: number[]; strength?: number}> = ({at, strength = 0.85}) => {
  const frame = useCurrentFrame();
  const o = Math.max(0, ...at.map((f) => interpolate(frame - f, [0, 2, 14], [0, strength, 0], clamp)));
  if (o <= 0) return null;
  return <AbsoluteFill style={{background: '#FFFFFF', opacity: o, pointerEvents: 'none'}} />;
};

/** Smartfon ramkasi */
export const Phone: React.FC<{
  width?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
  glow?: string;
}> = ({width = 420, children, style, glow = COLORS.violet}) => {
  const height = width * 2.05;
  return (
    <div
      style={{
        width,
        height,
        borderRadius: width * 0.14,
        padding: width * 0.035,
        background: 'linear-gradient(160deg, #2A3142, #0B0E16)',
        boxShadow: `0 60px 120px rgba(0,0,0,0.6), 0 0 0 2px rgba(255,255,255,0.12), 0 0 140px ${glow}44`,
        position: 'relative',
        ...style,
      }}
    >
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: '100%',
          borderRadius: width * 0.11,
          overflow: 'hidden',
          background: '#05070D',
        }}
      >
        {children}
        <div
          style={{
            position: 'absolute',
            top: width * 0.03,
            left: '50%',
            width: width * 0.3,
            height: width * 0.075,
            marginLeft: -width * 0.15,
            borderRadius: width,
            background: '#000',
          }}
        />
      </div>
    </div>
  );
};

/** Kamera interfeysi (viewfinder) */
export const Viewfinder: React.FC<{label?: string; color?: string; rec?: boolean}> = ({
  label = 'FOTO',
  color = COLORS.amber,
  rec = true,
}) => {
  const frame = useCurrentFrame();
  const corner = (r: number): React.CSSProperties => ({
    position: 'absolute',
    width: 70,
    height: 70,
    borderColor: '#FFFFFF',
    borderStyle: 'solid',
    borderWidth: 0,
    transform: `rotate(${r}deg)`,
  });
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {/* uchdan bir panjara */}
      <AbsoluteFill
        style={{
          backgroundImage:
            'linear-gradient(90deg, transparent 33.1%, rgba(255,255,255,0.35) 33.3%, transparent 33.5%, transparent 66.5%, rgba(255,255,255,0.35) 66.7%, transparent 66.9%), linear-gradient(transparent 33.1%, rgba(255,255,255,0.35) 33.3%, transparent 33.5%, transparent 66.5%, rgba(255,255,255,0.35) 66.7%, transparent 66.9%)',
        }}
      />
      <div style={{...corner(0), left: 40, top: 40, borderLeftWidth: 6, borderTopWidth: 6, borderRadius: '14px 0 0 0'}} />
      <div style={{...corner(0), right: 40, top: 40, borderRightWidth: 6, borderTopWidth: 6, borderRadius: '0 14px 0 0'}} />
      <div style={{...corner(0), left: 40, bottom: 40, borderLeftWidth: 6, borderBottomWidth: 6, borderRadius: '0 0 0 14px'}} />
      <div style={{...corner(0), right: 40, bottom: 40, borderRightWidth: 6, borderBottomWidth: 6, borderRadius: '0 0 14px 0'}} />
      <div
        style={{
          position: 'absolute',
          top: 54,
          left: 0,
          right: 0,
          textAlign: 'center',
          fontFamily: FONT_BODY,
          fontWeight: 700,
          fontSize: 26,
          letterSpacing: 6,
          color,
        }}
      >
        {rec && (
          <span
            style={{
              display: 'inline-block',
              width: 16,
              height: 16,
              borderRadius: 8,
              marginRight: 12,
              background: COLORS.red,
              opacity: Math.floor(frame / 20) % 2 ? 1 : 0.25,
            }}
          />
        )}
        {label}
      </div>
    </AbsoluteFill>
  );
};

/** Termometr: value 0..1 */
export const Thermometer: React.FC<{value: number; height?: number; label?: string}> = ({
  value,
  height = 420,
  label,
}) => {
  const color = interpolateHex(value);
  return (
    <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 18}}>
      <div
        style={{
          position: 'relative',
          width: 64,
          height,
          borderRadius: 40,
          background: 'rgba(255,255,255,0.08)',
          border: '3px solid rgba(255,255,255,0.25)',
        }}
      >
        <div
          style={{
            position: 'absolute',
            left: 12,
            right: 12,
            bottom: 12,
            height: `${Math.max(6, value * 100 - 4)}%`,
            borderRadius: 30,
            background: `linear-gradient(to top, ${color}, ${color}AA)`,
            boxShadow: `0 0 40px ${color}`,
          }}
        />
        <div
          style={{
            position: 'absolute',
            left: '50%',
            bottom: -48,
            width: 110,
            height: 110,
            marginLeft: -55,
            borderRadius: '50%',
            background: color,
            border: '3px solid rgba(255,255,255,0.25)',
            boxShadow: `0 0 60px ${color}`,
          }}
        />
      </div>
      {label && (
        <div
          style={{
            marginTop: 50,
            fontFamily: FONT_DISPLAY,
            fontWeight: 900,
            fontSize: 64,
            color,
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {label}
        </div>
      )}
    </div>
  );
};

/** Issiq (to'q sariq) → sovuq (havorang) */
export const interpolateHex = (v: number) => {
  const a = [56, 189, 248];
  const b = [255, 106, 61];
  const t = Math.min(1, Math.max(0, v));
  const c = a.map((x, i) => Math.round(x + (b[i] - x) * t));
  return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
};

/** Gap pufagi (speech bubble) */
export const SpeechBubble: React.FC<{
  children: React.ReactNode;
  color: string;
  tail?: 'left' | 'right' | 'bottom';
  style?: React.CSSProperties;
}> = ({children, color, tail = 'left', style}) => (
  <div
    style={{
      position: 'relative',
      padding: '40px 56px',
      borderRadius: 44,
      background: `linear-gradient(135deg, ${color}, ${color}CC)`,
      boxShadow: `0 30px 80px rgba(0,0,0,0.45), 0 0 90px ${color}66`,
      ...style,
    }}
  >
    <div
      style={{
        position: 'absolute',
        width: 54,
        height: 54,
        background: color,
        borderRadius: 8,
        transform: 'rotate(45deg)',
        ...(tail === 'left'
          ? {left: -14, top: '50%', marginTop: -27}
          : tail === 'right'
            ? {right: -14, top: '50%', marginTop: -27}
            : {bottom: -18, left: 90}),
      }}
    />
    <div style={{position: 'relative'}}>{children}</div>
  </div>
);
