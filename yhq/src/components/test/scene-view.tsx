// Savol vaziyatlarini (chorraha, transport vositalari, belgilar) sxematik SVG ko'rinishida chizadi.
import { SignSvg } from "@/components/sign-icon";

type Dir = "N" | "S" | "E" | "W";
export type SceneData = {
  layout: "cross" | "T" | "round";
  main?: "NS" | "EW";
  tram?: "NS" | "EW";
  signs?: Partial<Record<Dir, string>>;
  lights?: Partial<Record<Dir, string>>;
  vehicles: { id: string; from: Dir; to: Dir; kind?: string; color?: string }[];
  pedestrians?: Dir[];
  caption?: string;
};

const START: Record<Dir, [number, number, number]> = { S: [175, 262, 0], N: [125, 38, 180], E: [262, 125, 270], W: [38, 175, 90] };
const ENTRY: Record<Dir, [number, number]> = { S: [175, 205], N: [125, 95], E: [205, 125], W: [95, 175] };
const EXIT_EDGE: Record<Dir, [number, number]> = { N: [175, 100], S: [125, 200], E: [200, 175], W: [100, 125] };
const EXIT_END: Record<Dir, [number, number]> = { N: [175, 12], S: [125, 288], E: [288, 175], W: [12, 125] };
const SIGN_POS: Record<Dir, [number, number]> = { S: [208, 214], N: [62, 58], E: [214, 62], W: [58, 208] };
const ANGLE: Record<Dir, number> = { E: 0, S: 90, W: 180, N: 270 };
const COLORS = ["#2563eb", "#e11d48", "#16a34a", "#9333ea", "#ea580c"];

function pathFor(from: Dir, to: Dir, round: boolean) {
  const [sx, sy] = START[from];
  const [ex, ey] = EXIT_END[to];
  if (round) {
    const R = 52;
    let a0 = ANGLE[from];
    let a1 = ANGLE[to];
    // o'ng tomonlama harakat: orolcha chap tomonda qoladi (ekranda burchak kamayadi)
    if (a1 >= a0) a1 -= 360;
    const pts: string[] = [];
    for (let a = a0; a >= a1; a -= 15) {
      const r = (a * Math.PI) / 180;
      pts.push(`${150 + R * Math.cos(r)},${150 + R * Math.sin(r)}`);
    }
    const [enx, eny] = ENTRY[from];
    const [xx, xy] = EXIT_EDGE[to];
    return `M${sx},${sy} L${enx},${eny} L${pts.join(" L")} L${xx},${xy} L${ex},${ey}`;
  }
  const [enx, eny] = ENTRY[from];
  const [xx, xy] = EXIT_EDGE[to];
  const vertical = from === "N" || from === "S";
  const straight = (from === "S" && to === "N") || (from === "N" && to === "S") || (from === "E" && to === "W") || (from === "W" && to === "E");
  if (straight) return `M${sx},${sy} L${ex},${ey}`;
  const cx = vertical ? enx : xx;
  const cy = vertical ? xy : eny;
  return `M${sx},${sy} L${enx},${eny} Q${cx},${cy} ${xx},${xy} L${ex},${ey}`;
}

function Vehicle({ v, i }: { v: SceneData["vehicles"][number]; i: number }) {
  const [x, y, rot] = START[v.from];
  const tram = v.kind === "tram";
  const color = v.color ?? (v.kind === "ambulance" ? "#ffffff" : tram ? "#f59e0b" : COLORS[i % COLORS.length]);
  const h = tram ? 58 : 38;
  return (
    <g transform={`translate(${x} ${y}) rotate(${rot})`}>
      <rect x={-12} y={-h / 2} width={24} height={h} rx={tram ? 4 : 6} fill={color} stroke="#0f172a" strokeWidth="1.5" />
      <rect x={-9} y={-h / 2 + 5} width={18} height={8} rx="2" fill="#bfdbfe" opacity=".9" />
      {v.kind === "ambulance" && (
        <>
          <rect x={-3} y={-2} width={6} height={14} fill="#dc2626" /><rect x={-7} y={2} width={14} height={6} fill="#dc2626" />
          <rect x={-9} y={-h / 2 + 14} width={8} height={4} fill="#2563eb" /><rect x={1} y={-h / 2 + 14} width={8} height={4} fill="#dc2626" />
        </>
      )}
      <g transform={`rotate(${-rot})`}>
        <circle r="10" cx="0" cy={tram ? 0 : 6} fill="#0f172a" opacity=".85" />
        <text x="0" y={tram ? 0 : 6} dy="0.35em" textAnchor="middle" fontSize="12" fontWeight="800" fill="#fff" fontFamily="Arial">{v.id}</text>
      </g>
    </g>
  );
}

