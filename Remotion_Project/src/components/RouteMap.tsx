import React from "react";
import { interpolate, useCurrentFrame, Easing } from "remotion";
import { ACCENT, FONT, ICE } from "../theme";

/* Schematic (not survey-accurate) map of the route, drawn from real coordinates.
   Equirectangular projection over lon -74..-54, lat -29..-38 into a 1000x560 panel. */
const W = 1000, H = 560;
const DEFAULT_B = { lon0: -74, lon1: -54, lat0: -29, lat1: -38 };
const TREK_B = { lon0: -71.9, lon1: -69.3, lat0: -33.95, lat1: -35.4 };
let B = DEFAULT_B;
const px = (lon: number) => ((lon - B.lon0) / (B.lon1 - B.lon0)) * W;
const py = (lat: number) => ((B.lat0 - lat) / (B.lat0 - B.lat1)) * H;
const P = (lon: number, lat: number) => [px(lon), py(lat)] as const;

const PLACES: Record<string, { lon: number; lat: number; name: string; dx?: number; dy?: number }> = {
  mvd: { lon: -56.16, lat: -34.9, name: "Montevideo", dx: -60, dy: 40 },
  mdz: { lon: -68.84, lat: -32.89, name: "Mendosa", dx: 14, dy: -12 },
  scl: { lon: -70.67, lat: -33.45, name: "Santyago", dx: -150, dy: -10 },
  cur: { lon: -71.24, lat: -34.98, name: "Kuriko", dx: -110, dy: 30 },
  mlg: { lon: -69.58, lat: -35.47, name: "Malargue", dx: 14, dy: 22 },
  crash: { lon: -70.29, lat: -34.77, name: "Halokat joyi", dx: 18, dy: -14 },
  mait: { lon: -70.6, lat: -34.85, name: "Los Maytenes", dx: -160, dy: 44 },
};

// rough coast / Andes for orientation only
const pacific = () => [P(-74, -29), P(-71.35, -29), P(-71.55, -31), P(-71.65, -33), P(-72.0, -35), P(-72.6, -37), P(-73.6, -38), P(-74, -38)];
const plata = () => [P(-58.4, -34.0), P(-56.2, -34.95), P(-54.9, -34.95), P(-54, -34.6), P(-54, -38), P(-57.5, -38), P(-58.3, -36.3), P(-57.2, -35.3), P(-58.4, -34.0)];
const andes = () => [P(-69.9, -29), P(-70.0, -31), P(-70.0, -33), P(-70.2, -34.5), P(-70.5, -36), P(-71.0, -38)];
const poly = (pts: readonly (readonly [number, number])[]) => pts.map((p) => p.join(",")).join(" ");

const Dot: React.FC<{ id: string; o: number; color?: string; pulse?: number }> = ({ id, o, color = "#fff", pulse = 0 }) => {
  const p = PLACES[id];
  const [x, y] = P(p.lon, p.lat);
  return (
    <g opacity={o}>
      {pulse > 0 ? <circle cx={x} cy={y} r={8 + pulse * 26} fill="none" stroke={color} strokeWidth={2} opacity={1 - pulse} /> : null}
      <circle cx={x} cy={y} r={8} fill={color} stroke="#000" strokeWidth={2} />
      <text x={x + (p.dx ?? 12)} y={y + (p.dy ?? -10)} fill="#fff" fontSize={24} fontWeight={700} fontFamily={FONT} style={{ paintOrder: "stroke" }} stroke="rgba(0,0,0,0.85)" strokeWidth={4}>
        {p.name}
      </text>
    </g>
  );
};

const Path: React.FC<{ pts: [number, number][]; p: number; color: string; dash?: boolean; width?: number }> = ({ pts, p, color, dash, width = 5 }) => {
  const d = pts.map((q, i) => `${i ? "L" : "M"}${px(q[0])},${py(q[1])}`).join(" ");
  const len = 3000;
  return (
    <path d={d} fill="none" stroke={color} strokeWidth={width} strokeLinecap="round" strokeLinejoin="round"
      strokeDasharray={dash ? "14 12" : `${len}`} strokeDashoffset={dash ? 0 : len * (1 - p)} opacity={dash ? p : 1} />
  );
};

