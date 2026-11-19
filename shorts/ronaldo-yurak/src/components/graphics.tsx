import React, { useMemo } from 'react';
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { BODY, C, HEAD, beatPulse, useAbsFrame } from './fx';

/* ---------------------------------------------------------------- ECG */
const ecgShape = (dt: number) => {
  const g = (mu: number, sig: number, a: number) => a * Math.exp(-((dt - mu) ** 2) / (2 * sig * sig));
  return g(-0.16, 0.025, 0.12) + g(-0.025, 0.008, -0.12) + g(0, 0.011, 1) + g(0.03, 0.01, -0.32) + g(0.22, 0.04, 0.24);
};

/**
 * Scrolling ECG trace locked to absolute beat times (seconds), so every spike
 * lands exactly on an audible heartbeat in the score.
 */
export const ECG: React.FC<{
  beats: number[];
  color?: string;
  y?: number;
  amp?: number;
  pxPerSec?: number;
  width?: number;
  opacity?: number;
  thickness?: number;
}> = ({ beats, color = C.red, y = 960, amp = 220, pxPerSec = 520, width = 1080, opacity = 1, thickness = 7 }) => {
  const frame = useAbsFrame();
  const { fps } = useVideoConfig();
  const now = frame / fps;
  const head = width * 0.78;
  const pts: string[] = [];
  for (let x = 0; x <= head; x += 4) {
    const t = now - (head - x) / pxPerSec;
    let v = 0;
    for (const b of beats) {
      const d = t - b;
      if (d > -0.3 && d < 0.4) v += ecgShape(d);
    }
    pts.push(`${x},${(y - v * amp).toFixed(1)}`);
  }
  const last = pts[pts.length - 1].split(',');
  return (
    <AbsoluteFill style={{ opacity, pointerEvents: 'none' }}>
      <svg width={width} height={1920}>
        <defs>
          <linearGradient id={`fade-${color}`} x1="0" x2="1">
            <stop offset="0" stopColor={color} stopOpacity="0" />
            <stop offset="0.5" stopColor={color} stopOpacity="0.7" />
            <stop offset="1" stopColor={color} stopOpacity="1" />
          </linearGradient>
          <filter id="ecgGlow" x="-20%" y="-50%" width="140%" height="200%">
            <feGaussianBlur stdDeviation="8" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <polyline
          points={pts.join(' ')}
          fill="none"
          stroke={`url(#fade-${color})`}
          strokeWidth={thickness}
          strokeLinejoin="round"
          filter="url(#ecgGlow)"
        />
        <circle cx={Number(last[0])} cy={Number(last[1])} r={12} fill="#fff" filter="url(#ecgGlow)" />
      </svg>
    </AbsoluteFill>
  );
};

/* ---------------------------------------------------------------- Heart */
const HEART_PATH =
  'M0,-30 C-10,-60 -60,-62 -62,-20 C-64,12 -30,38 0,64 C30,38 64,12 62,-20 C60,-62 10,-60 0,-30 Z';

export const Heart: React.FC<{ beats: number[]; size?: number; x?: number; y?: number; color?: string; at?: number }> = ({
  beats,
  size = 6,
  x = 540,
  y = 820,
  color = C.red,
  at = 0,
}) => {
  const frame = useCurrentFrame();
  const abs = useAbsFrame();
  const { fps } = useVideoConfig();
  const local = frame - at;
  if (local < 0) return null;
  const enter = spring({ frame: local, fps, config: { damping: 12, stiffness: 120 } });
  const pulse = beatPulse(abs, fps, beats, 7);
  const sc = size * enter * (1 + pulse * 0.12);
  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      <svg width={1080} height={1920}>
        <defs>
          <radialGradient id="hg" cx="40%" cy="30%" r="80%">
            <stop offset="0" stopColor="#ff7480" />
            <stop offset="0.5" stopColor={color} />
            <stop offset="1" stopColor={C.redDeep} />
          </radialGradient>
          <filter id="hglow" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation={18 + pulse * 25} result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {[0, 1, 2].map((i) => {
          const ring = (pulse > 0 ? 1 - pulse : 0) + i * 0.33;
          return (
            <path
              key={i}
              d={HEART_PATH}
              transform={`translate(${x},${y}) scale(${sc * (1 + (ring % 1) * 0.9)})`}
              fill="none"
              stroke={color}
              strokeWidth={1.2 / sc}
              opacity={(1 - (ring % 1)) * 0.5 * enter}
            />
          );
        })}
        <path d={HEART_PATH} transform={`translate(${x},${y}) scale(${sc})`} fill="url(#hg)" filter="url(#hglow)" />
        <path
          d="M-40,-28 C-44,-46 -24,-52 -14,-40"
          transform={`translate(${x},${y}) scale(${sc})`}
          fill="none"
          stroke="rgba(255,255,255,0.55)"
          strokeWidth={4 / size}
          strokeLinecap="round"
        />
      </svg>
    </AbsoluteFill>
  );
};

