import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  random,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { fonts } from "../fonts";
import type { Theme } from "../schema";

export const ThemeContext = React.createContext<Theme>({
  accent: "#C9A23F",
  background: "#120E0A",
  text: "#F2E8D5",
  paper: "#E6D5B0",
});
export const useTheme = () => React.useContext(ThemeContext);

export const ease = Easing.bezier(0.22, 1, 0.36, 1);

/** 0→1 progress between two frames with a smooth ease-out. */
export const progress = (frame: number, from: number, dur: number) =>
  interpolate(frame, [from, from + dur], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: ease,
  });

/** Fade-out multiplier for the last `dur` frames of a scene. */
export const useExit = (dur = 15) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return interpolate(frame, [durationInFrames - dur, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
};

export const useSpring = (delay = 0, damping = 200) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - delay, fps, config: { damping } });
};

export const toRoman = (n: number) => {
  const map: [number, string][] = [
    [50, "L"], [40, "XL"], [10, "X"], [9, "IX"], [5, "V"], [4, "IV"], [1, "I"],
  ];
  let out = "";
  for (const [v, s] of map) {
    while (n >= v) {
      out += s;
      n -= v;
    }
  }
  return out;
};

export const resolveSrc = (src: string) =>
  /^(https?:|data:)/.test(src) ? src : staticFile(src);

/** Warm dark backdrop with drifting dust and a vignette. */
export const Backdrop: React.FC<{ seed?: string; glow?: [number, number] }> = ({
  seed = "dust",
  glow = [50, 45],
}) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const motes = new Array(36).fill(0).map((_, i) => {
    const x = random(`${seed}x${i}`) * width;
    const y0 = random(`${seed}y${i}`) * height;
    const speed = 0.15 + random(`${seed}s${i}`) * 0.5;
    const size = 1 + random(`${seed}r${i}`) * 3;
    const y = (((y0 - frame * speed) % height) + height) % height;
    const sway = Math.sin(frame / 40 + i) * 12;
    const op = 0.15 + 0.35 * random(`${seed}o${i}`);
    return (
      <div
        key={i}
        style={{
          position: "absolute",
          left: x + sway,
          top: y,
          width: size,
          height: size,
          borderRadius: "50%",
          background: t.paper,
          opacity: op,
          filter: "blur(0.5px)",
        }}
      />
    );
  });
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse at ${glow[0]}% ${glow[1]}%, ${t.accent}26 0%, ${t.background} 60%, #000 100%)`,
      }}
    >
      {motes}
    </AbsoluteFill>
  );
};

export const Vignette: React.FC<{ strength?: number }> = ({ strength = 0.75 }) => (
  <AbsoluteFill
    style={{
      pointerEvents: "none",
      background: `radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,${strength}) 100%)`,
    }}
  />
);

/** Animated film grain + occasional flicker. */
export const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  const seed = Math.floor(frame / 2) % 97;
  const flicker = 0.035 + random(`flicker${Math.floor(frame / 3)}`) * 0.03;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "overlay" }}>
      <svg width="100%" height="100%" style={{ opacity: 0.55 }}>
        <filter id={`grain${seed}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={seed} />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#grain${seed})`} />
      </svg>
      <AbsoluteFill style={{ background: "#fff", opacity: flicker }} />
    </AbsoluteFill>
  );
};

/** Gold rule that grows from the centre, with a diamond in the middle. */
export const Ornament: React.FC<{ width: number; delay?: number; dur?: number }> = ({
  width,
  delay = 0,
  dur = 30,
}) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const p = progress(frame, delay, dur);
  const half = (width / 2 - 18) * p;
  const line: React.CSSProperties = {
    height: 2,
    width: half,
    background: t.accent,
  };
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10, width }}>
      <div style={{ ...line, background: `linear-gradient(90deg, transparent, ${t.accent})` }} />
      <div
        style={{
          width: 12,
          height: 12,
          border: `2px solid ${t.accent}`,
          transform: `rotate(45deg) scale(${p})`,
        }}
      />
      <div style={{ ...line, background: `linear-gradient(270deg, transparent, ${t.accent})` }} />
    </div>
  );
};

export const Kicker: React.FC<{ children: React.ReactNode; delay?: number; size?: number }> = ({
  children,
  delay = 0,
  size = 26,
}) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const p = progress(frame, delay, 25);
  return (
    <div
      style={{
        fontFamily: fonts.sans,
        fontWeight: 600,
        fontSize: size,
        letterSpacing: interpolate(p, [0, 1], [18, 8]),
        textTransform: "uppercase",
        color: t.accent,
        opacity: p,
      }}
    >
      {children}
    </div>
  );
};

