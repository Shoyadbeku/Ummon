import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fonts } from "../fonts";
import type { MapProps } from "../schema";
import { KenBurns, Kicker, Vignette, progress, useExit, useTheme } from "../components/ui";

const W = 1920;
const H = 1080;

/**
 * Animated route map. Points are placed by longitude/latitude
 * (equirectangular with cos(lat) correction), then joined by a route that
 * draws itself; each city pops in as the line reaches it.
 * Put a real map in public/ and set `image` for a geographic background.
 */
export const MapScene: React.FC<MapProps> = ({ title, subtitle, bounds, points, image }) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exit = useExit(15);

  const { lonMin, lonMax, latMin, latMax } = bounds;
  const k = Math.cos((((latMin + latMax) / 2) * Math.PI) / 180);
  const pad = 140;
  const scale = Math.min((W - pad * 2) / ((lonMax - lonMin) * k), (H - pad * 2) / (latMax - latMin));
  const offX = (W - (lonMax - lonMin) * k * scale) / 2;
  const offY = (H - (latMax - latMin) * scale) / 2;
  const proj = (lon: number, lat: number) => ({
    x: offX + (lon - lonMin) * k * scale,
    y: offY + (latMax - lat) * scale,
  });
  const pts = points.map((p) => ({ ...p, ...proj(p.lon, p.lat) }));

  // Curved route segments (quadratic, bulging sideways)
  const segs = pts.slice(1).map((b, i) => {
    const a = pts[i];
    const mx = (a.x + b.x) / 2;
    const my = (a.y + b.y) / 2;
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const len = Math.hypot(dx, dy) || 1;
    const bend = Math.min(120, len * 0.2);
    const cx = mx - (dy / len) * bend;
    const cy = my + (dx / len) * bend;
    return { d: `M${a.x},${a.y} Q${cx},${cy} ${b.x},${b.y}`, len: len * 1.08 };
  });
  const total = segs.reduce((s, x) => s + x.len, 0) || 1;

  const start = 25;
  const end = durationInFrames - 35;
  const drawn = interpolate(frame, [start, end], [0, total], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Camera gently follows the head of the route
  let acc = 0;
  let headIdx = 0;
  segs.forEach((s, i) => {
    if (drawn >= acc + s.len * 0.0001) headIdx = i;
    acc += s.len;
  });
  const reachedAt = (i: number) => (i === 0 ? 0 : segs.slice(0, i).reduce((s, x) => s + x.len, 0));
  const target = pts[Math.min(headIdx + 1, pts.length - 1)] ?? { x: W / 2, y: H / 2 };
  const zoom = interpolate(frame, [0, 30, end, durationInFrames], [1.0, 1.12, 1.12, 1.0], {
    extrapolateRight: "clamp",
  });
  const camX = interpolate(target.x, [0, W], [80, -80]);
  const camY = interpolate(target.y, [0, H], [50, -50]);

  let consumed = 0;
  return (
    <AbsoluteFill style={{ opacity: exit, background: t.background }}>
      <AbsoluteFill style={{ transform: `scale(${zoom}) translate(${camX}px, ${camY}px)` }}>
        {image ? (
          <KenBurns src={image} filter="sepia(0.6) brightness(0.6) contrast(1.1)" />
        ) : (
          <AbsoluteFill
            style={{
              background: `radial-gradient(ellipse at 50% 50%, #2b2115 0%, ${t.background} 80%)`,
            }}
          />
        )}
        <svg width={W} height={H} style={{ position: "absolute" }}>
          {/* graticule */}
          <g stroke={t.paper} strokeOpacity={0.09} strokeWidth={1}>
            {Array.from({ length: Math.floor(lonMax / 5) - Math.ceil(lonMin / 5) + 1 }, (_, i) => {
              const lon = (Math.ceil(lonMin / 5) + i) * 5;
              const { x } = proj(lon, latMin);
              return <line key={`v${lon}`} x1={x} y1={0} x2={x} y2={H} />;
            })}
            {Array.from({ length: Math.floor(latMax / 5) - Math.ceil(latMin / 5) + 1 }, (_, i) => {
              const lat = (Math.ceil(latMin / 5) + i) * 5;
              const { y } = proj(lonMin, lat);
              return <line key={`h${lat}`} x1={0} y1={y} x2={W} y2={y} />;
            })}
          </g>

          {/* route */}
          {segs.map((s, i) => {
            const segStart = consumed;
            consumed += s.len;
            const local = Math.max(0, Math.min(1, (drawn - segStart) / s.len));
            return (
              <g key={i}>
                <path
                  d={s.d}
                  fill="none"
                  stroke={t.accent}
                  strokeOpacity={0.18}
                  strokeWidth={12}
                  strokeLinecap="round"
                  pathLength={1}
                  style={{ strokeDasharray: 1, strokeDashoffset: 1 - local }}
                />
                <path
                  d={s.d}
                  fill="none"
                  stroke={t.accent}
                  strokeWidth={4}
                  strokeLinecap="round"
                  pathLength={1}
                  style={{ strokeDasharray: 1, strokeDashoffset: 1 - local }}
                />
              </g>
            );
          })}

          {/* cities */}
          {pts.map((p, i) => {
            const at = reachedAt(i);
            const f0 = interpolate(at, [0, total], [start, end]);
            const pop = progress(frame, f0 - 4, 18);
            const pulse = ((frame - f0) % 45) / 45;
            const active = i === Math.min(headIdx + 1, pts.length - 1) && frame < end;
            // Put the label on the other side if an earlier city sits close by
            const crowded = pts.slice(0, i).some((q) => Math.hypot(q.x - p.x, q.y - p.y) < 90);
            const labelLeft = p.x > W * 0.78 ? !crowded : crowded;
            const labelDy = crowded ? 34 : 0;
            return (
              <g key={p.name} opacity={pop} transform={`translate(${p.x},${p.y})`}>
                {active || i === pts.length - 1 ? (
                  <circle r={10 + pulse * 40} fill="none" stroke={t.accent} strokeOpacity={1 - pulse} strokeWidth={2} />
                ) : null}
                <circle r={11 * pop} fill={t.background} stroke={t.accent} strokeWidth={3} />
                <circle r={4.5 * pop} fill={t.accent} />
                <g transform={`translate(${labelLeft ? -22 : 22}, ${labelDy})`} textAnchor={labelLeft ? "end" : "start"}>
                  <text
                    y={-4}
                    fill={t.text}
                    fontFamily={fonts.serif}
                    fontWeight={700}
                    fontSize={38}
                    style={{ paintOrder: "stroke" }}
                    stroke={t.background}
                    strokeWidth={6}
                  >
                    {p.name}
                  </text>
                  <text
                    y={28}
                    fill={t.accent}
                    fontFamily={fonts.sans}
                    fontWeight={600}
                    fontSize={22}
                    letterSpacing={3}
                    style={{ paintOrder: "stroke" }}
                    stroke={t.background}
                    strokeWidth={5}
                  >
                    {p.label}
                  </text>
                </g>
              </g>
            );
          })}
        </svg>
      </AbsoluteFill>

      {/* compass */}
      <svg
        width={120}
        height={120}
        viewBox="-60 -60 120 120"
        style={{
          position: "absolute",
          right: 80,
          bottom: 70,
          opacity: 0.8 * progress(frame, 10, 25),
          transform: `rotate(${interpolate(progress(frame, 10, 40), [0, 1], [-90, 0])}deg)`,
        }}
      >
        <circle r={50} fill="none" stroke={t.accent} strokeOpacity={0.6} />
        <path d="M0,-48 L8,0 L0,48 L-8,0 Z" fill={t.accent} />
        <path d="M-48,0 L0,6 L48,0 L0,-6 Z" fill={t.paper} fillOpacity={0.5} />
        <text y={-54} textAnchor="middle" fill={t.text} fontFamily={fonts.display} fontSize={16}>
          N
        </text>
      </svg>

      <div style={{ position: "absolute", top: 70, left: 90, display: "flex", flexDirection: "column", gap: 10 }}>
        <Kicker delay={0}>{subtitle}</Kicker>
        <div
          style={{
            fontFamily: fonts.serif,
            fontWeight: 700,
            fontSize: 72,
            color: t.text,
            opacity: progress(frame, 5, 25),
            textShadow: "0 4px 20px rgba(0,0,0,0.8)",
          }}
        >
          {title}
        </div>
      </div>
      <Vignette strength={0.8} />
    </AbsoluteFill>
  );
};