/* ---------------------------------------------------------------- BPM monitor */
export const BPMPanel: React.FC<{
  beats: number[];
  startBpm: number;
  mode: 'rising' | 'falling';
  at: number;
  top?: number;
  alertAt?: number;
}> = ({ beats, startBpm, mode, at, top = 420, alertAt }) => {
  const frame = useCurrentFrame();
  const abs = useAbsFrame();
  const { fps } = useVideoConfig();
  const local = frame - at;
  if (local < 0) return null;
  const t = abs / fps;
  let bpm = startBpm;
  if (mode === 'rising') {
    const past = beats.filter((b) => b <= t);
    if (past.length >= 2) bpm = 60 / (past[past.length - 1] - past[past.length - 2]);
    // ease between beats for a "climbing" read-out
    const next = beats.find((b) => b > t);
    if (next && past.length >= 1) {
      const target = 60 / (next - past[past.length - 1]);
      const k = (t - past[past.length - 1]) / (next - past[past.length - 1]);
      bpm = bpm + (target - bpm) * k;
    }
  } else {
    bpm = interpolate(local, [0, 40], [startBpm, 72], { extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
  }
  const enter = spring({ frame: local, fps, config: { damping: 15, stiffness: 150 } });
  const pulse = beatPulse(abs, fps, beats, 9);
  const danger = mode === 'rising' && bpm > 120;
  const col = mode === 'falling' && local > 30 ? C.green : danger ? C.red : C.green;
  const alertOn = alertAt !== undefined && frame >= alertAt && Math.floor((frame - alertAt) / 4) % 2 === 0;
  return (
    <div
      style={{
        position: 'absolute',
        top,
        left: 90,
        right: 90,
        height: 430,
        borderRadius: 28,
        background: 'rgba(5,10,12,0.72)',
        border: `3px solid ${alertOn ? C.red : col}66`,
        boxShadow: `0 0 ${30 + pulse * 60}px ${col}55, inset 0 0 60px ${col}22`,
        backdropFilter: 'blur(14px)',
        transform: `scale(${interpolate(enter, [0, 1], [0.85, 1]) * (1 + pulse * 0.015)})`,
        opacity: enter,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div style={{ fontFamily: BODY, fontWeight: 800, letterSpacing: 8, fontSize: 34, color: `${col}cc` }}>
        ♥ YURAK URISHI
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 18 }}>
        <div
          style={{
            fontFamily: HEAD,
            fontSize: 250,
            color: col,
            lineHeight: 1,
            textShadow: `0 0 40px ${col}`,
            fontVariantNumeric: 'tabular-nums',
            transform: `scale(${1 + pulse * 0.06})`,
          }}
        >
          {Math.round(bpm)}
        </div>
        <div style={{ fontFamily: HEAD, fontSize: 80, color: `${col}aa` }}>BPM</div>
      </div>
    </div>
  );
};

/* ---------------------------------------------------------------- Counter */
export const Counter: React.FC<{
  to: number;
  at: number;
  dur: number;
  size?: number;
  color?: string;
  suffix?: string;
  sep?: string;
}> = ({ to, at, dur, size = 200, color = C.white, suffix = '', sep = ' ' }) => {
  const frame = useCurrentFrame();
  const local = frame - at;
  if (local < 0) return null;
  const p = interpolate(local, [0, dur], [0, 1], { extrapolateRight: 'clamp', easing: Easing.out(Easing.exp) });
  const v = Math.round(to * p);
  const str = v.toString().replace(/\B(?=(\d{3})+(?!\d))/g, sep);
  const blur = interpolate(p, [0, 0.8, 1], [6, 2, 0]);
  return (
    <div
      style={{
        fontFamily: HEAD,
        fontSize: size,
        color,
        lineHeight: 1,
        fontVariantNumeric: 'tabular-nums',
        filter: `blur(${blur}px)`,
        textShadow: '0 10px 50px rgba(0,0,0,0.7)',
      }}
    >
      {str}
      {suffix}
    </div>
  );
};

/* ---------------------------------------------------------------- Stat chips */
export const StatChips: React.FC<{ items: { big: string; small: string }[]; at: number; top?: number }> = ({
  items,
  at,
  top = 1060,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div style={{ position: 'absolute', top, left: 70, right: 70, display: 'flex', flexDirection: 'column', gap: 22 }}>
      {items.map((it, i) => {
        const s = spring({ frame: frame - at - i * 5, fps, config: { damping: 14, stiffness: 170 } });
        if (frame - at - i * 5 < 0) return null;
        return (
          <div
            key={i}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 26,
              background: 'linear-gradient(90deg, rgba(20,14,2,0.85), rgba(20,14,2,0.35))',
              borderLeft: `8px solid ${C.gold}`,
              padding: '14px 28px',
              transform: `translateX(${interpolate(s, [0, 1], [i % 2 ? 300 : -300, 0])}px)`,
              opacity: s,
              filter: `blur(${(1 - s) * 10}px)`,
            }}
          >
            <div style={{ fontFamily: HEAD, fontSize: 96, color: C.gold, minWidth: 150, textShadow: `0 0 30px ${C.gold}88` }}>
              {it.big}
            </div>
            <div style={{ fontFamily: BODY, fontWeight: 800, fontSize: 42, color: '#fff', letterSpacing: 2 }}>{it.small}</div>
          </div>
        );
      })}
    </div>
  );
};

