import React, {useMemo} from 'react';
import {random} from 'remotion';
import {Steam} from './Steam';

/**
 * Vektorli palov (AI rasm bo'lmaganda ishlatiladigan zaxira illyustratsiya).
 * An'anaviy "paxta" naqshli lagan, oltin guruch, sabzi, no'xat, go'sht va sarimsoq.
 * `heat` (0..1) — bug' kuchi va ranglarning iliqligi.
 */
export const PlovPlate: React.FC<{
  size?: number;
  heat?: number;
  tilt?: number;
  spin?: number;
  steam?: boolean;
  style?: React.CSSProperties;
}> = ({size = 640, heat = 1, tilt = 58, spin = 0, steam = true, style}) => {
  const rice = useMemo(() => {
    const palette = ['#FCE7B0', '#F6D58E', '#EDBB63', '#FFF3D1', '#E9A94D'];
    return new Array(520).fill(0).map((_, i) => {
      const r = Math.sqrt(random(`rr${i}`)) * 192;
      const a = random(`ra${i}`) * Math.PI * 2;
      return {
        x: Math.cos(a) * r,
        y: Math.sin(a) * r,
        rot: random(`rt${i}`) * 180,
        c: palette[Math.floor(random(`rc${i}`) * palette.length)],
      };
    });
  }, []);

  const carrots = useMemo(
    () =>
      new Array(80).fill(0).map((_, i) => {
        const r = Math.sqrt(random(`cr${i}`)) * 185;
        const a = random(`ca${i}`) * Math.PI * 2;
        return {
          x: Math.cos(a) * r,
          y: Math.sin(a) * r,
          rot: random(`ct${i}`) * 180,
          c: random(`cc${i}`) > 0.5 ? '#F07F2B' : '#E5651B',
          w: 18 + random(`cw${i}`) * 16,
        };
      }),
    [],
  );

  const chickpeas = useMemo(
    () =>
      new Array(18).fill(0).map((_, i) => {
        const r = 40 + random(`pr${i}`) * 140;
        const a = random(`pa${i}`) * Math.PI * 2;
        return {x: Math.cos(a) * r, y: Math.sin(a) * r};
      }),
    [],
  );

  const meat = [
    {x: -58, y: -28, r: 0},
    {x: 52, y: -40, r: 40},
    {x: -40, y: 52, r: 80},
    {x: 60, y: 48, r: 130},
    {x: 0, y: -78, r: 200},
    {x: -88, y: 10, r: 260},
    {x: 90, y: 4, r: 310},
  ];

  const warm = 0.55 + heat * 0.45;

  return (
    <div style={{position: 'relative', width: size, height: size, ...style}}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform: `perspective(1400px) rotateX(${tilt}deg) rotateZ(${spin}deg)`,
          filter: `saturate(${warm}) brightness(${0.85 + heat * 0.15})`,
        }}
      >
        <svg viewBox="-310 -310 620 620" width={size} height={size} style={{overflow: 'visible'}}>
          <defs>
            <radialGradient id="plate" cx="40%" cy="35%" r="75%">
              <stop offset="0%" stopColor="#FFFFFF" />
              <stop offset="70%" stopColor="#EEF2F7" />
              <stop offset="100%" stopColor="#C9D3E0" />
            </radialGradient>
            <radialGradient id="riceBase" cx="45%" cy="40%" r="65%">
              <stop offset="0%" stopColor="#F9D98F" />
              <stop offset="70%" stopColor="#E3A548" />
              <stop offset="100%" stopColor="#B87628" />
            </radialGradient>
            <radialGradient id="meat" cx="35%" cy="30%" r="80%">
              <stop offset="0%" stopColor="#B2683A" />
              <stop offset="60%" stopColor="#7B3B19" />
              <stop offset="100%" stopColor="#4A220D" />
            </radialGradient>
            <radialGradient id="shadow" cx="50%" cy="50%" r="50%">
              <stop offset="60%" stopColor="rgba(0,0,0,0.55)" />
              <stop offset="100%" stopColor="rgba(0,0,0,0)" />
            </radialGradient>
          </defs>
          <circle cx={14} cy={22} r={312} fill="url(#shadow)" />
          <circle r={292} fill="url(#plate)" />
          <circle r={292} fill="none" stroke="#1E40AF" strokeWidth={6} />
          {/* "Paxta" naqshi */}
          {new Array(16).fill(0).map((_, i) => {
            const a = (i / 16) * Math.PI * 2;
            const x = Math.cos(a) * 258;
            const y = Math.sin(a) * 258;
            return (
              <g key={i} transform={`translate(${x} ${y}) rotate(${(a * 180) / Math.PI})`}>
                <circle r={9} fill="#1D4ED8" />
                {[0, 90, 180, 270].map((d) => (
                  <ellipse key={d} rx={6} ry={13} transform={`rotate(${d + 45}) translate(0 -14)`} fill="#2563EB" />
                ))}
                <circle r={4} fill="#FFFFFF" />
              </g>
            );
          })}
          <circle r={232} fill="none" stroke="#1D4ED8" strokeWidth={3} strokeDasharray="2 10" strokeLinecap="round" />
          {/* Guruch tepaligi */}
          <circle r={205} fill="url(#riceBase)" />
          {rice.map((g, i) => (
            <ellipse key={i} cx={g.x} cy={g.y} rx={6.5} ry={2.4} fill={g.c} transform={`rotate(${g.rot} ${g.x} ${g.y})`} />
          ))}
          {carrots.map((c, i) => (
            <rect
              key={i}
              x={c.x - c.w / 2}
              y={c.y - 2.6}
              width={c.w}
              height={5.2}
              rx={2.6}
              fill={c.c}
              transform={`rotate(${c.rot} ${c.x} ${c.y})`}
            />
          ))}
          {chickpeas.map((p, i) => (
            <g key={i}>
              <circle cx={p.x} cy={p.y} r={8} fill="#E8C98B" stroke="#C99B4E" strokeWidth={1.5} />
              <circle cx={p.x - 2} cy={p.y - 3} r={2.5} fill="#FFF1CF" />
            </g>
          ))}
          {meat.map((m, i) => (
            <g key={i} transform={`translate(${m.x} ${m.y}) rotate(${m.r})`}>
              <path
                d="M-34 -14 C-30 -30 10 -32 30 -20 C44 -10 40 14 24 24 C4 34 -30 30 -38 12 C-42 2 -38 -8 -34 -14Z"
                fill="url(#meat)"
              />
              <path d="M-20 -14 C-6 -20 12 -18 22 -10" stroke="#D49260" strokeWidth={4} fill="none" strokeLinecap="round" opacity={0.7} />
            </g>
          ))}
          {/* Sarimsoq boshi */}
          <g>
            <circle r={34} fill="#F2E3C6" stroke="#CDAE7C" strokeWidth={3} />
            {[0, 60, 120, 180, 240, 300].map((d) => (
              <path key={d} d="M0 0 L0 -32" stroke="#D3B98A" strokeWidth={2.5} transform={`rotate(${d})`} />
            ))}
            <circle r={9} fill="#B98C4E" />
          </g>
          {/* Sovuq holatda moy qotishi */}
          <circle r={205} fill="#9FB7D4" opacity={(1 - heat) * 0.28} />
        </svg>
      </div>
      {steam && heat > 0.02 && (
        <Steam
          heat={heat}
          width={size * 0.8}
          height={size * 0.95}
          style={{position: 'absolute', left: size * 0.1, bottom: size * 0.5}}
        />
      )}
    </div>
  );
};
