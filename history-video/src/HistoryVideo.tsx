import React from "react";
import { AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame } from "remotion";
import "./fonts";
import data from "./data/scenes.json";
import { overlays, CHANNEL, Overlay } from "./overlays";
import { buildChunks, Subtitles, Word } from "./Subtitles";
import { KenBurns } from "./rve/KenBurns";
import { FilmBurn } from "./rve/FilmBurn";
import { FilmGrain } from "./rve/FilmGrain";
import { Letterbox } from "./rve/Letterbox";
import { CinematicTitle } from "./rve/CinematicTitle";
import { ChapterTitle } from "./rve/ChapterTitle";
import { LowerThird } from "./rve/LowerThird";
import { StatCounter } from "./rve/StatCounter";
import { TypewriterDate } from "./rve/TypewriterDate";
import { SubscribeReminder } from "./rve/SubscribeReminder";

export const FPS = 30;
const OFFSET = 1; // seconds of letterbox intro before the voice starts
const TAIL = 3; // seconds after the voice ends
const XF = 18; // cross-dissolve frames (RVE cross-dissolve.tsx)

type Scene = { id: number; img: string; text: string; start: number; end: number; words: Word[] };
const scenes = data.scenes as Scene[];
const voiceEnd = data.duration;
export const totalFrames = Math.ceil((OFFSET + voiceEnd + TAIL) * FPS);
const chunks = buildChunks(scenes);
const f = (sec: number) => Math.round((sec + OFFSET) * FPS);

const SceneLayer: React.FC<{ scene: Scene; index: number; dur: number }> = ({ scene, index, dur }) => {
  const frame = useCurrentFrame();
  const opacity = index === 0 ? 1 : interpolate(frame, [0, XF], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ opacity }}>
      <KenBurns src={`img/${scene.img}`} durationInFrames={dur} variant={index * 5 + (index % 3)} />
    </AbsoluteFill>
  );
};

const renderOverlay = (o: Overlay, dur: number) => {
  switch (o.kind) {
    case "date": return <TypewriterDate text={o.text} place={o.place} durationInFrames={dur} />;
    case "lower": return <LowerThird name={o.name} role={o.role} durationInFrames={dur} />;
    case "stat": return <StatCounter value={o.value} suffix={o.suffix} label={o.label} durationInFrames={dur} />;
    case "chapter": return <ChapterTitle label="Bob" number={o.number} title={o.title} durationInFrames={dur} />;
    case "title": return <CinematicTitle title={o.title} subtitle={o.subtitle} durationInFrames={dur} />;
    case "burn": return <FilmBurn durationInFrames={dur} />;
  }
};

const defaultDur: Record<Overlay["kind"], number> = { date: 5, lower: 6, stat: 5, chapter: 3.6, title: 7, burn: 1.0 };

export const HistoryVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const vEnd = f(voiceEnd);
  const musicVolume = (fr: number) =>
    interpolate(fr, [0, 25, 45, vEnd - 10, vEnd + 30, totalFrames - 50, totalFrames], [0.0, 0.32, 0.11, 0.11, 0.32, 0.32, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  const fadeOut = interpolate(frame, [totalFrames - 45, totalFrames - 1], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const last = scenes[scenes.length - 1];

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {scenes.map((sc, i) => {
        const from = i === 0 ? 0 : f(sc.start);
        const to = i === scenes.length - 1 ? totalFrames : f(sc.end) + XF;
        return (
          <Sequence key={sc.id} from={from} durationInFrames={to - from} name={`Sahna ${sc.id}`}>
            <SceneLayer scene={sc} index={i} dur={to - from} />
          </Sequence>
        );
      })}

      <FilmGrain />

      {scenes.flatMap((sc) =>
        (overlays[sc.id] ?? []).map((o, k) => {
          const dur = Math.round((o.dur ?? defaultDur[o.kind]) * FPS);
          const from = (sc.id === 1 ? 0 : f(sc.start)) + Math.round((o.at ?? 0) * FPS) + (sc.id === 1 ? 0 : 0);
          return (
            <Sequence key={`${sc.id}-${k}`} from={from} durationInFrames={dur} name={`${o.kind} ${sc.id}`}>
              {renderOverlay(o, dur)}
            </Sequence>
          );
        }),
      )}

      <Subtitles chunks={chunks} offset={OFFSET} />

      <Sequence from={f(last.start) + FPS} name="Obuna">
        <SubscribeReminder channel={CHANNEL} />
      </Sequence>

      <Letterbox final={7} />
      <AbsoluteFill style={{ backgroundColor: "black", opacity: fadeOut }} />

      <Sequence from={f(0)} name="Ovoz">
        <Audio src={staticFile("voice.mp3")} />
      </Sequence>
      <Audio src={staticFile("music.mp3")} volume={musicVolume} />
    </AbsoluteFill>
  );
};