function Light({ state, x, y }: { state: string; x: number; y: number }) {
  const on = (c: string) => state === c || (c === "green" && state === "green-left");
  return (
    <g transform={`translate(${x} ${y})`}>
      <rect width="14" height="36" rx="3" fill="#111827" />
      <circle cx="7" cy="7" r="4.2" fill={on("red") ? "#ef4444" : "#3f3f46"} />
      <circle cx="7" cy="18" r="4.2" fill={on("yellow") || state === "yellow-flash" ? "#facc15" : "#3f3f46"} />
      <circle cx="7" cy="29" r="4.2" fill={on("green") ? "#22c55e" : "#3f3f46"} />
    </g>
  );
}

export function SceneView({ scene, className }: { scene: SceneData; className?: string }) {
  const round = scene.layout === "round";
  const noNorth = scene.layout === "T";
  return (
    <figure className={className}>
      <svg viewBox="0 0 300 300" className="mx-auto w-full max-w-[340px] rounded-xl border bg-[#7fb069] dark:bg-[#35522b]" role="img" aria-label={scene.caption ?? "Yo'l harakati vaziyati sxemasi"}>
        <defs>
          <marker id="arrowhead" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill="#0f172a" />
          </marker>
        </defs>
        {/* Yo'llar */}
        <rect x="0" y="100" width="300" height="100" fill="#4b5563" />
        <rect x="100" y={noNorth ? 100 : 0} width="100" height={noNorth ? 200 : 300} fill="#4b5563" />
        {/* Yo'l chiziqlari */}
        <g stroke="#f8fafc" strokeWidth="2.5" strokeDasharray="12 10">
          <line x1="0" y1="150" x2="100" y2="150" /><line x1="200" y1="150" x2="300" y2="150" />
          {!noNorth && <line x1="150" y1="0" x2="150" y2="100" />}
          <line x1="150" y1="200" x2="150" y2="300" />
        </g>
        {/* Asosiy yo'l ko'rsatkichi */}
        {scene.main && (
          <rect x={scene.main === "NS" ? 96 : 0} y={scene.main === "NS" ? 0 : 96} width={scene.main === "NS" ? 108 : 300} height={scene.main === "NS" ? 300 : 108} fill="none" stroke="#facc15" strokeWidth="3" opacity=".7" />
        )}
        {/* Tramvay izlari */}
        {scene.tram && (
          <g stroke="#cbd5e1" strokeWidth="2">
            {scene.tram === "EW"
              ? [118, 132, 168, 182].map((y) => <line key={y} x1="0" y1={y} x2="300" y2={y} />)
              : [118, 132, 168, 182].map((x) => <line key={x} x1={x} y1="0" x2={x} y2="300" />)}
          </g>
        )}
        {round && (
          <g>
            <circle cx="150" cy="150" r="78" fill="#4b5563" />
            <circle cx="150" cy="150" r="30" fill="#7fb069" stroke="#f8fafc" strokeWidth="3" />
          </g>
        )}
        {/* Piyodalar o'tish joylari */}
        {scene.pedestrians?.map((d) => {
          const zebra = d === "N" ? [100, 72, true] : d === "S" ? [100, 208, true] : d === "E" ? [208, 100, false] : [72, 100, false];
          const [zx, zy, horiz] = zebra as [number, number, boolean];
          return (
            <g key={d}>
              {Array.from({ length: 6 }, (_, i) =>
                horiz ? <rect key={i} x={zx + 6 + i * 16} y={zy} width="8" height="20" fill="#f8fafc" /> : <rect key={i} x={zx} y={zy + 6 + i * 16} width="20" height="8" fill="#f8fafc" />,
              )}
              <g transform={`translate(${horiz ? zx + 50 : zx + 10} ${horiz ? zy + 10 : zy + 50})`}>
                <circle r="7" fill="#f97316" stroke="#0f172a" strokeWidth="1.5" />
                <circle cy="-2" r="2.5" fill="#0f172a" />
              </g>
            </g>
          );
        })}
        {/* Harakat yo'nalishlari */}
        {scene.vehicles.map((v) => (
          <path key={v.id + "p"} d={pathFor(v.from, v.to, round)} fill="none" stroke="#0f172a" strokeOpacity=".75" strokeWidth="3" strokeDasharray="6 5" markerEnd="url(#arrowhead)" />
        ))}
        {scene.vehicles.map((v, i) => <Vehicle key={v.id} v={v} i={i} />)}
        {/* Belgilar va svetoforlar */}
        {Object.entries(scene.signs ?? {}).map(([d, code]) => {
          const [x, y] = SIGN_POS[d as Dir];
          return <SignSvg key={d} code={code!} x={x} y={y} size={30} />;
        })}
        {Object.entries(scene.lights ?? {}).map(([d, st]) => {
          const [x, y] = SIGN_POS[d as Dir];
          return <Light key={d} state={st!} x={x + 8} y={y - 4} />;
        })}
      </svg>
      {scene.caption && <figcaption className="mt-2 text-center text-xs text-muted-foreground">{scene.caption}</figcaption>}
    </figure>
  );
}