/** Word-by-word reveal with a slight blur and rise. */
export const RevealText: React.FC<{
  text: string;
  delay?: number;
  stagger?: number;
  style?: React.CSSProperties;
}> = ({ text, delay = 0, stagger = 4, style }) => {
  const frame = useCurrentFrame();
  return (
    <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "inherit", ...style }}>
      {text.split(" ").map((w, i) => {
        const p = progress(frame, delay + i * stagger, 22);
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              whiteSpace: "pre",
              opacity: p,
              filter: `blur(${(1 - p) * 10}px)`,
              transform: `translateY(${(1 - p) * 30}px)`,
            }}
          >
            {w}
            {i < text.split(" ").length - 1 ? " " : ""}
          </span>
        );
      })}
    </div>
  );
};

/**
 * Image with Ken Burns motion. If `src` is empty, draws an atmospheric
 * placeholder so the template still renders before real media is added.
 */
export const KenBurns: React.FC<{
  src: string;
  zoom?: "in" | "out";
  pan?: "left" | "right" | "up" | "down" | "none";
  label?: string;
  filter?: string;
}> = ({ src, zoom = "in", pan = "none", label, filter }) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const p = frame / Math.max(1, durationInFrames);
  const scale = zoom === "in" ? 1.05 + p * 0.15 : 1.2 - p * 0.15;
  const d = 60 * (p - 0.5);
  const tx = pan === "left" ? -d : pan === "right" ? d : 0;
  const ty = pan === "up" ? -d : pan === "down" ? d : 0;
  const transform = `scale(${scale}) translate(${tx}px, ${ty}px)`;

  if (src) {
    return (
      <AbsoluteFill style={{ overflow: "hidden" }}>
        <Img
          src={resolveSrc(src)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform,
            filter: filter ?? "sepia(0.25) contrast(1.05) brightness(0.85)",
          }}
        />
      </AbsoluteFill>
    );
  }
  // Placeholder: layered arches silhouette suggesting old architecture
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          transform,
          background: `linear-gradient(180deg, #3a2a18 0%, ${t.accent}55 55%, #1b130b 100%)`,
        }}
      >
        <svg viewBox="0 0 1920 1080" width="100%" height="100%" preserveAspectRatio="xMidYMid slice">
          <defs>
            <radialGradient id="sun" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor={t.paper} stopOpacity="0.9" />
              <stop offset="100%" stopColor={t.paper} stopOpacity="0" />
            </radialGradient>
          </defs>
          <circle cx="960" cy="560" r="420" fill="url(#sun)" opacity="0.35" />
          <g fill="#140d07" opacity="0.92">
            {/* central portal */}
            <path d="M700 1080 V420 H1220 V1080 Z" />
            <path d="M800 1080 V560 Q960 360 1120 560 V1080 Z" fill={`${t.accent}40`} />
            {/* dome */}
            <path d="M1260 520 Q1260 330 1400 300 Q1540 330 1540 520 Z" />
            <rect x="1250" y="520" width="300" height="560" />
            <rect x="1396" y="250" width="8" height="55" />
            {/* minarets */}
            <rect x="610" y="260" width="60" height="820" />
            <path d="M600 260 H680 L640 210 Z" />
            <rect x="1580" y="300" width="56" height="780" />
            <path d="M1570 300 H1646 L1608 255 Z" />
            {/* left dome */}
            <path d="M330 640 Q330 480 450 450 Q570 480 570 640 Z" />
            <rect x="320" y="640" width="260" height="440" />
            <rect y="900" width="1920" height="180" />
          </g>
        </svg>
      </AbsoluteFill>
      {label ? (
        <div
          style={{
            position: "absolute",
            top: 90,
            right: 56,
            fontFamily: fonts.sans,
            fontSize: 18,
            color: t.paper,
            opacity: 0.5,
            letterSpacing: 2,
          }}
        >
          {label}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

/** Small corner brackets framing the whole picture, like an archive plate. */
export const FrameCorners: React.FC<{ inset?: number; delay?: number }> = ({
  inset = 48,
  delay = 0,
}) => {
  const t = useTheme();
  const frame = useCurrentFrame();
  const p = progress(frame, delay, 30);
  const len = 60 * p;
  const s = (pos: React.CSSProperties, bt: string, bl: string): React.CSSProperties => ({
    position: "absolute",
    width: len,
    height: len,
    borderTop: bt,
    borderLeft: bl,
    ...pos,
  });
  const b = `2px solid ${t.accent}`;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: 0.8 * p }}>
      <div style={s({ top: inset, left: inset }, b, b)} />
      <div style={{ ...s({ top: inset, right: inset }, b, "none"), borderRight: b }} />
      <div style={{ ...s({ bottom: inset, left: inset }, "none", b), borderBottom: b }} />
      <div
        style={{
          ...s({ bottom: inset, right: inset }, "none", "none"),
          borderBottom: b,
          borderRight: b,
        }}
      />
    </AbsoluteFill>
  );
};