export const RouteMap: React.FC<{ stage: string; dur: number }> = ({ stage, dur }) => {
  const frame = useCurrentFrame();
  B = stage === "trek" ? TREK_B : DEFAULT_B;
  const o = interpolate(frame, [0, 12, dur - 12, dur], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const p = (a: number, b: number) =>
    interpolate(frame, [a * dur, b * dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const pulse = (frame % 40) / 40;
  const title: Record<string, string> = {
    route: "REJALASHTIRILGAN YO'NALISH",
    error: "NAVIGATSIYA XATOSI",
    search: "QIDIRUV: TAXMINIY JOY NOTO'G'RI",
    trek: "PARRADO VA KANESSA YO'LI • 12–20 DEKABR",
  };
  return (
    <div style={{ position: "absolute", right: 80, top: 150, opacity: o, width: W, height: H + 60, fontFamily: FONT }}>
      <div style={{ color: ACCENT, fontSize: 26, fontWeight: 800, letterSpacing: 4, marginBottom: 10, textShadow: "0 2px 6px #000" }}>{title[stage]}</div>
      <svg width={W} height={H} style={{ background: "rgba(14,22,30,0.88)", borderRadius: 8, boxShadow: "0 20px 60px rgba(0,0,0,0.6)" }}>
        <polygon points={poly(pacific())} fill="rgba(70,110,150,0.35)" />
        <polygon points={poly(plata())} fill="rgba(70,110,150,0.35)" />
        <polyline points={poly(andes())} fill="none" stroke="rgba(220,230,240,0.22)" strokeWidth={stage === "trek" ? 260 : 46} strokeLinecap="round" />
        <text x={px(-73.3)} y={py(-36.4)} fill="rgba(255,255,255,0.35)" fontSize={22} fontWeight={700} letterSpacing={6}>CHILI</text>
        <text x={px(-66.5)} y={py(-34.3)} fill="rgba(255,255,255,0.35)" fontSize={22} fontWeight={700} letterSpacing={6}>ARGENTINA</text>
        <text x={px(-57.6)} y={py(-32.6)} fill="rgba(255,255,255,0.35)" fontSize={22} fontWeight={700} letterSpacing={6}>URUG'VAY</text>
        <text x={px(-70.6)} y={py(-30.2)} fill="rgba(255,255,255,0.4)" fontSize={18} letterSpacing={3}>AND TOG'LARI</text>

        {stage === "route" ? (
          <>
            <Path pts={[[-56.16, -34.9], [-62, -33.6], [-68.84, -32.89]]} p={p(0.1, 0.55)} color={ACCENT} />
            <Path pts={[[-68.84, -32.89], [-70.67, -33.45]]} p={p(0.6, 0.85)} color={ICE} dash />
            <Dot id="mvd" o={1} />
            <Dot id="mdz" o={p(0.45, 0.55)} />
            <Dot id="scl" o={p(0.7, 0.8)} />
          </>
        ) : null}

        {stage === "error" ? (
          <>
            <Path pts={[[-68.84, -32.89], [-69.3, -34.2], [-69.58, -35.2], [-70.0, -35.1], [-70.29, -34.77]]} p={p(0.05, 0.6)} color={ACCENT} />
            <Dot id="mdz" o={1} />
            <Dot id="scl" o={1} />
            <Dot id="cur" o={p(0.4, 0.5)} color={ICE} pulse={frame > 0.5 * dur ? pulse : 0} />
            <Dot id="crash" o={p(0.55, 0.62)} color="#e0533d" pulse={frame > 0.62 * dur ? pulse : 0} />
            <g opacity={p(0.5, 0.6)}>
              <text x={px(-73.8)} y={py(-36.0)} fill={ICE} fontSize={21} fontFamily={FONT}>Ekipaj fikricha: Kuriko ustida,</text>
              <text x={px(-73.8)} y={py(-36.0) + 26} fill={ICE} fontSize={21} fontFamily={FONT}>tog' tizmasidan o'tib bo'lingan</text>
            </g>
            <g opacity={p(0.62, 0.72)}>
              <text x={px(-69.3)} y={py(-36.6)} fill="#ff8a75" fontSize={21} fontFamily={FONT}>Aslida: hali tog'lar ichida</text>
            </g>
          </>
        ) : null}

        {stage === "search" ? (
          <>
            <circle cx={px(-71.0)} cy={py(-34.9)} r={40 + 60 * p(0, 0.6)} fill="rgba(207,227,242,0.10)" stroke={ICE} strokeDasharray="8 8" strokeWidth={2} />
            <text x={px(-73.8)} y={py(-33.6)} fill={ICE} fontSize={21} fontFamily={FONT} opacity={p(0.2, 0.3)}>Qidiruv hududi (taxminiy joy)</text>
            <Dot id="cur" o={1} color={ICE} />
            <Dot id="crash" o={p(0.4, 0.5)} color="#e0533d" pulse={pulse} />
          </>
        ) : null}

        {stage === "trek" ? (
          <>
            <Path pts={[[-70.29, -34.77], [-70.36, -34.74], [-70.45, -34.79], [-70.55, -34.83], [-70.6, -34.85]]} p={p(0.1, 0.85)} color={ACCENT} width={6} />
            <Dot id="crash" o={1} color="#e0533d" />
            <Dot id="mait" o={p(0.8, 0.9)} color={ICE} />
            <Dot id="scl" o={0.6} />
          </>
        ) : null}
      </svg>
      <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 16, marginTop: 6 }}>Sxematik xarita • masshtab aniq emas</div>
    </div>
  );
};
