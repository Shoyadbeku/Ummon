import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  Easing,
} from "remotion";
import timeline from "./data/timeline.json";
import { FONT } from "./theme";
import { Subtitles } from "./components/Subtitles";
import { LowerThird, ShotTag, SourceCredit } from "./components/Labels";
import { SceneOverlay } from "./components/SceneOverlay";

type Shot = {
  idx: number;
  scene: number;
  src: string;
  label: string | null;
  credit: string;
  kind: string;
  from: number;
  dur: number;
  file: string;
  lt: [string, string] | null;
};

const XF = 12; // cross-dissolve frames

const ShotLayer: React.FC<{ shot: Shot; last: boolean }> = ({ shot, last }) => {
  const frame = useCurrentFrame();
  const total = shot.dur + (last ? 0 : XF);
  const opacity = shot.idx === 0 ? 1 : interpolate(frame, [0, XF], [0, 1], { extrapolateRight: "clamp" });
  // Ken Burns: slow push-in / pull-out, alternating, gentler on interviews
  const amp = shot.kind === "interview" ? 0.035 : 0.09;
  const dir = shot.idx % 2 === 0 ? 1 : -1;
  const p = interpolate(frame, [0, total], [0, 1], { easing: Easing.inOut(Easing.quad) });
  const scale = dir > 0 ? 1.02 + amp * p : 1.02 + amp * (1 - p);
  const tx = (shot.idx % 3 - 1) * 18 * p;
  const ty = ((shot.idx + 1) % 3 - 1) * 10 * p;
  const grade =
    shot.kind === "archive"
      ? "contrast(1.1) saturate(0.85) brightness(0.96)"
      : "contrast(1.06) saturate(0.9) brightness(0.97)";
  return (
    <AbsoluteFill style={{ opacity }}>
      <AbsoluteFill style={{ transform: `scale(${scale}) translate(${tx}px, ${ty}px)`, filter: grade }}>
        <OffthreadVideo src={staticFile(shot.file)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
      <ShotTag label={shot.label} />
      <SourceCredit credit={shot.credit} kind={shot.kind} />
      {shot.lt ? <LowerThird name={shot.lt[0]} role={shot.lt[1]} duration={shot.dur} /> : null}
    </AbsoluteFill>
  );
};

const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  const n = (Math.floor(frame / 2) % 8) + 1;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <Img
        src={staticFile(`fx/grain${n}.png`)}
        style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.07, mixBlendMode: "overlay" }}
      />
      <AbsoluteFill
        style={{
          background: "radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};

export const Documentary: React.FC = () => {
  const shots = timeline.shots as unknown as Shot[];
  const scenes = timeline.scenes as any[];
  return (
    <AbsoluteFill style={{ backgroundColor: "#000", fontFamily: FONT }}>
      {shots.map((s, i) => (
        <Sequence key={s.idx} from={s.from} durationInFrames={s.dur + (i === shots.length - 1 ? 0 : XF)} layout="none">
          <ShotLayer shot={s} last={i === shots.length - 1} />
        </Sequence>
      ))}
      <Grain />
      {scenes.map((sc) => (
        <Sequence key={sc.i} from={sc.vFrom} durationInFrames={sc.vTo - sc.vFrom} layout="none">
          <SceneOverlay scene={sc} />
        </Sequence>
      ))}
      <Subtitles subs={timeline.subs as any[]} scenes={scenes} />
      <Audio src={staticFile("soundtrack.wav")} />
    </AbsoluteFill>
  );
};