/* ---------------------------------------------------------------- Year rewind */
export const YearRewind: React.FC<{ from: number; to: number; at: number; dur: number; top?: number }> = ({
  from,
  to,
  at,
  dur,
  top = 330,
}) => {
  const frame = useCurrentFrame();
  const local = frame - at;
  if (local < 0) return null;
  const p = interpolate(local, [0, dur], [0, 1], { extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) });
  const year = Math.round(from + (to - from) * p);
  const done = p >= 1;
  return (
    <div style={{ position: 'absolute', top, left: 0, right: 0, textAlign: 'center' }}>
      <div style={{ fontFamily: BODY, fontWeight: 800, fontSize: 36, letterSpacing: 10, color: '#ffffffaa' }}>
        {done ? '◀◀ 15 YOSH' : '◀◀ REWIND'}
      </div>
      <div
        style={{
          fontFamily: HEAD,
          fontSize: 200,
          color: done ? C.red : '#fff',
          lineHeight: 1,
          textShadow: done ? `0 0 40px ${C.red}` : '0 0 30px rgba(255,255,255,0.4)',
          filter: `blur(${done ? 0 : 3}px)`,
          transform: `skewX(${done ? 0 : -6}deg)`,
        }}
      >
        {year}
      </div>
    </div>
  );
};

/* ---------------------------------------------------------------- VHS lines */
export const VHS: React.FC<{ opacity?: number }> = ({ opacity = 0.35 }) => {
  const frame = useCurrentFrame();
  const y = (frame * 37) % 1920;
  return (
    <AbsoluteFill style={{ pointerEvents: 'none', opacity }}>
      <AbsoluteFill
        style={{
          background: 'repeating-linear-gradient(0deg, rgba(0,0,0,0.35) 0px, rgba(0,0,0,0.35) 2px, transparent 2px, transparent 5px)',
        }}
      />
      <div style={{ position: 'absolute', top: y, left: 0, right: 0, height: 120, background: 'rgba(255,255,255,0.12)', filter: 'blur(8px)' }} />
    </AbsoluteFill>
  );
};

export const useMemoOnce = useMemo;
